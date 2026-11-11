"""Exercise the local assembly and individual-parts review with Chromium."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent
BASE='http://127.0.0.1:8768'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader'])
    page=browser.new_page(viewport={'width':1500,'height':1050},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'/review/',timeout=90000)
    page.wait_for_function('window.tinfox && window.lastCollision',timeout=90000)
    for name in ['stand','studio','raised','crouch','reach','fold','splay','side_reach']:
        page.evaluate('(name)=>window.tinfox.setPose(window.tinfox.data.poses[name])',name)
        assert not page.evaluate('window.lastCollision.collision'),name
    page.select_option('#pose','studio')
    page.screenshot(path=str(ROOT/'output/exterior-preview.png'),timeout=90000)
    body_ids=page.evaluate('window.tinfox.objects.filter(o=>!o.userData.leg && o.visible).map(o=>o.userData.name).sort()')
    for angle in [-60,-6,0,6,60]:
        page.evaluate('''a=>{const q=structuredClone(window.tinfox.data.poses.stand);for(const l of Object.keys(q))q[l]=[l.endsWith('L')?a:-a,l.startsWith('F')?-35:35,-70];return window.tinfox.setPose(q)}''',angle)
        assert not page.evaluate('window.lastCollision.collision'),angle
        assert body_ids==page.evaluate('window.tinfox.objects.filter(o=>!o.userData.leg && o.visible).map(o=>o.userData.name).sort()')
    assert not page.evaluate("window.tinfox.data.parts.some(p=>p.material==='fabric')")
    page.click('#roll-demo');page.wait_for_timeout(1100)
    assert page.evaluate('window.tinfox.poses.FR[0]')!=0
    page.click('#roll-demo')
    page.evaluate('window.tinfox.setPose(window.tinfox.data.poses.stand)')
    page.click('[data-view="section"]');assert page.locator('#open-shell').is_checked()
    page.screenshot(path=str(ROOT/'output/leg-section-preview.png'),timeout=90000)
    page.evaluate('''()=>{const q=structuredClone(window.tinfox.data.poses.stand);q.FL=[-60,60,-120];q.FR=[-60,60,-120];return window.tinfox.setPose(q)}''')
    assert page.evaluate('window.lastCollision.collision')
    assert page.request.post(BASE+'/api/collision',data={'poses':{}}).status==400
    for path in ['/output/tinfox-assembly.step','/output/tinfox.glb','/studio.png']:
        assert page.request.get(BASE+path).status==200,path
    page.goto(BASE+'/review/parts.html',timeout=90000)
    page.wait_for_function('window.partsReview && window.currentPart',timeout=90000)
    page.select_option('#category','Mounts');mount_count=page.locator('#list button').count();assert mount_count==12
    for button in page.locator('#list button').all():
        button.click();url=page.locator('#downloads a.primary').get_attribute('href')
        assert page.request.get(BASE+'/review/'+url).status==200
    page.evaluate("window.partsReview.choose('shoulder_cover_1')")
    page.screenshot(path=str(ROOT/'output/shoulder-cowling-preview.png'),timeout=90000)
    page.evaluate("window.partsReview.choose('front_fascia')")
    page.screenshot(path=str(ROOT/'output/front-fascia-preview.png'),timeout=90000)
    for view in ['front','side','iso']:page.click(f'[data-camera="{view}"]')
    assert page.request.get(BASE+'/output/tinfox-individual-cad.zip').status==200
    assert not errors,errors
    (ROOT/'output/browser-checks.json').write_text(json.dumps({'model_sha256':json.loads((ROOT/'output/manifest.json').read_text())['model_sha256'],'presets':8,'mount_variants':mount_count,'known_interference_detected':True,'downloads_ok':True,'page_errors':errors},indent=2))
    print('Eight poses, articulated roll, section view,12 mount downloads and parts controls passed; no JavaScript errors.')
    browser.close()
