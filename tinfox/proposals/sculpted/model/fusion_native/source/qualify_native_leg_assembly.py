"""Check physical native occurrences against independent linkage frames."""
import gzip,json,sys
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent));import kinematics as k
model=json.loads(gzip.decompress((ROOT/'snapshots/cohesive-limb/model.json.gz').read_bytes()));k.P.update(model['parameters']);baseline=k.P.copy();cases=[]
for name,pose in model['poses'].items():cases.append({'name':name,'pose':pose,'edits':{},'frames':{leg:{name:m.tolist() for name,m in k.frames(leg,pose[leg]).items()} for leg in k.LEGS}})
for parameter,source,value in [('lc_thigh_length','thigh',180),('lc_hip_x','hip_x',200),('lc_roll_y','roll_y',73),('lc_pitch_offset','pitch_offset',5)]:
 k.P.update(baseline);k.P[source]=value;pose=model['poses']['stand'];cases.append({'name':'Edit '+parameter,'pose':pose,'edits':{parameter:f'{value} mm'},'frames':{leg:{name:m.tolist() for name,m in k.frames(leg,pose[leg]).items()} for leg in k.LEGS}})
k.P.update(baseline);cases.append({'name':'Restored stand','pose':model['poses']['stand'],'edits':{},'frames':{leg:{name:m.tolist() for name,m in k.frames(leg,model['poses']['stand'][leg]).items()} for leg in k.LEGS}})
s='''import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;rows=[];parts=[];defs={};frames={};modules=[];started=time.monotonic()
 for leg in root.occurrences:
  if not leg.component.partNumber.startswith('ASSEMBLY_'):continue
  modules.append(leg)
  for frame in leg.childOccurrences:
   attr=frame.component.attributes.itemByName('Tinfox','KinematicFrame')
   if not attr:continue
   lname,group=attr.value.split(':');frames[(lname,group)]=frame
   for part in frame.childOccurrences:parts.append((lname,group,part));defs[part.component.partNumber]=part.component
 assert len(parts)==80 and len(defs)==44
 def state(c):return {'volumes':[b.volume for b in c.bRepBodies],'bounds':[[*b.boundingBox.minPoint.asArray(),*b.boundingBox.maxPoint.asArray()] for b in c.bRepBodies]}
 original={key:state(c) for key,c in defs.items()};parameters={name:d.userParameters.itemByName(name).expression for name in ['lc_thigh_length','lc_hip_x','lc_roll_y','lc_pitch_offset']};pose_parameters={f'pose_{leg}_{axis}':d.userParameters.itemByName(f'pose_{leg}_{axis}').expression for leg in ['FL','FR','RL','RR'] for axis in ['roll','hip','knee']}
 def matrix(rows):
  m=core.Matrix3D.create();assert m.setWithArray([v*(.1 if j==3 and i<3 else 1) for i,row in enumerate(rows) for j,v in enumerate(row)]);return m
 try:
  for case in CASES:
   tick=time.monotonic()
   for name,expression in parameters.items():d.userParameters.itemByName(name).expression=case['edits'].get(name,expression)
   for leg,pose in case['pose'].items():
    for axis,value in zip(['roll','hip','knee'],pose):d.userParameters.itemByName('pose_'+leg+'_'+axis).expression=str(value)+' deg'
   assert d.computeAll();worst=0;vworst=0
   for leg,group,part in parts:
    expected=matrix(case['frames'][leg][group]);actual=part.transform2;error=max(abs(a-b) for a,b in zip(expected.asArray(),actual.asArray()));worst=max(worst,error);assert error<1e-7,(case['name'],part.fullPathName,error)
    for body in part.component.bRepBodies:
     point=body.vertices.item(0).geometry.copy();point.transformBy(expected);actual_point=body.createForAssemblyContext(part).vertices.item(0).geometry;delta=point.distanceTo(actual_point);vworst=max(vworst,delta);assert delta<1e-7,(case['name'],part.fullPathName,delta)
   for key,c in defs.items():assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),(case['name'],key)
   for leg in modules:assert all(j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for j in leg.component.joints),(case['name'],leg.name)
   rows.append({'case':case['name'],'maximum_matrix_component_error_cm':worst,'maximum_vertex_error_cm':vworst,'physical_instances_checked':len(parts),'seconds':time.monotonic()-tick})
 finally:
  for name,expression in (parameters|pose_parameters).items():d.userParameters.itemByName(name).expression=expression
  assert d.computeAll()
 restored={key:state(c) for key,c in defs.items()};restore_error=max(abs(a-b) for key in defs for aa,bb in zip(original[key]['bounds'],restored[key]['bounds']) for a,b in zip(aa,bb));assert restore_error<1e-7,restore_error
 for key in defs:assert max(abs(a-b) for a,b in zip(original[key]['volumes'],restored[key]['volumes']))<1e-6,key
 app.activeViewport.fit();print(json.dumps({'passed':True,'saved':False,'checks':rows,'definition_geometry_restored':True,'maximum_restored_bound_error_cm':restore_error,'physical_instances':80,'unique_definitions':44,'native_pose_mates':24,'elapsed_seconds':time.monotonic()-started,'limitation':'Native driven poses, not dynamic free joints. No collision-free claim for every tested pose.'}))
'''.replace('CASES',repr(cases))
r=rpc(s,'native-leg-assembly-qualification',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/native-leg-assembly-qualification.json').write_text(json.dumps(record,indent=2));print(record)
