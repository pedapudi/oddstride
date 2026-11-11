"""Save reviewed candidate work without changing the protected robot assembly."""
import json,hashlib
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
for key in ['shin_inner','shin_outer','shin_inner_right','shin_outer_right']:
 label='rounded-native-'+key;sha=hashlib.sha256((ROOT/'exports'/f'{label}.step').read_bytes()).hexdigest()
 for suffix,gate in [('geometry','geometric_gate_passed'),('sections','section_gate_passed')]:
  row=json.loads((ROOT/'audits'/f'{label}-{suffix}.json').read_text());assert row[gate]and row['native_step_sha256']==sha
for name in ['rounded-shin-family-edits','rounded-shin-native-interfaces','rounded-shin-service','rounded-shin-motion','slim-motor-mounts-family-qualification']:
 assert json.loads((ROOT/'audits'/f'{name}.json').read_text())['passed']
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json
def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);assert doc.dataFile.versionNumber==14;rows=[]
 for c in d.allComponents:
  issues=[(f.name,f.errorOrWarningMessage)for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,(c.name,issues)
 for o in d.rootComponent.occurrences:
  c=o.component
  if not c.partNumber.startswith('CANDIDATE_'):continue
  assert c.partNumber.startswith(('CANDIDATE_sl_','CANDIDATE_round_shin_')),c.partNumber;o.isLightBulbOn=False
  for plane in c.constructionPlanes:plane.isLightBulbOn=False
  rows.append({'part':c.partNumber,'name':c.name,'hidden':not o.isLightBulbOn,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count})
 assert len(rows)==10;assert doc.save('Prototype limb work checkpoint: comparison-tested slim motor mounts and rounded shin candidates with open washer seats; four shin family edits restored. Compact closed-thigh stock and linked sidewall cavity remain in progress. Candidates are hidden and not installed in the protected assembly. Paired standard roll bearings and final assembly migration are pending.');print(json.dumps({'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'capacity':capacity,'candidates':rows,'assembly_updated':False,'source_of_truth_changed':False,'checkpoint_kind':'Saved work, not a fabrication or whole-robot release.'}))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'prototype-leg-work-checkpoint',timeout=180);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/prototype-leg-work-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k not in['capacity','candidates']})
