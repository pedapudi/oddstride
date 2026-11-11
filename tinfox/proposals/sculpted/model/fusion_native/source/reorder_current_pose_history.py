"""Keep physical occurrence construction before the parameter-driven pose mates.

Initial-position and as-built features authored after a pose mate otherwise
recalculate from world positions when its upstream angle changes. Reuse native
parts, frames and datum sketches; move only the assembly-driving history.
"""
import gzip,json,sys
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];target=json.loads((ROOT/'manifests/whole-robot-integration-target.json').read_text());model=json.loads(gzip.decompress((ROOT/target['reference_model']).read_bytes()));sys.path.insert(0,str(ROOT.parent));import kinematics as k
k.P.update(model['parameters']);frames={leg:{name:m.tolist()for name,m in k.frames(leg,model['poses']['stand'][leg]).items()}for leg in k.LEGS}
header='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py','native_pose_frames.py','current_pose_frames.py'])
s=header+'''
class ReusedDatumFrames(CurrentLegPoseFrames):
 def point(self,occ,plane='XZ',x='0 mm',y='0 mm',name='Joint datum'):
  key=(occ.component.id,plane,x,y)
  if key in self.point_cache:return self.point_cache[key]
  sketches=[sk for sk in occ.component.sketches if sk.name==name];assert len(sketches)==1,(self.leg,occ.component.partNumber,name,len(sketches));sk=sketches[0];points=[p for p in sk.sketchPoints if p.entityToken!=sk.originPoint.entityToken];assert len(points)==1,(name,len(points));point=points[0];g=IntentGeometry(self.d,occ.component);assert abs(point.geometry.x-g.mm(x)*.1)<1e-8 and abs(point.geometry.y-g.mm(y)*.1)<1e-8,(name,point.geometry.asArray(),x,y);geometry=fusion.JointGeometry.createByPoint(point.createForAssemblyContext(occ));self.point_cache[key]=geometry;return geometry
 def constrain(self):
  datum=next(o for o in self.owner.occurrences if o.component.partNumber=='CURRENT_DATUM_'+self.leg);f=self.frames;k='pose_'+self.leg+'_knee';hip='pose_'+self.leg+'_hip';roll='pose_'+self.leg+'_roll'
  self.mate('Hip mounting position',f['mount'],datum,'XY',offset_x=str(self.front)+'*lc_hip_x',offset_y=str(self.side)+'*lc_roll_y')
  self.mate('Hip roll',f['roll'],f['mount'],'YZ',str(self.side)+'*'+roll)
  self.mate('Hip pitch',f['thigh'],f['roll'],'XZ',hip,offset_x=str(self.front)+'*pr_pitch_x_offset',offset=str(self.side)+'*lc_pitch_offset')
  self.mate('Knee pitch',f['knee'],f['thigh'],'XZ',k,parent_y='lc_thigh_length')
  self.mate('Knee drive phase',f['crank'],f['thigh'],'XZ',k+'+lc_crank_phase')
  self.mate('Parallel link position',f['rod'],f['thigh'],'XZ',offset_x='lc_crank_radius*cos('+k+'+lc_crank_phase)',offset_y='lc_crank_radius*sin('+k+'+lc_crank_phase)')

def run(_context:str):
 import json,time,os
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;tick=time.monotonic();modules={};progress_path=os.path.join(os.path.expanduser('~'),'Library','Caches','Tinfox','current-pose-history-reorder.json');identity=list(core.Matrix3D.create().asArray());ground_released=[]
 def progress(stage,**values):open(progress_path,'w').write(json.dumps({'stage':stage,'elapsed_seconds':time.monotonic()-tick,**values}))
 for leg,(front,side)in{'FL':(1,1),'FR':(1,-1),'RL':(-1,1),'RR':(-1,-1)}.items():
  o=next(o for o in root.occurrences if o.component.partNumber=='CURRENT_ASSEMBLY_'+leg);module=ReusedDatumFrames(d,o,leg,front,side);module.frames={f.component.partNumber.split('_')[-1]:f for f in module.owner.occurrences if f.component.partNumber.startswith('CURRENT_FRAME_')};assert len(module.frames)==6;modules[leg]=module
  def unground(occ):
   if occ.isGrounded:ground_released.append(occ.fullPathName);occ.isGrounded=False
   for child in occ.component.occurrences:unground(child.createForAssemblyContext(occ))
  for frame in module.frames.values():
   fp=module.proxy(frame)
   for child in frame.component.occurrences:unground(child.createForAssemblyContext(fp))
 joints=[j for m in modules.values()for j in m.owner.joints];assert len(joints)==24;old_joint_rows=[{'name':j.name,'index':j.timelineObject.index}for j in joints]
 for j in sorted(joints,key=lambda j:j.timelineObject.index,reverse=True):assert j.deleteMe()
 assert d.computeAll();progress('pose_mates_removed',released_world_grounds=len(ground_released))
 for leg,module in modules.items():
  for group,frame in module.frames.items():
   matrix=list(module.proxy(frame).transform2.asArray());assert max(abs(a-b)for a,b in zip(matrix,identity))<1e-8,(leg,group,'unposed frame',matrix)
 aliases=[(child,child.timelineObject,module,frame)for module in modules.values()for frame in module.frames.values()for child in frame.component.occurrences];assert len(aliases)==128;aliases.sort(key=lambda row:row[1].index);reset=[]
 for occ,creation,module,frame in aliases:
  assert creation.rollTo(False);assert occ.isVaildForEditInitialPosition;occ.initialTransform=core.Matrix3D.create();reset.append(occ.component.partNumber);progress('initial_positions_rebased',complete=len(reset),total=128)
 d.timeline.moveToEnd();assert d.computeAll()
 for occ,creation,module,frame in aliases:
  fp=module.proxy(frame);cp=occ.createForAssemblyContext(fp);assert not cp.isGrounded;assert cp.isGroundToParent;error=max(abs(a-b)for a,b in zip(cp.transform2.asArray(),identity));assert error<1e-8,(occ.component.partNumber,'unposed occurrence',error,list(cp.transform2.asArray()))
 for leg,module in modules.items():
  module.constrain();progress('pose_mates_recreated',leg=leg)
 assert d.computeAll();checks=[]
 for leg,module in modules.items():
  assert len(module.joints)==6 and all(j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for j in module.joints)
  for group,frame in module.frames.items():
   fp=module.proxy(frame);expected=[v*(.1 if j==3 and i<3 else 1)for i,row in enumerate(FRAMES[leg][group])for j,v in enumerate(row)];assert max(abs(a-b)for a,b in zip(fp.transform2.asArray(),expected))<1e-7,(leg,group,'frame')
   for child in frame.component.occurrences:
    cp=child.createForAssemblyContext(fp);error=max(abs(a-b)for a,b in zip(cp.transform2.asArray(),expected));assert error<1e-7,(leg,group,child.component.partNumber,error);checks.append({'leg':leg,'group':group,'part':child.component.partNumber,'matrix_error_cm':error})
 progress('complete');print(json.dumps({'passed':True,'saved':False,'source_target_sha256':TARGET,'old_pose_mates':old_joint_rows,'new_pose_mates':24,'reused_existing_datum_sketches':True,'rebound_child_occurrences':len(aliases),'world_ground_released':ground_released,'standing_checks':checks,'elapsed_seconds':time.monotonic()-tick,'scope':'Reordered native assembly history: physical definitions and initial positions precede all current pose mates. Geometry is unchanged; moving edit/restore validation remains required.'}))
'''.replace('FRAMES',repr(frames)).replace('TARGET',repr(target['model_sha256']))
compile(s,'reorder_current_pose_history.py','exec');a=rpc(s,'current-pose-history-reorder',timeout=1800);assert a[0]['success'],a;rec=json.loads(a[0]['message']);(ROOT/'audits/current-pose-history-reorder.json').write_text(json.dumps(rec,indent=2));print({k:v for k,v in rec.items()if k not in ['standing_checks','old_pose_mates','world_ground_released']})
