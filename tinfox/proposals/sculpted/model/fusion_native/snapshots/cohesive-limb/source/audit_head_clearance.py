"""Sample the equipment head and neck against both complete front legs."""
import hashlib,itertools,json,sys
from pathlib import Path
import numpy as np
import trimesh
from kinematics import ROOT,P,frames
OUT=ROOT/'output'/(sys.argv[1] if len(sys.argv)>1 else 'raised-head-prototype')
raw=(OUT/'model.json').read_bytes();model=json.loads(raw);P.update(model['parameters'])
meshes={k:trimesh.Trimesh(vertices=q['vertices'],faces=q['faces'],process=False) for k,q in model['meshes'].items()}
parts=model['parts'];moving=[p for p in parts if p.get('leg') in ['FL','FR'] and p.get('service_role') not in ['withdrawal']]
limbs=trimesh.collision.CollisionManager();reserved=trimesh.collision.CollisionManager()
for p in moving:(reserved if p.get('service_role')=='keepout' else limbs).add_object(p['name'],meshes[p['mesh']])
groups={name:trimesh.collision.CollisionManager() for name in ['head','neck']+(['mounting'] if any(p['name'].startswith('head_bridge') for p in parts) else [])}
for p in parts:
 n=p['name']
 if n.startswith('head_bridge'):groups['mounting'].add_object(n,meshes[p['mesh']])
 elif n.startswith(('equipment_head','head_','lidar')):groups['head'].add_object(n,meshes[p['mesh']])
 elif n.startswith('neck_'):groups['neck'].add_object(n,meshes[p['mesh']])
rows=[];minima={k:{'distance_mm':1e9} for k in groups};count=0
rolls=list(range(-60,61,5));pitches=list(range(-35,86,10))+[90];knees=[-156,-100,-48]
for q in itertools.product(rolls,pitches,knees):
 fs={leg:frames(leg,q) for leg in ['FL','FR']}
 for p in moving:(reserved if p.get('service_role')=='keepout' else limbs).set_transform(p['name'],fs[p['leg']][p['group']])
 count+=1
 for kind,target in groups.items():
  hit,pairs=limbs.in_collision_other(target,return_names=True)
  reservation_hit,reservation_pairs=reserved.in_collision_other(target,return_names=True)
  if hit or reservation_hit:rows.append({'angles_deg':q,'group':kind,'hits':sorted([sorted(t) for t in pairs]),'connector_keepout_hits':sorted([sorted(t) for t in reservation_pairs])})
  distance,names=limbs.min_distance_other(target,return_names=True)
  if distance<minima[kind]['distance_mm']:minima[kind]={'distance_mm':distance,'pair':names,'angles_deg':q}
report={'model_sha256':hashlib.sha256(raw).hexdigest(),'pose_count':count,'roll_deg':rolls,'hip_pitch_deg':pitches,'knee_pitch_deg':knees,'minimum_sampled_gaps':minima,'collision_samples':rows,'scope':'Both complete front legs, including modeled motor housings, carriers, fasteners, sockets, plugs, boots and static cable envelopes. Connector keepouts checked separately; withdrawal/service envelopes excluded. Grid samples do not certify continuous motion, tolerances, structural deflection or cable flex. Unrelated chassis/leg collisions are outside this targeted audit.'}
(OUT/'head-clearance.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'pose_count':count,'minima':minima,'collision_count':len(rows),'examples':rows[:3]},indent=2),flush=True)
