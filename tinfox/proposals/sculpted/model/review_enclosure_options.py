"""Check a rounded cover on V0 and the pushrod inside a closed thigh web."""
import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh
import cadquery as cq

from kinematics import ROOT, P, matrix, uniform
from rounded_design import oval_loft

OUT = ROOT / 'output/enclosure-review'
OUT.mkdir(exist_ok=True)

def read(folder):
    raw = (ROOT / 'output' / folder / 'model.json').read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()

def mesh(data, key):
    m = data['meshes'][key]
    return trimesh.Trimesh(vertices=m['vertices'], faces=m['faces'], process=False)

v0, h0 = read('service-design')
rounded, hr = read('rounded-design')
poses = json.loads((ROOT / 'output/rounded-design/audit.json').read_text())['motion_samples']
cover = mesh(rounded, 'body_center_0')
manager = trimesh.collision.CollisionManager()
parts = {}
for p in v0['parts']:
    if p['name'] == 'body_center_0' or p.get('service_role') in ['keepout', 'withdrawal']:
        continue
    # Fixed electronics and frame are included, even if motion audits omit them.
    parts[p['name']] = p
    manager.add_object(p['name'], mesh(v0, p['mesh']))
cover_checks = []
for pose in poses:
    for name, p in parts.items():
        manager.set_transform(name, matrix(p, pose['angles']))
    _, hits = manager.in_collision_single(cover, return_names=True)
    cover_checks.append({'pose': pose['pose'], 'intersections': sorted(hits)})

# Reconstruct only the middle oval wall before the clearance cuts used in V1.
# This is a specific closure proposal, not a claim about every possible shell.
sections = [(-53,-.5,69,72,52),(-66,-.5,69,62,51),(-92,-1,69,50,50),
            (-121,-1,69,44,50),(-144,-1,69,43,51),(-157,0,69,45,52)]
outer = oval_loft(sections)
inner = oval_loft([(-50,-.5,69,64,44),(-66,-.5,69,54,43),(-92,-1,69,42,42),
                  (-121,-1,69,36,42),(-144,-1,69,35,43),(-160,0,69,37,44)])
closed = outer.cut(inner)
verts, faces = closed.tessellate(.08, .08)
closed_mesh = trimesh.Trimesh(vertices=[v.toTuple() for v in verts], faces=faces, process=False)
cq.exporters.export(closed, str(OUT / 'uncut-thigh-web.step'))
closed_mesh.export(OUT / 'uncut-thigh-web.stl')

rod_checks = {}
all_vertices = []
for design, data in [('v0', v0), ('rounded', rounded)]:
    byname = {p['name']: p for p in data['parts']}
    moving = ['FL_pushrod','FL_input_pin','FL_output_pin', 'FL_input_crank']
    moving += [n for n in byname if n.startswith('FL_rod_bush_')]
    obstacles = trimesh.collision.CollisionManager()
    for side in ['inner', 'outer']:
        obstacles.add_object(side, mesh(data, 'thigh_' + side))
    hypothetical = trimesh.collision.CollisionManager()
    hypothetical.add_object('uncut_oval_wall', closed_mesh)
    samples = []
    for knee in range(-156, -47):
        q = uniform([0, 0, knee])
        inverse = np.linalg.inv(matrix(byname['FL_thigh_inner'], q))
        actual_hits, closed_hits = [], []
        for name in moving:
            p = byname[name]
            transform = inverse @ matrix(p, q)
            part_mesh = mesh(data, p['mesh'])
            _, names = obstacles.in_collision_single(part_mesh, transform=transform, return_names=True)
            actual_hits.extend([[name, x] for x in sorted(names)])
            _, names = hypothetical.in_collision_single(part_mesh, transform=transform, return_names=True)
            closed_hits.extend([[name, x] for x in sorted(names)])
            if design == 'v0' and name == 'FL_pushrod':
                all_vertices.extend(trimesh.transform_points(part_mesh.vertices, transform))
        samples.append({'knee_deg': knee, 'existing_shell_hits': actual_hits, 'uncut_oval_wall_hits': closed_hits})
    rod_checks[design] = samples
sweep = trimesh.convex.convex_hull(np.array(all_vertices))
sweep.export(OUT / 'pushrod-sweep.stl')
report = {'source_hashes': {'v0':h0,'rounded':hr}, 'rounded_cover_on_v0':cover_checks,
          'rod_sweep_bounds_in_thigh_mm':sweep.bounds.tolist(), 'pushrod_checks':rod_checks,
          'scope':'Rigid triangle-mesh intersections. Cover checked at 35 poses against fixed parts and moving parts. Rod, bushes, pins and input crank checked against both thigh halves at 109 knee angles. The uncut oval wall is a hypothetical closure of the rounded middle web. No strength, deflection, tolerance or continuous swept-clearance qualification.'}
(OUT / 'audit.json').write_text(json.dumps(report, indent=2))
print('Cover checks:', cover_checks, flush=True)
for design, rows in rod_checks.items():
    print(design, 'existing hits', sum(bool(r['existing_shell_hits']) for r in rows),
          'uncut wall hits',sum(bool(r['uncut_oval_wall_hits']) for r in rows),flush=True)
print('Rod bounds:', sweep.bounds.tolist(), flush=True)
