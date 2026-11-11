"""Compare native Head interfaces and sampled removal paths with the frozen V0."""
import gzip,hashlib,json,sys
from pathlib import Path
import cadquery as cq
import trimesh
ROOT=Path(__file__).resolve().parents[1];MODEL=ROOT.parent;sys.path.insert(0,str(MODEL))
from kinematics import matrix,POSES
from audit_part import volume
raw=gzip.decompress((ROOT/'snapshots/reference-model.json.gz').read_bytes());data=json.loads(raw);parts={p['name']:p for p in data['parts']}
labels={'body_nose_surround':'body_nose_surround-tangent','front_fascia':'front_fascia-intent','sensor_bezel':'sensor_bezel-intent'};cache={}
def solid(key,native=False):
 token=(key,native)
 if token not in cache:
  path=ROOT/'exports'/f'{labels[key]}.step' if native and key in labels else ROOT/'snapshots/step'/f'{key}.step'
  if not path.exists():path=MODEL/'output/service-design/step'/f'{key}.step'
  assert path.exists(),path;cache[token]=cq.importers.importStep(str(path)).val()
 return cache[token]
pairs=[('body_nose_surround',n) for n in ['chassis_crossmember_121','front_fascia','sensor_bezel','lidar_base','lidar']]+[('front_fascia','sensor_bezel')]
for y in [-18,18]:pairs.extend([(f'end_cap_nut_1_{y}','body_nose_surround'),(f'end_cap_nut_1_{y}','chassis_crossmember_121')])
checks=[]
for a,b in pairs:
 values=[max(0,volume(solid(a,native).intersect(solid(b,native)))[0]) for native in [False,True]]
 checks.append({'parts':[a,b],'source_overlap_mm3':values[0],'native_overlap_mm3':values[1],'source_has_interference':values[0]>.001,'translation_added_overlap_mm3':values[1]-values[0],'translation_fit_passed':values[1]<.001 if values[0]<.001 else values[1]<=values[0]+1})
 print(checks[-1],flush=True)
meshes={k:trimesh.Trimesh(vertices=m['vertices'],faces=m['faces'],process=False) for k,m in data['meshes'].items()};head={'body_nose_surround','front_fascia','sensor_bezel','sensor_window','depth_sensor'}|{n for n in parts if n.startswith(('front_fascia_screw_','camera_','lens_','iris_'))};obstacles=trimesh.collision.CollisionManager()
for n,p in parts.items():
 if n in head|{'body_center_0','body_aft_0'} or n.startswith(('end_cap_screw_','end_cap_nut_')) or p.get('service_role') in ['keepout','withdrawal']:continue
 if not p['check'] and not p.get('service_role'):continue
 obstacles.add_object(n,meshes[p['mesh']],transform=matrix(p,POSES['stand']))
modules={}
for native in [False,True]:
 mm=[]
 for name in head:
  if native and name in labels:
   v,f=solid(name,True).tessellate(.02,.05);mm.append(trimesh.Trimesh(vertices=[p.toTuple() for p in v],faces=f,process=False))
  else:mm.append(meshes[parts[name]['mesh']])
 modules[native]=trimesh.util.concatenate(mm)
paths=[]
for distance in [1,3,8,15,30,50,80,120]:
 hits={}
 for native in [False,True]:
  _,names=obstacles.in_collision_single(modules[native],transform=trimesh.transformations.translation_matrix([0,0,distance]),return_names=True);hits['native' if native else 'source']=sorted(names)
 paths.append({'lift_mm':distance,**hits,'no_new_collisions':set(hits['native'])<=set(hits['source'])})
record={'reference_model_sha256':hashlib.sha256(raw).hexdigest(),'native_exports':{n:{'file':v+'.step','sha256':hashlib.sha256((ROOT/'exports'/f'{v}.step').read_bytes()).hexdigest()} for n,v in labels.items()},'fixed_interfaces':checks,'removal_path':paths,'translation_gate_passed':all(r['translation_fit_passed'] for r in checks) and all(r['no_new_collisions'] for r in paths),'manufacturing_ready':False,'known_source_defect':'The frozen fascia and bezel overlap. Translation fidelity does not authorize fabrication.','service_sequence':'Remove upper shell and two cap screws, disconnect harness, lift complete front sensor module. Eight sampled positions, not swept-volume proof.'};(ROOT/'audits/head-interface-service.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
