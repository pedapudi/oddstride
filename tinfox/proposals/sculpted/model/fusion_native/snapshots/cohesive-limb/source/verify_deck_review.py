"""Exercise the deck preview, print orientation and independent service stages."""
import hashlib,json
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parent;errors=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader'])
 page=browser.new_page(viewport={'width':1550,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)))
 for name in ['electronics_shelf','chassis_lower_brace']:
  page.goto('http://127.0.0.1:8768/review/parts.html#'+name)
  page.wait_for_function('(n)=>window.currentPart?.id===n',arg=name,timeout=90000)
  page.click('#print-orientation');page.wait_for_timeout(400)
  for link in page.locator('#downloads a').all():assert page.request.get(link.evaluate('(a)=>a.href'),timeout=90000).status==200
  page.screenshot(path=str(R/'output'/f'{name}-review.png'),full_page=True)
 page.goto('http://127.0.0.1:8768/review/assembly.html');page.wait_for_function('window.assemblyReview && window.assemblyReview.audit.passed',timeout=90000)
 for i in [2,3,4]:
  page.click(f'[data-stage="{i}"]');page.wait_for_timeout(400)
  assert page.evaluate("window.assemblyReview.objects.find(o=>o.userData.name==='chassis_lower_brace').visible")
  if i==3:assert page.evaluate("window.assemblyReview.objects.find(o=>o.userData.name==='battery_cassette').visible")
  if i==4:assert page.evaluate("window.assemblyReview.objects.find(o=>o.userData.name==='electronics_shelf').visible")
  page.screenshot(path=str(R/'output'/f'deck-service-stage-{i}.png'))
 assert not errors,errors
 (R/'output/electronics-deck-browser-checks.json').write_text(json.dumps({'model_sha256':hashlib.sha256((R/'output/model.json').read_bytes()).hexdigest(),'parts':['electronics_shelf','chassis_lower_brace'],'service_stages':[2,3,4],'downloads_ok':True,'page_errors':errors},indent=2))
 browser.close()
print('Deck, fixed brace, flat DXFs and independent service stages passed in Chrome.')
