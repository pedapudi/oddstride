"""Save qualified body placement dependencies without changing frozen part geometry."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
for name in ['body-reference-family-edit-restore','native-frame-family-solid-interfaces']:assert json.loads((ROOT/'audits'/f'{name}.json').read_text())['passed']
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');doc.activate();assert doc.dataFile.versionNumber==16;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);frames=[c for c in d.allComponents if c.partNumber.startswith('BODY_PLACEMENT_')];assert len(frames)==14;assert root.joints.count==14;placements=[o for o in root.allOccurrences if o.attributes.itemByName('Tinfox','PlacementFrame')];assert len(placements)==90
 for c in d.allComponents:assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),c.name
 assert all(j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for j in root.joints);assert not any(c.partNumber.startswith('CANDIDATE_') for c in d.allComponents)
 retained=[]
 for occ in root.occurrences:
  if occ.component.partNumber=='REFERENCE_Body_body':
   solids=sum(c.bRepBodies.count for c in [occ.component]+[o.component for o in occ.childOccurrences]);retained.append({'part':occ.component.partNumber,'remaining_direct_or_child_bodies':solids,'reason':'Retain reference import history; physical items have moved into named placement frames.'});occ.isLightBulbOn=False
 assert doc.save('Bind ninety body/reference instances to fourteen shared native placement datums. Six edit/restore cases preserve purchased dimensions and move hardware with the frame; thirty-six native solid interface checks pass. Remove duplicate lidar-cover placement ownership while preserving its baseline geometry. CNC access, actual battery interfaces, screw-length selection and physical qualification remain open; generated CAD remains authoritative.');print(json.dumps({'save_requested':True,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'frames':len(frames),'instances':len(placements),'retained_reference_history':retained,'capacity':capacity,'source_of_truth':False}))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'body-reference-placement-checkpoint',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/body-reference-placement-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k!='capacity'})
