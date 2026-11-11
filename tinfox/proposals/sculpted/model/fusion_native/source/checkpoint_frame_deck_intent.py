"""Replace two qualified frame histories without changing their frozen shapes."""
import hashlib,json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1];keys=['chassis_lower_brace','electronics_shelf']
assert json.loads((ROOT/'audits/frame-deck-family-edit-restore.json').read_text())['passed']
for key in keys:
 label='frame-intent-'+key+'-restored';sha=hashlib.sha256((ROOT/'exports'/f'{label}.step').read_bytes()).hexdigest()
 for suffix,gate in [('geometry','geometric_gate_passed'),('sections','section_gate_passed')]:
  record=json.loads((ROOT/'audits'/f'{label}-{suffix}.json').read_text());assert record[gate] and record['native_step_sha256']==sha
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,time

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');assert app.activeDocument==doc and doc.dataFile.versionNumber==12;d=fusion.Design.cast(app.activeProduct);capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);root=d.rootComponent;rows=[]
 for key in KEYS:
  old=next(o for o in root.occurrences if o.component.partNumber==key);new=next(o for o in root.occurrences if o.component.partNumber=='CANDIDATE_'+key);c=new.component;before={'features':old.component.features.count,'sketches':old.component.sketches.count};assert c.bRepBodies.count==1;assert old.deleteMe();c.partNumber=key;new.isLightBulbOn=True;c.attributes.add('Tinfox','ConstructionQuality','Shared frame width and paired mounting datums; native profiles and patterns. Frozen shape and three physical parameter edits/restores pass.');c.attributes.add('Tinfox','ManufacturingRelease','False');rows.append({'part':key,'before':before,'after':{'features':c.features.count,'sketches':c.sketches.count}})
 removed=[]
 while True:
  eligible=[p for p in d.userParameters if p.name.startswith(('chassis_lower_brace_','electronics_shelf_')) and p.isDeletable]
  if not eligible:break
  for p in eligible:removed.append(p.name);assert p.deleteMe()
 assert d.computeAll();assert not any(c.partNumber.startswith('CANDIDATE_') for c in d.allComponents)
 for c in d.allComponents:
  issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,(c.name,issues)
 assert abs(d.userParameters.itemByName('frame_half_y').value-10.2)<1e-8;assert abs(d.userParameters.itemByName('robot_fastener_diametral_allowance').value-.04)<1e-8;paths=[]
 for key in KEYS:
  c=next(c for c in d.allComponents if c.partNumber==key);path=os.path.join(tempfile.gettempdir(),'tinfox-native','frame-intent-'+key+'-final.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));paths.append(path)
 assert doc.save('Replace the brace and electronics deck with compact native profiles and patterns: 62 features become 18. Shared frame width, brace thickness and independent M3 clearance propagate through paired mounting holes and restore exactly. Frozen surfaces and sections match. Rail and hardware family bindings remain unfinished; generated CAD remains authoritative.');print(json.dumps({'save_requested':True,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'parts':rows,'removed_unused_parameters':removed,'capacity':capacity,'paths':paths,'source_of_truth':False}))
'''.replace('KNOWN',repr(known_files())).replace('KEYS',repr(keys))
r=rpc(s,'frame-deck-native-checkpoint',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/frame-deck-native-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k!='capacity'},flush=True)
for p in record['paths']:fetch(p,Path(p).name)
