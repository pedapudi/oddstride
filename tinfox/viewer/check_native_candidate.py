"""Check a private native bench revision without publishing it as current."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default='http://127.0.0.1:8770/viewer/.native-candidate/')
    args=parser.parse_args();folder=ROOT/'.native-candidate';catalog=json.loads((folder/'catalog.json').read_text());design=catalog['designs'][0]
    errors=[];missing=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader'])
        page=browser.new_page(viewport={'width':1600,'height':1050})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('response',lambda r:missing.append([r.status,r.url]) if r.status>=400 and 'favicon' not in r.url else None)
        page.goto(args.url);page.wait_for_function('window.tinfoxReview',timeout=90000)
        assert page.evaluate('tinfoxReview.state.objects.length')==design['physical_components']
        assert page.evaluate('tinfoxReview.state.design.source.kind')=='fusion-native-candidate'
        assert page.locator('[data-mode="motion"]').is_disabled() and page.locator('#check').is_disabled()
        page.screenshot(path=str(folder/'assembly.png'))
        page.check('#actuators-only');assert page.evaluate('tinfoxReview.state.objects.filter(o=>o.visible).length')==3
        page.wait_for_timeout(200);assert 'null' not in page.locator('#actuator-labels').inner_text()
        page.screenshot(path=str(folder/'motors.png'));page.uncheck('#actuators-only')
        page.check('#open-shells');assert page.evaluate('tinfoxReview.state.objects.filter(o=>o.visible).length')==design['physical_components']-1
        page.screenshot(path=str(folder/'open-shell.png'))
        page.click('[data-mode="parts"]');assert page.locator('#part option').count()==13
        for record in design['parts']:
            if not record['custom']:continue
            page.select_option('#part',record['id'])
            assert page.evaluate('tinfoxReview.state.objects.filter(o=>o.visible).length')==1
            for link in page.locator('#part-downloads a').all():assert page.request.head(link.evaluate('(a)=>a.href')).status==200
        page.select_option('#category','Sensors and wiring');assert page.locator('#part option').count()==24
        page.select_option('#category','custom');page.select_option('#part','thigh_outer')
        page.check('#section');assert page.evaluate('tinfoxReview.state.objects.find(o=>o.visible).material.clippingPlanes.length')==1
        assert not errors,errors
        assert not missing,missing
        browser.close()
    report={'model_sha256':design['model_sha256'],'candidate_only':True,'browser_errors':errors,'missing_assets':missing,
        'bodies':design['physical_components'],'custom_parts':13,'motors':3,'connector_bodies':24,'static_controls':True,
        'all_custom_parts_isolated':True,'sections':True,'native_step_links':True}
    (folder/'browser-checks.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))


if __name__=='__main__':main()
