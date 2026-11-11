"""Exercise all construction tabs, part previews, print orientation and downloads."""
import json,hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parent
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader'])
 page=b.new_page(viewport={'width':1500,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8768/review/variants.html');results=[]
 for v in ['printed','hybrid','cnc']:
  page.click(f'[data-variant="{v}"]');page.wait_for_function('(v)=>window.currentLimbVariant===v',arg=v,timeout=120000)
  page.select_option('#part','assembly');page.locator('#explode').fill('35');page.locator('#explode').dispatch_event('input');page.wait_for_timeout(700)
  assert page.evaluate('window.limbVariants.objects.length')>20
  for a in page.locator('a').all():
   url=a.evaluate('(a)=>a.href');assert page.request.get(url,timeout=120000).status==200,url
  page.screenshot(path=str(R/f'output/limb-variants/{v}/assembly-preview.png'),full_page=True)
  for part in ['thigh_inner','thigh_outer','shin_inner','shin_outer','motor_carrier_1']:
   part=part+'_flange' if v=='printed' and part=='motor_carrier_1' else part
   page.select_option('#part',part);assert page.evaluate('window.limbVariants.objects.length')==1
   if v=='printed':page.click('#print');assert page.evaluate('window.limbVariants.printMode')
   for a in page.locator('#detail a').all():assert page.request.get(a.evaluate('(a)=>a.href'),timeout=120000).status==200
  for mode in ['knee','carrier']:
   page.select_option('#part',mode);page.locator('#explode').fill('45' if mode=='carrier' else '20');page.locator('#explode').dispatch_event('input');page.wait_for_timeout(400)
   assert page.evaluate('window.limbVariants.objects.length')>=(2 if mode=='knee' or v=='printed' else 1)
   page.screenshot(path=str(R/f'output/limb-variants/{v}/{mode}-service-preview.png'))
  page.select_option('#part','shin_outer')
  if v!='cnc':page.click('#print')
  page.wait_for_timeout(400)
  page.screenshot(path=str(R/f'output/limb-variants/{v}/shin-preview.png'))
  results.append({'variant':v,'previewed_parts':['thigh_inner','thigh_outer','shin_inner','shin_outer','motor_carrier_1'],'downloads_ok':True})
 assert not errors,errors
 (R/'output/limb-variants/browser-checks.json').write_text(json.dumps({'parent_model_sha256':hashlib.sha256((R/'output/model.json').read_bytes()).hexdigest(),'checks':results,'page_errors':errors},indent=2))
 b.close()
print('All construction tabs, exploded assemblies, individual parts and download links passed.')
