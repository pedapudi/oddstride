"""Make only the bench occurrence graph effectively visible, retaining hidden parents."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;bench=next(o for o in root.occurrences if o.component.partNumber=='BENCH_MOTOR_COMPLEX');rows=[]
 for o in root.occurrences:o.isLightBulbOn=o==bench
 def walk(occ):
  before=occ.isLightBulbOn;occ.isLightBulbOn=True;c=occ.component
  for body in c.bRepBodies:
   body.isLightBulbOn=True;proxy=body.createForAssemblyContext(occ);rows.append({'path':occ.fullPathName,'body':body.name,'occurrence_light_before':before,'occurrence_light_after':occ.isLightBulbOn,'body_light':body.isLightBulbOn,'body_visible':proxy.isVisible})
  for child in c.occurrences:walk(child.createForAssemblyContext(occ))
 walk(bench);assert len(rows)==124,(len(rows),rows);assert all(r['body_visible']for r in rows),[r for r in rows if not r['body_visible']];assert [o.component.partNumber for o in root.occurrences if o.isLightBulbOn]==['BENCH_MOTOR_COMPLEX'];app.activeViewport.fit();app.activeViewport.refresh();path=os.path.join(tempfile.gettempdir(),'tinfox-native','motor-complex-visible-bench.png');assert app.activeViewport.saveAsImageFile(path,1800,1200);print(json.dumps({'passed':True,'bodies':rows,'visible_bodies':len(rows),'saved':False,'checkpoint_version':doc.dataFile.versionNumber,'screenshot':path}))
'''
r=rpc(s,'motor-complex-effective-visibility',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/motor-complex-effective-visibility.json').write_text(json.dumps(record,indent=2));print({'passed':True,'visible_bodies':len(record['bodies'])})
