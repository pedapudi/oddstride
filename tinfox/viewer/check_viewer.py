"""Opt-in viewer-maintenance regression; not part of CAD iteration."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--full-regression', action='store_true',
                    help='Run viewer UI, archive and request-lifecycle checks.')
if not parser.parse_args().full_regression:
    parser.error('This is a full viewer regression. Use --full-regression only for viewer changes; CAD iterations use focused geometry checks and one visual review.')

ROOT = Path(__file__).resolve().parent
(ROOT/'captures').mkdir(exist_ok=True)
(ROOT/'checks').mkdir(exist_ok=True)
errors, failures, requests = [], [], []
base = 'http://127.0.0.1:8770'
catalog = json.loads((ROOT/'catalog.json').read_text())
release_count = len(json.loads((ROOT/'releases.json').read_text())['releases'])
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True,
        args=['--no-sandbox', '--enable-gpu', '--ignore-gpu-blocklist'])
    page = browser.new_page(viewport={'width':1600,'height':1050})
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda request: requests.append(request.url))
    page.on('response', lambda response: failures.append((response.status,response.url))
            if response.status>=400 and response.request.method=='GET' and 'favicon' not in response.url else None)
    page.goto(base+'/viewer/')
    page.wait_for_function('window.tinfoxReview', timeout=90000)
    page.wait_for_function('tinfoxReview.state.liveAvailable', timeout=20000)
    assert page.evaluate('tinfoxReview.state.design.id') == catalog['current_design']
    assert not page.locator('#show-archived').is_checked()
    assert page.locator('#design optgroup').count() == 0
    assert not any('/archive/designs/' in url for url in requests), 'Archived part libraries loaded at startup'
    assert page.locator('#geometry-source').inner_text()
    page.wait_for_function('(count)=>document.querySelectorAll("#current-releases a").length===count',arg=release_count)
    for link in page.locator('#current-releases a').all():
        assert page.request.head(link.evaluate('(a)=>a.href')).status == 200
    if page.evaluate('tinfoxReview.state.design.source.kind') == 'generated-reference':
        assert not page.evaluate('tinfoxReview.state.design.parts.some(p=>p.print_stl||p.print_3mf)')
    static_native = page.evaluate('tinfoxReview.state.design.presentation==="motor-complex"')
    whole_native = page.evaluate('tinfoxReview.state.design.source.kind==="fusion-native" && tinfoxReview.state.design.motion_available===true')
    if static_native:
        assert page.evaluate('tinfoxReview.state.design.source.kind') == 'fusion-native'
        assert page.locator('[data-mode="motion"]').is_disabled()
        assert page.locator('#check').is_disabled()
        assert page.locator('#clearance-title').inner_text() == 'Static motor-complex review'
        page.check('#actuators-only')
        assert page.evaluate('tinfoxReview.state.objects.filter(o=>o.visible).length') == 3
        page.uncheck('#actuators-only')
    if whole_native:
        assert '12 actuators' in page.locator('#design-metrics').inner_text()
        assert '88 definitions' in page.locator('#inventory-counts').inner_text()
        page.check('#actuators-only')
        assert page.evaluate('tinfoxReview.state.objects.filter(o=>o.visible).length') == 12
        page.uncheck('#actuators-only')
        identity = page.evaluate('tinfoxReview.state.design.model_sha256')
        poses = page.evaluate('structuredClone(tinfoxReview.state.q)')
        for supplied in (None, '0'*64):
            payload = {'design': catalog['current_design'], 'poses': poses}
            if supplied is not None:
                payload['model_sha256'] = supplied
            response = page.request.post(base+'/api/check', data=payload)
            assert response.status == 400 and 'Reload' in response.json()['error']
        response = page.request.post(base+'/api/check', data={
            'design': catalog['current_design'], 'poses': poses, 'model_sha256': identity})
        assert response.status == 200 and response.json()['model_sha256'] == identity
        assert response.json()['checked_components'] == page.evaluate('tinfoxReview.state.design.physical_components')
    page.screenshot(path=str(ROOT/'captures/current-review.png'))
    page.click('[data-mode="parts"]')
    page.select_option('#category','custom')
    page.fill('#search','thigh')
    page.select_option('#part','thigh_outer')
    assert page.evaluate('tinfoxReview.state.objects.filter(o=>o.visible).length') == 1
    page.check('#section')
    page.locator('#section-position').fill('42')
    page.locator('#section-position').dispatch_event('input')
    assert page.evaluate('tinfoxReview.state.objects.find(o=>o.visible).material.clippingPlanes.length') == 1
    for link in page.locator('#part-downloads a').all():
        assert page.request.head(link.evaluate('(a)=>a.href')).status == 200
    page.uncheck('#section')
    page.click('#show-in-robot')
    if static_native:
        page.select_option('#design','v14')
        page.wait_for_function('tinfoxReview.state.design.id==="v14" && document.getElementById("loading").hidden',timeout=90000)
        assert not page.locator('[data-mode="motion"]').is_disabled()
    page.click('[data-mode="motion"]')
    page.select_option('#pose','stand')
    page.select_option('#leg','FL')
    before = page.evaluate('structuredClone(tinfoxReview.state.q)')
    page.locator('#roll').fill('13')
    page.locator('#roll').dispatch_event('input')
    after = page.evaluate('tinfoxReview.state.q')
    assert after['FL'][0] == 13 and after['FR'] == before['FR']
    assert page.locator('#clearance-title').inner_text() == 'Pose not checked'
    page.click('#play')
    assert page.locator('#clearance-title').inner_text() == 'Motion preview'
    moving = page.evaluate('tinfoxReview.state.q.FL[1]')
    page.wait_for_function('(value)=>tinfoxReview.state.q.FL[1]!==value',arg=moving,timeout=15000)
    page.click('#play')
    assert not page.evaluate('tinfoxReview.state.playing')
    page.select_option('#pose','stand')
    page.click('#check')
    page.wait_for_function('!document.getElementById("clearance-title").textContent.startsWith("Checking")',timeout=90000)
    assert 'this pose' in page.locator('#clearance-title').inner_text()
    pending = []
    page.route('**/api/check', lambda route: pending.append(route))
    page.evaluate('void (window.pendingCheck=tinfoxReview.checkPose())')
    page.wait_for_timeout(100)
    assert pending
    page.locator('#roll').fill('14')
    page.locator('#roll').dispatch_event('input')
    pending.pop().fulfill(status=200,content_type='application/json',body=json.dumps({'pairs':[],'scope':'Delayed test result'}))
    page.evaluate('window.pendingCheck')
    assert page.locator('#clearance-title').inner_text() == 'Pose not checked'
    page.unroute('**/api/check')
    page.check('#show-archived')
    assert page.locator('#design optgroup option').count() == sum(bool(d.get('archived')) for d in catalog['designs'])
    page.select_option('#design','v1')
    page.wait_for_function('tinfoxReview.state.design.id==="v1" && document.getElementById("loading").hidden',timeout=90000)
    assert page.locator('#archive-notice').is_visible()
    assert sum('/archive/designs/v1.json.gz' in url for url in requests) == 1
    assert page.locator('#design-title').inner_text() == 'Rounded enclosure · V1'
    page.click('#open-current')
    page.wait_for_function('(id)=>tinfoxReview.state.design.id===id && document.getElementById("loading").hidden',arg=catalog['current_design'],timeout=90000)
    assert not page.locator('#show-archived').is_checked()
    assert page.locator('#archive-notice').is_hidden()
    for route in ['/viewer/enclosure-review.html','/model/review/index.html','/proposals/sculpted/model/review/parts.html']:
        response = page.request.get(base+route)
        assert response.status == 200 and 'tinfox-archived-entry' in response.text()
    assert page.request.post(base+'/api/check',data={'design':'unknown','poses':{}}).status == 400
    assert not errors,errors
    assert not failures,failures
    browser.close()
report = {'browser_errors':errors,'missing_assets':failures,'current_design':catalog['current_design'],
          'archived_catalogs_fetched':sum('/archive/designs/' in url for url in requests),
          'startup_archives_deferred':True,'current_release_links':True,'stale_print_links_removed':True,
          'part_isolation':True,'section_view':True,'motion_state':True,'stale_result_discarded':True,
          'historical_entry_notices':True,'native_static_scope':static_native,
          'native_whole_scope':whole_native,'native_geometry_hash_protocol':whole_native}
(ROOT/'checks/current.json').write_text(json.dumps(report,indent=2))
print('Current viewer checks passed: startup, deferred archive, parts, motion, release links and historical notices.')
