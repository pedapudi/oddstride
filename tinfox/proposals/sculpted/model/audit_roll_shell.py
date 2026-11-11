"""Separate rigid body clearance from collisions between legs during hip roll."""
import json,hashlib
import numpy as np
import trimesh
from kinematics import ROOT,POSES,LEGS,matrix
out=ROOT/'output';data=json.loads((out/'model.json').read_text())
body=trimesh.collision.CollisionManager()
def mesh(p):
 m=data['meshes'][p['mesh']];return trimesh.Trimesh(vertices=m['vertices'],faces=m['faces'],process=False)
shell=[p for p in data['parts'] if not p['leg'] and p['check'] and p['material']=='petg']
for p in shell:body.add_object(p['name'],mesh(p))
rows=[]
for leg in LEGS:
 for name in ['stand','studio','raised','crouch','fold','side_reach','reach']:
  poses={l:list(q) for l,q in POSES[name].items()};poses[leg][0]=0
  pieces=[]
  for p in data['parts']:
   if p['leg']!=leg or p['group']=='mount' or not p['check']:continue
   m=mesh(p);m.apply_transform(matrix(p,poses));pieces.append(m)
  combined=trimesh.util.concatenate(pieces)
  moving=trimesh.collision.CollisionManager();moving.add_object(leg,combined)
  representative=next(p for p in data['parts'] if p['leg']==leg and p['group']=='roll')
  origin=matrix(representative,poses);min_gap=float('inf');bad=[]
  for angle in range(-60,61):
   poses[leg][0]=angle;tf=matrix(representative,poses)@np.linalg.inv(origin)
   moving.set_transform(leg,tf)
   gap=body.min_distance_other(moving)
   if gap<min_gap:min_gap=float(gap);at=angle
   if body.in_collision_other(moving):bad.append(angle)
  clear=[a for a in range(-60,61) if a not in bad]
  intervals=[]
  for a in clear:
   if not intervals or a>intervals[-1][1]+1:intervals.append([a,a])
   else:intervals[-1][1]=a
  rows.append({'clear_intervals_deg':intervals,'leg':leg,'pitch_family':name,'roll_deg':[-60,60],'minimum_gap_mm':min_gap,'closest_roll_deg':at,'collision_angles_deg':bad})
  print(leg,name,round(min_gap,3),bad,flush=True)
report={'model_sha256':hashlib.sha256((out/'model.json').read_bytes()).hexdigest(),'shell_parts':[p['name'] for p in shell],'sample_count':len(rows)*121,'families':rows,'scope':'One-degree roll samples for seven fixed hip/knee configurations per leg against fixed printed body parts. Excludes inter-leg contact, fixed motor interfaces, tolerances and deformation. Full-robot motion remains separately checked.','provisional_gaiter_count':sum(p['material']=='fabric' for p in data['parts'])}
(out/'roll-shell-audit.json').write_text(json.dumps(report,indent=2))
assert report['provisional_gaiter_count']==0
assert not any(row['collision_angles_deg'] for row in rows if row['pitch_family'] in ['stand','raised','side_reach'])
print('Standing, raised and coordinated-side families clear through ±60 degrees. Crouched/folded roll limits are recorded; full joint-limit combinations are not clear.')
