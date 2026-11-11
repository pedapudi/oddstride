"""Remove redundant empty cuts and exercise the current crank family."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;c=next(o.component for o in root.occurrences if o.component.partNumber=='CANDIDATE_input_crank');removed=[]
 for name in ['M5 screw tip clearance','Replaceable rod bush flanges']:
  f=next(f for f in c.features if f.name.startswith(name));assert f.healthState==fusion.FeatureHealthStates.WarningFeatureHealthState;sk=f.profile.parentSketch if hasattr(f.profile,'parentSketch') else None;removed.append(f.name);assert f.deleteMe()
  if sk and sk.isValid:assert sk.deleteMe()
 assert d.computeAll();assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features)
 def signature():
  b=c.bRepBodies.item(0);return {'volume':b.volume,'faces':b.faces.count,'edges':b.edges.count}
 baseline=signature();edits=[]
 for key,value in [('lc_crank_radius','30 mm'),('lc_drive_coupling_depth','8 mm'),('lc_drive_fork_gap','9 mm')]:
  p=d.userParameters.itemByName(key);old=p.expression
  try:
   p.expression=value;assert d.computeAll();assert c.bRepBodies.count==1;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);changed=signature();assert abs(changed['volume']-baseline['volume'])>1e-5
  finally:p.expression=old;assert d.computeAll()
  restored=signature();assert abs(restored['volume']-baseline['volume'])<1e-7;edits.append({'parameter':key,'changed_expression':value,'restored_expression':old,'changed':changed,'restored':restored})
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-input-crank.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));print(json.dumps({'passed':True,'removed_empty_cuts':removed,'features':c.features.count,'sketches':c.sketches.count,'edits':edits,'paths':[path],'saved':False}))
'''
r=rpc(s,'cohesive-input-crank-family',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-input-crank-family.json').write_text(json.dumps(record,indent=2));print(record)
for path in record['paths']:fetch(path,Path(path).name)
