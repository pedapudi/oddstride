"""Arrange native custom parts as four physical legs without duplicate bodies."""
import gzip,json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];model=json.loads(gzip.decompress((ROOT/'snapshots/cohesive-limb/model.json.gz').read_bytes()));inventory=json.loads((ROOT/'audits/leg-v7-save-verification.json').read_text());keys={p['part'] for p in inventory['parts'] if p['bodies']};instances=[{'key':p['mesh'],'name':p['name'],'leg':p['leg'],'group':p['group']} for p in model['parts'] if p.get('leg') and p['mesh'] in keys]
assert len(instances)==80 and keys=={p['key'] for p in instances}
import sys
sys.path.insert(0,str(ROOT.parent));import kinematics as k
k.P.update(model['parameters']);frames={leg:{name:m.tolist() for name,m in k.frames(leg,model['poses']['stand'][leg]).items()} for leg in k.LEGS}
s='\n'.join((ROOT/'source'/p).read_text() for p in ['intent_geometry.py','native_pose_frames.py'])+'''
def run(_context: str):
 import json,time
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';assert doc.dataFile.versionNumber==7;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert not any(o.component.partNumber.startswith('ASSEMBLY_') for o in root.occurrences);started=time.monotonic();timings={};library={o.component.partNumber:o for o in root.occurrences if o.component.bRepBodies.count};components={key:o.component for key,o in library.items()};before={key:{'features':c.features.count,'sketches':c.sketches.count,'volumes':[b.volume for b in c.bRepBodies],'bounds':[[b.boundingBox.minPoint.x,b.boundingBox.minPoint.y,b.boundingBox.minPoint.z,b.boundingBox.maxPoint.x,b.boundingBox.maxPoint.y,b.boundingBox.maxPoint.z] for b in c.bRepBodies]} for key,c in components.items()}
 def matrix(rows):
  values=[v*(.1 if j==3 and i<3 else 1) for i,row in enumerate(rows) for j,v in enumerate(row)];m=core.Matrix3D.create();assert m.setWithArray(values);return m
 modules={}
 for leg,(front,side) in {'FL':(1,1),'FR':(1,-1),'RL':(-1,1),'RR':(-1,-1)}.items():
  occ=root.occurrences.addNewComponent(core.Matrix3D.create());occ.component.name=leg+' leg';occ.component.partNumber='ASSEMBLY_'+leg;occ.isGrounded=True;module=NativeLegPoseFrames(d,occ,leg,front,side);modules[leg]=module
  for name,rows in FRAMES[leg].items():module.add_frame(name,core.Matrix3D.create())
 timings['frames_seconds']=time.monotonic()-started;used=set();placed=[]
 for row in INSTANCES:
  module=modules[row['leg']];frame=module.frames[row['group']];frame_proxy=module.proxy(frame);key=row['key']
  if key not in used:
   moved=library[key].moveToComponent(frame_proxy);assert moved;occ=moved if moved.assemblyContext else moved.createForAssemblyContext(frame_proxy);used.add(key)
  else:
   native=frame.component.occurrences.addExistingComponent(components[key],core.Matrix3D.create());occ=native.createForAssemblyContext(frame_proxy)
  if occ.isGrounded:occ.isGrounded=False
  occ.isGroundToParent=True
  occ.attributes.add('Tinfox','SourceInstance',row['name']);occ.attributes.add('Tinfox','NativePart',key);placed.append((row,occ))
 assert used==set(library);timings['placement_seconds']=time.monotonic()-started-timings['frames_seconds']
 for module in modules.values():
  for frame in module.frames.values():module.proxy(frame).isGroundToParent=False
  module.constrain()
 timings['joint_seconds']=time.monotonic()-started-sum(timings.values());assert d.computeAll();after={}
 for key,c in components.items():
  assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),key;record={'features':c.features.count,'sketches':c.sketches.count,'volumes':[b.volume for b in c.bRepBodies],'bounds':[[b.boundingBox.minPoint.x,b.boundingBox.minPoint.y,b.boundingBox.minPoint.z,b.boundingBox.maxPoint.x,b.boundingBox.maxPoint.y,b.boundingBox.maxPoint.z] for b in c.bRepBodies]};assert record['features']==before[key]['features'] and record['sketches']==before[key]['sketches'];assert len(record['volumes'])==len(before[key]['volumes']);assert max(abs(a-b) for a,b in zip(record['volumes'],before[key]['volumes']))<1e-6,(key,record,before[key]);assert max(abs(a-b) for aa,bb in zip(record['bounds'],before[key]['bounds']) for a,b in zip(aa,bb))<1e-7,(key,record,before[key]);after[key]=record
 rows=[]
 for row,occ in placed:
  expected=matrix(FRAMES[row['leg']][row['group']]).asArray();actual=occ.transform2.asArray();error=max(abs(a-b) for a,b in zip(expected,actual));assert error<1e-7,(row,error,actual,expected);body=occ.component.bRepBodies.item(0);point=body.vertices.item(0).geometry.copy();point.transformBy(matrix(FRAMES[row['leg']][row['group']]));actual_point=body.createForAssemblyContext(occ).vertices.item(0).geometry;assert point.distanceTo(actual_point)<1e-7,(row,point.asArray(),actual_point.asArray());rows.append(row|{'path':occ.fullPathName,'transform_cm':actual,'maximum_matrix_component_error_cm':error})
 for module in modules.values():assert all(j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for j in module.joints)
 for occ in root.occurrences:
  if occ.component.partNumber.endswith('_design_master'):occ.isLightBulbOn=False
 app.activeViewport.fit();timings['verification_seconds']=time.monotonic()-started-sum(timings.values());print(json.dumps({'passed':True,'saved':False,'native_custom_definitions':len(components),'physical_custom_instances':len(rows),'instances':rows,'frames':{leg:m.matrices() for leg,m in modules.items()},'timings':timings,'native_parameter_mates':sum(len(m.joints) for m in modules.values()),'scope':'Physical custom parts only. Parameter-driven native pose mates, not free dynamic revolute joints. Vendor/hardware references and cross-subsystem validation remain incomplete.'}))
'''
s=s.replace('FRAMES',repr(frames)).replace('INSTANCES',repr(instances))
r=rpc(s,'native-leg-assembly-build',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/native-leg-assembly-build.json').write_text(json.dumps(record,indent=2));print({key:value for key,value in record.items() if key not in ['instances','frames']})
