"""Compare every native custom part against the frozen robot in motion and service."""
import gzip,hashlib,json,sys,time
from pathlib import Path
import numpy as np
import trimesh
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent));import kinematics as k
from metrology_mesh import absolute_tessellate
from audit_part import volume
start=time.monotonic();target=json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low'];raw=gzip.decompress((ROOT/target['reference_model']).read_bytes());assert hashlib.sha256(raw).hexdigest()==target['source_model_sha256'];model=json.loads(raw);k.P.update(model['parameters']);inventory=json.loads((ROOT/'manifests/current-native-exports.json').read_text());custom={r['key']:r for r in target['custom_parts']};hardware={r['key']:r for r in json.loads((ROOT/'manifests/current-exact-hardware-references.json').read_text())['parts']};parts={p['name']:p for p in model['parts'] if p.get('service_role') not in ['keepout','withdrawal'] and p['name']!='electronics_clearance'}
assembly_target_path=ROOT/'manifests/native-assembly-target.json'
assembly_scope=None
if assembly_target_path.exists():
 assembly_scope=json.loads(assembly_target_path.read_text());raw=gzip.decompress((ROOT/assembly_scope['reference_model']).read_bytes());assert hashlib.sha256(raw).hexdigest()==assembly_scope['model_sha256'];model=json.loads(raw);k.P.update(model['parameters']);target={**target,'source_model_sha256':assembly_scope['model_sha256']};body_target=json.loads((ROOT/'manifests/current-body-target.json').read_text())
 for key in body_target['custom_keys']:custom[key]={**custom[key],'files':body_target['files'][key]}
 for key in body_target['reference_hardware_keys']:hardware[key]={**body_target['files'][key]['step'],'key':key}
 parts={p['name']:p for p in model['parts'] if p.get('service_role') not in ['keepout','withdrawal'] and p['name']!='electronics_clearance'}
source_meshes={key:trimesh.Trimesh(v['vertices'],v['faces'],process=False) for key,v in model['meshes'].items()};native_meshes=dict(source_meshes);cache=ROOT/'audits/native-motion-mesh-cache';cache.mkdir(exist_ok=True);inputs={};shape_cache={}
for key in sorted(custom):
 row=inventory['parts'][key];path=ROOT/row['path'];sha=hashlib.sha256(path.read_bytes()).hexdigest();assert sha==row['sha256'] and row['shape_gate_passed_for_matching_export'];saved=cache/(sha+'-002-004.npz')
 if key=='shin_outer_right':
  native_path=ROOT/'exports/native-shin-outer-right-mesh.json.gz';proof=json.loads((ROOT/'audits/native-right-shin-direct-mesh-validation.json').read_text());assert proof['passed'] and proof['native_mesh_sha256']==hashlib.sha256(native_path.read_bytes()).hexdigest();direct=json.loads(gzip.decompress(native_path.read_bytes()));vertices=np.array(direct['vertices']);faces=np.array(direct['faces'])
 elif saved.exists():
  data=np.load(saved);vertices,faces=data['vertices'],data['faces']
 else:
  shape=cq.importers.importStep(str(path)).val();assert shape.isValid();v,f=absolute_tessellate(shape,.02,.04);vertices=np.array([p.toTuple() for p in v]);faces=np.array(f);np.savez_compressed(saved,vertices=vertices,faces=faces)
 native_meshes[key]=trimesh.Trimesh(vertices,faces,process=False);inputs[key]={'path':row['path'],'sha256':sha,'geometry_audit':row['geometry_audit'],'triangles':len(faces),'mesh_source':'Fusion meshManager' if key=='shin_outer_right' else 'Absolute-deflection native STEP triangulation'}
 if key=='shin_outer_right':inputs[key]['direct_mesh_sha256']=proof['native_mesh_sha256'];inputs[key]['direct_mesh_validation']='audits/native-right-shin-direct-mesh-validation.json'
print('Loaded native meshes',len(inputs),'physical items',len(parts),flush=True)
assert len(inputs)==64 and len(parts)==100+(len(assembly_scope['reference_names'])-1 if assembly_scope else 329)
managers={}
for label,meshes in [('source',source_meshes),('native',native_meshes)]:
 m=trimesh.collision.CollisionManager()
 for name,p in parts.items():m.add_object(name,meshes[p['mesh']])
 managers[label]=m
known_mates=[{'knee_motor','input_crank'}]+[{a,b} for a in ['knee_axle','knee_inner_spacer'] for b in ['bearing_inner','bearing_outer']]
def relevant(a,b,fixed=False):
 p,q=parts[a],parts[b]
 if '_port_' in a and '_port_' in b and a.rsplit('_',1)[0]==b.rsplit('_',1)[0]:return False
 if p.get('leg')==q.get('leg'):
  if not fixed and p['group']==q['group']:return False
  if p.get('leg') and {a.split('_',1)[1],b.split('_',1)[1]} in known_mates:return False
 return True
def collisions(q,fixed=False):
 hits={}
 for label,manager in managers.items():
  for name,p in parts.items():manager.set_transform(name,k.matrix(p,q))
  _,pairs=manager.in_collision_internal(return_names=True);hits[label]={tuple(sorted((a,b))) for a,b in pairs if relevant(a,b,fixed)}
 return hits
exact_cache={}
def solid(key,native):
 token=(key,native)
 if token not in shape_cache:
  if key in custom:path=ROOT/(inputs[key]['path'] if native else custom[key]['files']['step']['path'])
  else:path=ROOT/hardware[key]['path']
  shape_cache[token]=cq.importers.importStep(str(path)).val()
 return shape_cache[token]
def location(matrix):
 from OCP.gp import gp_Trsf
 tr=gp_Trsf();tr.SetValues(*matrix[:3,:].reshape(-1).tolist());return cq.Location(tr)
def exact_added(pair,q):
 a,b=pair;ma=k.matrix(parts[a],q);mb=k.matrix(parts[b],q);relative=np.linalg.inv(ma)@mb;token=(parts[a]['mesh'],parts[b]['mesh'],tuple(np.round(relative.flatten(),8)))
 if token not in exact_cache:
  overlaps={}
  for label,native in [('source',False),('native',True)]:
   one=solid(parts[a]['mesh'],native);two=solid(parts[b]['mesh'],native).located(location(relative));common=one.intersect(two);overlaps[label]=max(0,volume(common)[0]) if common.Solids() else 0
  exact_cache[token]=overlaps|{'added_penetration':overlaps['native']>overlaps['source']+.001 and overlaps['native']>.001}
 return {'pair':list(pair),**exact_cache[token]}
poses=dict(model['poses'])
for roll in [-45,0,45]:
 for hip in [0,30,65]:
  for knee in [-140,-90,-60]:poses[f'sample_{roll}_{hip}_{knee}']=k.uniform([roll,hip,knee])
assert len(poses)==35
rows=[];closure=[]
for name,q in poses.items():
 hits=collisions(q);added=hits['native']-hits['source'];proofs=[exact_added(pair,q) for pair in sorted(added)];rows.append({'pose':name,'angles':q,'source_contacts':[list(p) for p in sorted(hits['source'])],'native_contacts':[list(p) for p in sorted(hits['native'])],'added_mesh_contacts':[list(p) for p in sorted(added)],'exact_added_contact_checks':proofs,'added_solid_penetrations':[p for p in proofs if p['added_penetration']]})
 for leg,(_,side) in k.LEGS.items():
  frames=k.frames(leg,q[leg]);radius=k.P['crank_radius'];phase=np.deg2rad(k.P['crank_phase_deg']);y=side*70;upper=k.point(frames['crank'],[radius,y,0]);lower=k.point(frames['knee'],[radius*np.cos(phase),y,-radius*np.sin(phase)]);rod_top=k.point(frames['rod'],[0,y,0]);rod_bottom=k.point(frames['rod'],[0,y,-k.P['thigh']]);closure.append({'pose':name,'leg':leg,'eye_pin_error_mm':[float(np.linalg.norm(upper-rod_top)),float(np.linalg.norm(lower-rod_bottom))]})
 print('Pose',name,'source/native/additional solids',len(hits['source']),len(hits['native']),len(rows[-1]['added_solid_penetrations']),flush=True)
fixed_q=model['poses']['stand'];fixed=collisions(fixed_q,True);fixed_proofs=[exact_added(pair,fixed_q) for pair in sorted(fixed['native']-fixed['source'])]
knees=[]
for knee in range(-156,-47):
 q=k.uniform([0,30,knee]);hits=collisions(q);proofs=[exact_added(pair,q) for pair in sorted(hits['native']-hits['source'])];knees.append({'knee_deg':knee,'source_contact_count':len(hits['source']),'native_contact_count':len(hits['native']),'added_contact_checks':proofs,'added_solid_penetrations':[p for p in proofs if p['added_penetration']]})
 if knee%20==0:print('Knee',knee,flush=True)
# Sensor and cover removal retain all other physical robot parts.
hood={n for n in parts if n=='front_fascia' or n.startswith(('lidar','camera_','lens_','lens_ring_','iris_','sensor_window','depth_sensor'))};cradle={'body_nose_surround'}|{n for n in parts if n.startswith('sensor_hood_nut_')};cases=[('hood with sensors',hood,{n for n in parts if n.startswith('sensor_hood_screw_')}),('main cover with display',{'body_center_0','status_display'},{n for n in parts if n.startswith(('body_service_screw_','body_clamp_screw_'))}),('cradle after hood removal',cradle,hood|{n for n in parts if n.startswith(('sensor_hood_screw_','sensor_root_screw_','sensor_root_washer_'))})];service=[]
for label,moving,removed in cases:
 managers_service={}
 for variant,meshes in [('source',source_meshes),('native',native_meshes)]:
  manager=trimesh.collision.CollisionManager()
  for name,p in parts.items():
   if name not in moving|removed:manager.add_object(name,meshes[p['mesh']],transform=k.matrix(p,fixed_q))
  managers_service[variant]=manager
 for dz in [.2,1,3,5,10,20,40,80]:
  hits={}
  for variant,manager in managers_service.items():
   meshset=source_meshes if variant=='source' else native_meshes;found=set()
   for name in moving:
    transform=k.matrix(parts[name],fixed_q).copy();transform[2,3]+=dz;_,names=manager.in_collision_single(meshset[parts[name]['mesh']],transform=transform,return_names=True);found.update((name,n) for n in names)
   hits[variant]=found
  service.append({'operation':label,'upward_travel_mm':dz,'source_contacts':[list(p) for p in sorted(hits['source'])],'native_contacts':[list(p) for p in sorted(hits['native'])],'added_contacts':[list(p) for p in sorted(hits['native']-hits['source'])]})
report={'source_model_sha256':target['source_model_sha256'],'native_inputs':inputs,'custom_keys':64,'physical_items':len(parts),'assembly_scope':assembly_scope,'excluded_nonphysical':['electronics_clearance'],'motion_samples':rows,'fixed_stand':{'source_contacts':[list(p) for p in sorted(fixed['source'])],'native_contacts':[list(p) for p in sorted(fixed['native'])],'exact_added_contact_checks':fixed_proofs},'knee_samples':knees,'linkage_closure':closure,'sensor_service_samples':service,'passed':not any(r['added_solid_penetrations'] for r in rows+knees) and not any(r['added_penetration'] for r in fixed_proofs) and not any(r['added_contacts'] for r in service) and max(max(r['eye_pin_error_mm']) for r in closure)<1e-8,'elapsed_seconds':time.monotonic()-start,'scope':'Every native custom part substitutes into the frozen robot with all purchased references. Thirty-five named/grid poses and 109 knee samples compare added contacts; new mesh contacts receive exact-solid overlap checks. Existing source contacts remain listed. Sensor/cover removal uses 24 sampled heights. This does not prove continuous motion, cable flexibility, hand access, physical fit or structural strength.'};(ROOT/'audits/whole-native-robot-motion-service.json').write_text(json.dumps(report,indent=2));print(json.dumps({'passed':report['passed'],'seconds':report['elapsed_seconds'],'motion_samples':len(rows),'knee_samples':len(knees),'service_samples':len(service),'source_colliding_poses':sum(bool(r['source_contacts']) for r in rows),'added_solid_contacts':sum(len(r['added_solid_penetrations']) for r in rows+knees)+sum(r['added_penetration'] for r in fixed_proofs),'added_service_contacts':sum(len(r['added_contacts']) for r in service)}))
