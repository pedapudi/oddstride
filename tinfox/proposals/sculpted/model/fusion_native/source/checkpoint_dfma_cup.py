"""Checkpoint the changed cup and inspect only the pose-driver history relevant to iteration cost."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);groups=[o for o in root.occurrences if o.component.partNumber=='DFMA_PROPOSAL_FL'];assert len(groups)==1;group=groups[0];cup=[c for c in d.allComponents if c.partNumber=='DFMA_REAR_LOADED_CUP_FL'];assert len(cup)==1 and cup[0].bRepBodies.count==1;joints=[]
 for module in root.occurrences:
  if module.component.partNumber.startswith('CURRENT_ASSEMBLY_'):
   for j in module.component.joints:joints.append({'name':j.name,'module':module.component.partNumber,'timeline_index':j.timelineObject.index})
 assert len(joints)==24;before=doc.dataFile.versionNumber;assert before==30;group.component.attributes.add('Tinfox','BaselineReference','Master63 / Leg30 baseline remains canonical. This isolated DFMA architecture proposal is not promoted.');assert doc.save('Isolated DFMA rear-loaded hip cup: integral stator face removes the separate closure and its six fastener pieces. Native construction and changed-part export complete; focused insertion, tool and structural checks pending. Published Master63 remains pinned to Leg30.');print(json.dumps({'previous_version':before,'version_at_return':doc.dataFile.versionNumber,'complete_at_return':doc.dataFile.isComplete,'modified_at_return':doc.isModified,'proposal_group_timeline_index':group.timelineObject.index,'cup_feature_indices':[f.timelineObject.index for f in cup[0].features],'current_pose_joints':joints,'timeline_count':d.timeline.count,'capacity':capacity,'scope':'One changed-part checkpoint. No whole-model export, reopen, archive or baseline migration revalidation.'}))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'dfma-cup-checkpoint',timeout=300);assert r[0]['success'],r;d=json.loads(r[0]['message']);(ROOT/'audits/dfma-cup-checkpoint.json').write_text(json.dumps(d,indent=2));print({k:v for k,v in d.items()if k not in ['capacity','current_pose_joints','cup_feature_indices']});print('first current pose joint',min(j['timeline_index']for j in d['current_pose_joints']))
