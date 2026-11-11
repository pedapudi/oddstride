"""Check strength notes, measured orientations and the new structural part previews."""
import hashlib,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent;BASE='http://127.0.0.1:8768/review/'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader'])
 page=b.new_page(viewport={'width':1500,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(BASE+'strength.html');assert page.locator('table tr').count()==9
 assert 'not strength-qualified' in page.locator('pre').inner_text()
 for a in page.locator('nav a').all():assert page.request.get(a.evaluate('(a)=>a.href')).status==200
 page.screenshot(path=str(ROOT/'output/print-strength-preview.png'),full_page=True)
 for part in ['shin_inner','shin_outer','thigh_outer','motor_carrier_1']:
  page.goto(BASE+'parts.html#'+part);page.wait_for_function('(name)=>window.currentPart?.id===name',arg=part,timeout=90000)
  page.click('#print-orientation')
  page.screenshot(path=str(ROOT/('output/'+part+'-print-preview.png')),timeout=90000)
 page.goto(BASE+'hardware.html');rows=len(json.loads((ROOT/'output/hardware-research.json').read_text())['parts'])
 assert page.locator('tbody tr').count()==rows
 for a in page.locator('a').all():
  url=a.evaluate('(a)=>a.href')
  if '127.0.0.1' in url:assert page.request.get(url).status==200,url
 assert not errors,errors
 (ROOT/'output/strength-browser-checks.json').write_text(json.dumps({'model_sha256':hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest(),'orientation_rows':8,'hardware_rows':rows,'part_previews':['shin_inner','shin_outer','thigh_outer','motor_carrier_1'],'page_errors':errors},indent=2))
 b.close()
print('Strength evidence, eight orientation rows, hardware links and four part previews passed.')
