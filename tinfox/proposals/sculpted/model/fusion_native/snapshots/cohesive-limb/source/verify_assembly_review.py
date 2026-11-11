"""Exercise staged CAD assembly views and their evidence downloads in Chrome."""
import hashlib,json
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader'])
 page=browser.new_page(viewport={'width':1550,'height':1050});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8768/review/assembly.html',timeout=90000)
 page.wait_for_function('window.assemblyReview && window.assemblyReview.audit.passed',timeout=90000)
 assert page.locator('[data-stage]').count()==6
 for i in range(6):
  page.click(f'[data-stage="{i}"]')
  assert page.evaluate('window.currentAssemblyStage')==i
  assert page.evaluate('window.assemblyReview.objects.some(o=>o.visible)')
  if i==2:
   assert page.evaluate("window.assemblyReview.objects.find(o=>o.userData.name==='body_center_0').visible===false")
   assert page.evaluate("window.assemblyReview.objects.find(o=>o.userData.name==='chassis_beam_102').visible===true")
  if i==3:
   assert page.evaluate("window.assemblyReview.objects.find(o=>o.userData.name==='battery_cassette').visible")
   assert page.evaluate("window.assemblyReview.objects.find(o=>o.userData.name==='chassis_lower_brace').visible")
  if i==4:
   assert page.evaluate("window.assemblyReview.objects.find(o=>o.userData.name==='electronics_shelf').visible")
  page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
  if i in [1,2,3,4]:page.screenshot(path=str(ROOT/f'output/assembly-stage-{i}.png'),timeout=90000)
 page.click('#top');page.click('#home')
 for a in page.locator('.links a').all():assert page.request.get(urljoin(page.url,a.get_attribute('href'))).status==200
 stamp=hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest()
 assert page.evaluate('window.assemblyReview.audit.model_sha256')==stamp
 assert not errors,errors
 (ROOT/'output/assembly-browser-checks.json').write_text(json.dumps({'model_sha256':stamp,'stages':6,'downloads_ok':True,'page_errors':errors},indent=2))
 browser.close()
print('Six assembly stages, camera controls and evidence downloads passed in Chrome.')
