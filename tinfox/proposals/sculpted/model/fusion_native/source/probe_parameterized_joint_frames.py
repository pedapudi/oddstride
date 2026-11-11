"""Test native dimensional frame placement in a disposable unsaved design."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
s=script_header()+(ROOT/'source/intent_geometry.py').read_text()+'''
def run(_context: str):
 import json
 app=core.Application.get();leg=app.activeDocument;assert leg.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';assert not leg.isModified;capacity=require_personal_capacity(app,leg,KNOWN,new_cloud_files=0,reserve_slots=1);scratch=app.documents.add(core.DocumentTypes.FusionDesignDocumentType);scratch.name='Tinfox native joint frame audit';d=fusion.Design.cast(app.activeProduct);d.designType=fusion.DesignTypes.ParametricDesignType;root=d.rootComponent
 def perform():
  datum=root.occurrences.addNewComponent(core.Matrix3D.create());datum.component.name='Robot dimensional datum';datum.isGrounded=True;g=IntentGeometry(d,datum.component);g.parameter('probe_hip_x',185);g.parameter('probe_hip_y',68);sk=datum.component.sketches.add(datum.component.xYConstructionPlane);p=g.skeleton_point(sk,'probe_hip_x','probe_hip_y');g.point_dimensions(sk,p,'probe_hip_x','probe_hip_y');hip=p.createForAssemblyContext(datum);m=core.Matrix3D.create();m.translation=core.Vector3D.create(18.5,6.8,0);mount=root.occurrences.addNewComponent(m);mount.component.name='Mount frame';c=mount.component;g2=IntentGeometry(d,c);g2.box('5 mm','5 mm','5 mm','0 mm','0 mm','0 mm','Frame witness solid');point=c.originConstructionPoint.createForAssemblyContext(mount);a=fusion.JointGeometry.createByPoint(hip);b=fusion.JointGeometry.createByPoint(point);inp=root.joints.createInput(b,a);inp.setAsRigidJointMotion();joint=root.joints.add(inp);joint.name='Mount at driven hip datum';assert d.computeAll()
  g.parameter('probe_hip_pitch',30,'deg');g.parameter('probe_knee_pitch',-60,'deg');g.parameter('probe_length',170);g.parameter('probe_radius',28);g.parameter('probe_phase',-78,'deg')
  frames={'mount':mount};joints=[joint]
  def point(occ,x,y,name):
   comp=occ.component;gg=IntentGeometry(d,comp);ss=comp.sketches.add(comp.xZConstructionPlane);ss.name=name;pp=gg.skeleton_point(ss,x,y);gg.point_dimensions(ss,pp,x,y);return fusion.JointGeometry.createByPoint(pp.createForAssemblyContext(occ))
  for key,parent,x,y,angle in [('thigh','mount','0 mm','0 mm','probe_hip_pitch'),('knee','thigh','0 mm','probe_length','probe_knee_pitch'),('crank','thigh','0 mm','0 mm','probe_knee_pitch+probe_phase'),('rod','thigh','0 mm','0 mm','0 deg')]:
   child=root.occurrences.addNewComponent(core.Matrix3D.create());child.component.name=key;IntentGeometry(d,child.component).box('5 mm','5 mm','5 mm','0 mm','0 mm','0 mm',key+' witness');a=point(child,'0 mm','0 mm',key+' joint origin');b=point(frames[parent],x,y,key+' parent datum');inp=root.joints.createInput(a,b);inp.setAsRigidJointMotion();inp.angle=core.ValueInput.createByString(angle);jj=root.joints.add(inp);jj.name=key+' parameterized pose'
   if key=='rod':jj.offsetX.expression='probe_radius*cos(probe_knee_pitch+probe_phase)';jj.offsetY.expression='probe_radius*sin(probe_knee_pitch+probe_phase)'
   frames[key]=child;joints.append(jj)
  poses=[]
  for knee_value in [-60,-156,-102,-48]:
   d.userParameters.itemByName('probe_knee_pitch').expression=str(knee_value)+' deg';assert d.computeAll();poses.append({'knee_deg':knee_value,'frames':{k:o.transform2.asArray() for k,o in frames.items()},'joint_health':[(jj.name,int(jj.healthState),jj.errorOrWarningMessage) for jj in joints]})
  d.userParameters.itemByName('probe_knee_pitch').expression='-60 deg';assert d.computeAll()
  def state():return {'matrix':mount.transform2.asArray(),'health':int(joint.healthState),'message':joint.errorOrWarningMessage}
  before=state();parameter=d.userParameters.itemByName('probe_hip_x');parameter.expression='200 mm';assert d.computeAll();changed=state();parameter.expression='185 mm';assert d.computeAll();restored=state();return {'before':before,'changed':changed,'restored':restored,'capacity':capacity,'leg_modified':leg.isModified,'pose_frames':poses}
 try:record=perform()
 finally:scratch.close(False);leg.activate()
 print(json.dumps(record))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'native-parameterized-joint-frame-probe',timeout=120);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/native-parameterized-joint-frame-probe.json').write_text(json.dumps(record,indent=2));print(record)
