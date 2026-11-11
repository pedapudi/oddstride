"""Reuse the closed-channel mesh to check the original V0 shin and linkage."""
import hashlib
import json
import numpy as np
import trimesh
from kinematics import ROOT, P, matrix, uniform

out = ROOT / 'output/enclosure-review'
source = ROOT / 'output/service-design/model.json'
raw = source.read_bytes()
data = json.loads(raw)
parts = {p['name']:p for p in data['parts']}
report = json.loads((out / 'large-crank-channel-audit.json').read_text())
P['crank_radius'] = report['crank_radius_mm']
manager = trimesh.collision.CollisionManager()
path = out / 'large-crank-channel-thigh-web.stl'
manager.add_object('web', trimesh.load(path))
names = ['FL_pushrod','FL_input_pin','FL_output_pin','FL_shin_inner','FL_shin_outer']
names += [n for n in parts if n.startswith('FL_rod_bush_')]
meshes = {}
for n in names:
    m = data['meshes'][parts[n]['mesh']]
    meshes[n] = trimesh.Trimesh(vertices=m['vertices'], faces=m['faces'], process=False)
delta = P['crank_radius'] - 22
angle = np.deg2rad(P['crank_phase_deg'])
meshes['FL_input_pin'].apply_translation([delta,0,0])
meshes['FL_output_pin'].apply_translation([delta*np.cos(angle),0,-delta*np.sin(angle)])
rows = []
for knee in range(-156,-47):
    q=uniform([0,0,knee]);inverse=np.linalg.inv(matrix(parts['FL_thigh_inner'],q))
    hits=[];distances={}
    for n in names:
        transform=inverse@matrix(parts[n],q)
        if manager.in_collision_single(meshes[n],transform=transform):hits.append(n)
        distances[n]=float(manager.min_distance_single(meshes[n],transform=transform))
    rows.append({'knee_deg':knee,'hits':hits,'distance_mm':distances})
report.update(samples=rows,source_model_sha256=hashlib.sha256(raw).hexdigest(),
              web_stl_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
report['scope'] = report['scope'].replace('Original shin shells','Original V0 shin shells')
(out/'large-crank-channel-v0-audit.json').write_text(json.dumps(report,indent=2))
for name in names:
    print(name,'collision samples',sum(name in r['hits'] for r in rows),
          'minimum gap',round(min(r['distance_mm'][name] for r in rows),3))
