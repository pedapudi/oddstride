"""Save the verified current pose scaffold, then defer its solves during reference staging."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1];assert json.loads((ROOT/'audits/current-native-pose-frames.json').read_text())['passed']
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);tick=time.monotonic();groups=[o for o in d.rootComponent.occurrences if o.component.partNumber.startswith('CURRENT_ASSEMBLY_')];assert len(groups)==4;joints=[j for o in groups for j in o.component.joints];assert len(joints)==24 and all(not j.isSuppressed and j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for j in joints);before=doc.dataFile.versionNumber;assert doc.save('Add four native leg pose scaffolds with24 parameter-driven frame mates. All standing matrices match current5mm fore-aft hip offset and28mm crank linkage. Physical parts and current references are not yet installed; published Leg24 bench remains unchanged.');saved_return={'version_at_return':doc.dataFile.versionNumber,'complete_at_return':doc.dataFile.isComplete};
 for j in joints:j.isSuppressed=True
 assert all(j.isSuppressed for j in joints);print(json.dumps({'saved_scaffold':saved_return,'previous_version':before,'suppressed_current_pose_joints':24,'purpose':'Temporary solver deferral during bulk reference and native occurrence staging; restore and verify before assembly publication.','working_modified':doc.isModified,'capacity':capacity,'elapsed_seconds':time.monotonic()-tick}))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'current-frame-checkpoint-and-defer',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-frame-checkpoint-and-defer.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k!='capacity'})
