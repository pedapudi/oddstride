"""Create native current-leg assembly datums before installing physical instances."""
import gzip,json,sys
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];target=json.loads((ROOT/'manifests/whole-robot-integration-target.json').read_text());model=json.loads(gzip.decompress((ROOT/target['reference_model']).read_bytes()));sys.path.insert(0,str(ROOT.parent));import kinematics as k
k.P.update(model['parameters']);frames={leg:{name:m.tolist()for name,m in k.frames(leg,model['poses']['stand'][leg]).items()}for leg in k.LEGS}
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py','native_pose_frames.py','current_pose_frames.py'])+'''
def run(_context:str):
 import json,time
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;tick=time.monotonic();modules={};rows=[]
 for leg,(front,side) in {'FL':(1,1),'FR':(1,-1),'RL':(-1,1),'RR':(-1,-1)}.items():
  number='CURRENT_ASSEMBLY_'+leg;assert not any(c.partNumber==number for c in d.allComponents);o=root.occurrences.addNewComponent(core.Matrix3D.create());o.component.name=leg+' current leg';o.component.partNumber=number;o.isGrounded=True;o.isLightBulbOn=False;module=CurrentLegPoseFrames(d,o,leg,front,side);modules[leg]=module
  for name in FRAMES[leg]:module.add_frame(name,core.Matrix3D.create())
  for frame in module.frames.values():
   proxy=module.proxy(frame)
   if proxy.isGrounded:proxy.isGrounded=False
   proxy.isGroundToParent=False
  module.constrain();assert d.computeAll()
  for name,expected in FRAMES[leg].items():
   values=[v*(.1 if j==3 and i<3 else 1)for i,row in enumerate(expected)for j,v in enumerate(row)];actual=module.matrices()[name];error=max(abs(a-b)for a,b in zip(values,actual));assert error<1e-7,(leg,name,error,actual,values);rows.append({'leg':leg,'frame':name,'matrix_cm':actual,'maximum_matrix_error_cm':error})
  assert all(j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for j in module.joints)
 assert [o.component.partNumber for o in root.occurrences if o.isLightBulbOn]==['BENCH_MOTOR_COMPLEX'];print(json.dumps({'passed':True,'saved':False,'frames':rows,'joints':sum(len(m.joints)for m in modules.values()),'elapsed_seconds':time.monotonic()-tick,'source_target_sha256':TARGET,'scope':'Native parameter-driven pose frames at standing pose; physical instance installation and moving clearance remain pending.'}))
'''.replace('FRAMES',repr(frames)).replace('TARGET',repr(target['model_sha256']))
compile(s,'current_pose_frames.py','exec');r=rpc(s,'current-native-pose-frames',timeout=900);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-native-pose-frames.json').write_text(json.dumps(record,indent=2));print({'frames':len(record['frames']),'seconds':record['elapsed_seconds']})
