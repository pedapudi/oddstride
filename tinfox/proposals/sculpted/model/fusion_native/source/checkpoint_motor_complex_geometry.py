"""Protect completed native definitions independently of pending assembly placement."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
from motor_complex_exports import COMPONENTS
ROOT=Path(__file__).resolve().parents[1]
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);rows=[]
 for key,number in PARTS.items():
  c=next(c for c in d.allComponents if c.partNumber==number);assert c.bRepBodies.count==1 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),(key,c.name);rows.append({'part':key,'component':number,'features':c.features.count,'sketches':c.sketches.count,'bodies':1})
 assert len(rows)==13;before=doc.dataFile.versionNumber;assert doc.save('Protect all 13 native paired-6810 motor-complex definitions, corrected assembly access, shared fit bindings and reference library. Geometry and staged-assembly comparisons passed. Clean static occurrence placement and publication gates remain pending.');print(json.dumps({'previous_version':before,'version_at_return':doc.dataFile.versionNumber,'complete_at_return':doc.dataFile.isComplete,'modified_at_return':doc.isModified,'parts':rows,'capacity':capacity,'native_source_of_truth':False}))
'''.replace('KNOWN',repr(known_files())).replace('PARTS',repr({k:v[0]for k,v in COMPONENTS.items()}))
r=rpc(s,'motor-complex-geometry-checkpoint',timeout=240);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/motor-complex-geometry-checkpoint.json').write_text(json.dumps(record,indent=2));print(record)
