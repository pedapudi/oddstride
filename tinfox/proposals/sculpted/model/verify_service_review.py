"""Exercise revised CAD, extraction animation and downloads in Chrome."""
import json,hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parent;out=root/'output/service-design';errors=[];failures=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader'])
 page=browser.new_page(viewport={'width':1550,'height':1050});page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:failures.append([r.status,r.url]) if r.status>=400 and 'favicon' not in r.url else None)
 page.goto('http://127.0.0.1:8768/review/service.html');page.wait_for_function('window.serviceReview',timeout=90000)
 for i in range(9):
  page.click(f'[data-stage="{i}"]');page.wait_for_timeout(350)
  assert page.evaluate('serviceReview.objects.some(o=>o.visible)'),i
  if i==3:
   page.check('#cutaway');page.locator('#extract').fill('14');page.locator('#extract').dispatch_event('input')
   pos=page.evaluate("serviceReview.objects.find(o=>o.userData.name==='FL_bearing_inner').matrix.elements[13]")
   assert abs(pos+14)<1e-6,pos
  if i==4:
   radius=page.evaluate("(()=>{const o=serviceReview.objects.find(o=>o.userData.name==='FL_pushrod');let e=o.matrix.elements;return Math.hypot(e[12],e[14]);})()")
   assert abs(radius-22)<1e-6,('Pushrod eye crank radius',radius)
  if i==5:
   page.check('#keepout')
   assert page.evaluate("serviceReview.objects.filter(o=>o.visible).every(o=>o.userData.name.endsWith('_motor')||Boolean(o.userData.service_role))")
  page.wait_for_timeout(200);page.screenshot(path=str(out/f'review-stage-{i}.png'))
 for link in page.locator('#downloads a').all():
  response=page.request.get(link.evaluate('(a)=>a.href'),timeout=90000);assert response.status==200,(response.status,link.inner_text())
 page.check('#keepout')
 for pose in ['stand','studio','raised','crouch','reach','splay','side_reach']:
  page.select_option('#pose',pose)
  assert page.locator('#status').inner_text().startswith('0 reported'),pose
 page.select_option('#pose','fold');assert not page.locator('#status').inner_text().startswith('0 reported')
 page.select_option('#pose','sample_45_65_-90');assert not page.locator('#status').inner_text().startswith('0 reported')
 page.goto('http://127.0.0.1:8768/output/service-design/README.html');assert page.locator('h1').count()==1
 for link in page.locator('a').all():
  url=link.evaluate('(a)=>a.href')
  if '127.0.0.1' in url:assert page.request.get(url,timeout=90000).status==200,url
 assert not errors,errors;assert not failures,failures
 browser.close()
(out/'browser-checks.json').write_text(json.dumps({'model_sha256':hashlib.sha256((out/'model.json').read_bytes()).hexdigest(),'stages_checked':9,'extraction_travel_checked_mm':14,'downloads_ok':True,'page_errors':errors,'http_failures':failures},indent=2))
print('Chrome views, extraction travel, named pose warnings and downloads passed.')
