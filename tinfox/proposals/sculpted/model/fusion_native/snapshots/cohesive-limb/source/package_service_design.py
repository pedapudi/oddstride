"""Package revised CAD, print mockups and the exact review evidence."""
from pathlib import Path
import json,hashlib,zipfile
from kinematics import ROOT
out=ROOT/'output/service-design';stamp=hashlib.sha256((out/'model.json').read_bytes()).hexdigest()
for name in ['audit','parts','print-extras','torques','assembly-export','browser-checks','body-cap-audit']:
 assert json.loads((out/(name+'.json')).read_text())['model_sha256']==stamp,name
zip_path=out/'tinfox-service-design.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in out.rglob('*'):
  if p.is_file() and p!=zip_path:z.write(p,'output/service-design/'+str(p.relative_to(out)))
 for name in ['audit_body_caps.py','body_caps.py','service_design.py','audit_service_design.py','service_print_parts.py','export_service_assembly.py','write_service_review.py','verify_service_review.py','package_service_design.py','build.py','engineering.py','kinematics.py','parameters.json','printed_carrier.py','mesh_cleanup.py','collision.py']:
  z.write(ROOT/name,'source/'+name)
 for name in ['service.html','service.js']:
  z.write(ROOT/'review'/name,'review/'+name)
 for p in (ROOT/'review/vendor').iterdir():
  if p.is_file():z.write(p,'review/vendor/'+p.name)
 z.writestr('START.txt','Tinfox bearing and connector revision\n\nStart a local HTTP server in this extracted folder and open review/service.html.\nThe previous-assembly link requires the main repository.\n\nUpdated whole robot: output/service-design/updated-robot.step\nIndividual changed solids: output/service-design/step/\nPrint prototypes and fit coupons: output/service-design/print-stl/\nInstructions: output/service-design/README.html\n\nThese are nominal design prototypes. Physical fits, cable life and strength\nremain unqualified. The source scripts depend on the preceding repository\nassembly and CadQuery environment; this archive is not a standalone rebuild kit.\n')
print(zip_path,round(zip_path.stat().st_size/1e6,1),'MB')
