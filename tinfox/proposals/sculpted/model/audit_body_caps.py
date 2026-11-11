"""Check the end bridges against fixed interfaces and their service paths."""
import json,hashlib
import cadquery as cq
import trimesh
from kinematics import ROOT, matrix, POSES
out=ROOT/'output/service-design';raw=(out/'model.json').read_bytes();data=json.loads(raw)
parts={p['name']:p for p in data['parts']};cache={}
def solid(key):
 if key not in cache:
  path=out/'step'/f'{key}.step'
  if not path.exists():path=ROOT/'output/step-parts'/f'{key}.step'
  cache[key]=cq.importers.importStep(str(path)).val()
 return cache[key]
checks=[]
pairs=[('body_nose_surround','chassis_crossmember_121'),('body_nose_surround','front_fascia'),('body_nose_surround','sensor_bezel'),('body_nose_surround','lidar_base'),('body_nose_surround','lidar')]
for front in [1]:
 cap='body_nose_surround' if front>0 else 'body_aft_0'
 for yy in [-18,18]:
  pairs.extend([(f'end_cap_nut_{front}_{yy}',cap),(f'end_cap_nut_{front}_{yy}',f'chassis_crossmember_{front*121}')])
for a,b in pairs:
 v=max(0,solid(a).intersect(solid(b)).Volume());assert v<1e-3,(a,b,v)
 checks.append({'parts':[a,b],'overlap_mm3':v})
# Roof contact is intentional at each cap's broad mounting lap.
sections=[]
from build import box
for key,sign in [('body_nose_surround',1)]:
 s=solid(key);bb=s.BoundingBox();samples=[]
 for x in range(132,221,8):
  section=s.intersect(box(1,280,150,(sign*x,0,40)))
  samples.append({'x_mm':sign*x,'area_approx_mm2':section.Volume()})
 sections.append({'part':key,'solid_count':len(s.Solids()),'valid':s.isValid(),'crown_height_mm':bb.zmax,'mass_g':parts[key]['mass_kg']*1000,'cross_sections':samples})
# A service sequence, not a swept-volume guarantee: remove the main cover,
# disconnect the harness, remove two cap screws, then lift the entire end module.
meshes={k:trimesh.Trimesh(vertices=m['vertices'],faces=m['faces'],process=False) for k,m in data['meshes'].items()}
obstacles=trimesh.collision.CollisionManager()
head_names={'body_nose_surround','front_fascia','sensor_bezel','sensor_window','depth_sensor'}
head_names.update(n for n in parts if n.startswith(('front_fascia_screw_','camera_','lens_','iris_')))
removed={'body_center_0','body_aft_0'}|head_names
for n,p in parts.items():
 if n in removed or n.startswith(('end_cap_screw_','end_cap_nut_')) or p.get('service_role') in ['keepout','withdrawal']:continue
 if not p['check'] and not p.get('service_role'):continue
 obstacles.add_object(n,meshes[p['mesh']],transform=matrix(p,POSES['stand']))
paths=[]
for key in ['body_nose_surround']:
 samples=[]
 for distance in [1,3,8,15,30,50,80,120]:
  transform=trimesh.transformations.translation_matrix([0,0,distance])
  module=trimesh.util.concatenate([meshes[parts[n]['mesh']] for n in head_names]) if key=='body_nose_surround' else meshes[parts[key]['mesh']]
  _,hits=obstacles.in_collision_single(module,transform=transform,return_names=True)
  samples.append({'lift_mm':distance,'hits':sorted(hits)})
 assert all(not q['hits'] for q in samples),(key,samples)
 paths.append({'part':key,'samples':samples,'passed':True,'sequence':'Remove upper body cover, disconnect wiring, remove two cap screws and lift. The front check includes the attached fascia, bezel and camera envelopes.'})
report={'model_sha256':hashlib.sha256(raw).hexdigest(),'fixed_interface_checks':checks,'sections':sections,'service_paths':paths,'limitations':'Nominal geometry. No strength, creep or impact qualification. Surface contact at the mounting laps and fascia locating edges is intentional. Print support and finish require slicer review.'}
(out/'body-cap-audit.json').write_text(json.dumps(report,indent=2));print('Body bridge interfaces and sampled lift paths passed.',flush=True)
