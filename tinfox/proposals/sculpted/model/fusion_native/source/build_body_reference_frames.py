"""Keep purchased dimensions fixed while shared chassis datums move their instances."""
import json
from pathlib import Path
from run_native import rpc
from body_reference_plan import plan
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'\n'+(ROOT/'source/body_reference_coordinates.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert d.activateRootComponent();assert not any(c.partNumber.startswith('BODY_PLACEMENT_') for c in d.allComponents);tick=time.monotonic();lidar_bindings=bind_lidar_reference_coordinates(d);library={}
 for name in PLAN['assignments']:
  matches=[o for o in root.allOccurrences if o.component.partNumber==name or o.component.name==name];assert len(matches)==1,(name,len(matches));library[name]=matches[0]
 def shape(occ):
  c=occ.component;assert c.bRepBodies.count>=1,(c.name,c.bRepBodies.count);bodies=[b.createForAssemblyContext(occ) for b in c.bRepBodies];bounds=[min(getattr(b.boundingBox.minPoint,axis) for b in bodies)*10 for axis in ['x','y','z']]+[max(getattr(b.boundingBox.maxPoint,axis) for b in bodies)*10 for axis in ['x','y','z']]
  return {'volume_mm3':sum(b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume for b in c.bRepBodies)*1000,'bounds_mm':bounds,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'path':occ.fullPathName,'matrix':list(occ.transform2.asArray())}

 before={name:shape(occ) for name,occ in library.items()};frames={};joints=[]
 for name in PLAN['groups']:
  occ=root.occurrences.addNewComponent(core.Matrix3D.create());occ.component.name='Placement '+name.replace('_',' ');occ.component.partNumber='BODY_PLACEMENT_'+name;frames[name]=occ
 moved={}
 for name,group in PLAN['assignments'].items():
  occ=library[name];visible=occ.isLightBulbOn
  if occ.isGrounded:occ.isGrounded=False
  if occ.isGroundToParent:occ.isGroundToParent=False
  result=occ.moveToComponent(frames[group]);assert result;proxy=result if result.assemblyContext else result.createForAssemblyContext(frames[group]);proxy.isGroundToParent=True;proxy.isLightBulbOn=visible;proxy.attributes.add('Tinfox','SourceInstance',name);proxy.attributes.add('Tinfox','PlacementFrame',group);moved[name]=proxy
 datum=root.occurrences.addNewComponent(core.Matrix3D.create());datum.component.name='Grounded body placement datum';datum.component.partNumber='DATUM_BODY_PLACEMENT';datum.isGrounded=True;points={}
 def point(occ):
  sk=occ.component.sketches.add(occ.component.xYConstructionPlane);sk.name='Translation origin';sk.isLightBulbOn=False;return fusion.JointGeometry.createByPoint(sk.originPoint.createForAssemblyContext(occ))
 fixed=point(datum)
 for name,occ in frames.items():
  if occ.isGrounded:occ.isGrounded=False
  if occ.isGroundToParent:occ.isGroundToParent=False
  inp=root.joints.createInput(point(occ),fixed);inp.setAsRigidJointMotion();joint=root.joints.add(inp);joint.name='Body datum '+name.replace('_',' ')
  for parameter,key in [(joint.offsetX,'x'),(joint.offsetY,'y'),(joint.offset,'z')]:parameter.expression=PLAN['groups'][name][key]
  joint.attributes.add('Tinfox','PlacementRule',json.dumps(PLAN['groups'][name]));joints.append(joint)
 assert d.computeAll();after={name:shape(occ) for name,occ in moved.items()}
 for name,a in before.items():
  b=after[name];assert a['features']==b['features'] and a['sketches']==b['sketches'];assert abs(a['volume_mm3']-b['volume_mm3'])<max(.001,1e-7*a['volume_mm3']),(name,'volume');assert max(abs(x-y) for x,y in zip(a['bounds_mm'],b['bounds_mm']))<.0001,(name,a['bounds_mm'],b['bounds_mm'])
 assert all(j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for j in joints)
 for c in d.allComponents:assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),c.name
 print(json.dumps({'passed':True,'saved':False,'before':before,'after':after,'groups':PLAN['groups'],'assignments':PLAN['assignments'],'frames':len(frames),'instances':len(moved),'elapsed_seconds':time.monotonic()-tick,'scope':PLAN['scope']}))
'''.replace('PLAN',repr(plan()))
r=rpc(s,'body-reference-frames-build',timeout=480);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/body-reference-frames-build.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'frames':record['frames'],'instances':record['instances'],'seconds':record['elapsed_seconds']})
