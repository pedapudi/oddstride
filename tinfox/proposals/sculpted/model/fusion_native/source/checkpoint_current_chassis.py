"""Save the complete frozen body inventory without promoting robot authority."""
import json,hashlib
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
for label in ['current-front-crossmember-native','current-lidar-lid-native','current-belly-native']:
 sha=hashlib.sha256((ROOT/'exports'/f'{label}.step').read_bytes()).hexdigest()
 for suffix,gate in [('geometry','geometric_gate_passed'),('sections','section_gate_passed')]:
  r=json.loads((ROOT/'audits'/f'{label}-{suffix}.json').read_text());assert r[gate] and r['native_step_sha256']==sha,(label,suffix)
assert json.loads((ROOT/'audits/native-body-reference-shape.json').read_text())['passed'];assert json.loads((ROOT/'audits/current-chassis-update-qualification.json').read_text())['passed']
keys=[p['key'] for p in json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low']['custom_parts'] if any(i['group']=='body' for i in p['instances']) and p['key'] not in ['front_fascia','body_nose_surround']];assert len(keys)==18
s=script_header()+'''
import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,time

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:R7U8KNNBSA6o3YwVNF2ZQQ';d=fusion.Design.cast(app.activeProduct);capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);rows=[]
 for key in KEYS:
  c=next(c for c in d.allComponents if c.partNumber==key);assert c.bRepBodies.count==1;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),key
  for sk in c.sketches:sk.isLightBulbOn=False
  for pl in c.constructionPlanes:pl.isLightBulbOn=False
  for ax in c.constructionAxes:ax.isLightBulbOn=False
  for b in c.bRepBodies:b.isLightBulbOn=True
  c.attributes.add('Tinfox','ManufacturingRelease','False');rows.append({'part':key,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count})
 for o in d.rootComponent.occurrences:
  if o.component.partNumber in KEYS:o.isLightBulbOn=True
 assert not any(c.partNumber.startswith('CANDIDATE_') for c in d.allComponents);previous=doc.dataFile.versionNumber;tick=time.monotonic();assert doc.save('Complete frozen low chassis: current upper cover, native lower shell, sensor root bores and lidar lid placement; 82 source reference items with nonphysical clearance marked. Retired 279-feature cover removed. Whole robot and family qualification remain open.');path=os.path.join(tempfile.gettempdir(),'tinfox-native','Tinfox-Chassis-complete-low-checkpoint.f3d');assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path));print(json.dumps({'save_requested':True,'previous_version':previous,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'path':path,'parts':rows,'reference_items':82,'nonphysical_reference_items':['electronics_clearance'],'capacity':capacity,'elapsed_seconds':time.monotonic()-tick,'source_of_truth_changed':False}))
'''.replace('KNOWN',repr(known_files())).replace('KEYS',repr(keys))
r=rpc(s,'current-chassis-checkpoint',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-chassis-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k not in ['parts','capacity']});fetch(record['path'],Path(record['path']).name)
