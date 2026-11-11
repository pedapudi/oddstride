"""Replace the colliding hub and preserve the established component appearances."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
assert json.loads((ROOT/'audits/hub-case-family-edit-restore.json').read_text())['passed']
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;bench=next(o for o in root.occurrences if o.component.partNumber=='BENCH_MOTOR_COMPLEX');old=next(o for o in bench.component.occurrences if o.component.partNumber=='CANDIDATE_sl_hip_hub');part=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_hc_hip_hub');new=bench.component.occurrences.addExistingComponent(part,old.transform2);new.isGroundToParent=True;new.attributes.add('Tinfox','BenchPart','hip_hub');assert old.deleteMe();appearance_rows=[]
 for new_key,old_key in [('CANDIDATE_hc_hip_hub','CANDIDATE_sl_hip_hub'),('CANDIDATE_hc_hip_hub_right','CANDIDATE_sl_hip_hub'),('CANDIDATE_ks_motor_mount_ring','CANDIDATE_sl_motor_mount_ring'),('CANDIDATE_ks_motor_mount_ring_right','CANDIDATE_sl_motor_mount_ring'),('CANDIDATE_rc_hip_stator_closure_1','CANDIDATE_pr_hip_stator_closure_1'),('CANDIDATE_rc_motor_carrier_1','CANDIDATE_pr_motor_carrier_1'),('CANDIDATE_rc_motor_carrier_-1','CANDIDATE_pr_motor_carrier_1')]:
  body=next(c for c in d.allComponents if c.partNumber==new_key).bRepBodies.item(0);source=next(c for c in d.allComponents if c.partNumber==old_key).bRepBodies.item(0);body.material=source.material;body.appearance=source.appearance;appearance_rows.append({'part':new_key,'material':body.material.name,'appearance':body.appearance.name})
 for o in root.occurrences:o.isLightBulbOn=o==bench
 visible=[]
 def show(o):
  o.isLightBulbOn=True
  for b in o.component.bRepBodies:b.isLightBulbOn=True;assert b.createForAssemblyContext(o).isVisible;visible.append(o.fullPathName+' / '+b.name)
  for child in o.component.occurrences:show(child.createForAssemblyContext(o))
 show(bench);assert len(visible)==121;bench.component.name='Motor complex - corrected native assembly candidate';bench.component.attributes.add('Tinfox','AssemblyReleaseReady','false');app.activeViewport.fit();print(json.dumps({'saved_version':doc.dataFile.versionNumber,'working_modified':doc.isModified,'visible_bodies':121,'replaced_hub':'CANDIDATE_hc_hip_hub','retained_native_parent':'CANDIDATE_sl_hip_hub','appearance_roles_preserved':appearance_rows,'assembly_release_ready':False}))
'''
compile(s,'activate_hub_case_relief.py','exec');r=rpc(s,'case-relief-bench-activation',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/case-relief-bench-activation.json').write_text(json.dumps(record,indent=2));print(record)
