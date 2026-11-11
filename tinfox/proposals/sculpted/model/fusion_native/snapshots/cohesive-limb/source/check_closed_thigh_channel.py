"""Screen a wider internal rod channel before revising structural thigh parts."""
import json
import sys
import hashlib
import cadquery as cq
import numpy as np
import trimesh
from rounded_design import oval_loft
from kinematics import ROOT, P, matrix, uniform

OUT = ROOT / 'output/enclosure-review'
data = json.loads((ROOT / 'output/rounded-design/model.json').read_text())
parts = {p['name']: p for p in data['parts']}
def mesh(key):
    m = data['meshes'][key]
    return trimesh.Trimesh(vertices=m['vertices'], faces=m['faces'], process=False)
sections = [(-53,-.5,69,72,52),(-66,-2.5,69,66,51),(-92,-5,69,58,50),
            (-121,-5,69,52,50),(-144,-5,69,51,51),(-157,-5,69,55,52)]
large = '--large-cranks' in sys.argv
rear = '--rear-channel' in sys.argv or large
if rear:
    sections = [(-53,-.5,69,72,52),(-66,-8,69,48,40),(-92,-14,69,36,32),
                (-121,-16,69,32,30),(-144,-16,69,32,32),(-157,-12,69,42,40)]
prefix = 'rear-channel' if rear else 'wider-channel'
if large:
    sections = [(-53,-1.5,69,78,52),(-66,-11,69,60,40),(-92,-19,69,42,32),
                (-121,-22.25,69,35.5,30),(-144,-22.25,69,35.5,32),(-157,-15,69,52,40)]
    prefix = 'large-crank-channel'
    P['crank_radius'] = 28
outer = oval_loft(sections)
inner = oval_loft([(z+3 if z==-53 else z-3 if z==-157 else z,x,y,w-8,d-8) for z,x,y,w,d in sections])
wall = outer.cut(inner)
# The hip and knee joint regions need separate geometry. This experiment checks
# the middle web, where a closed wall currently intersects the rod.
wall = wall.intersect(cq.Workplane('XY').box(160,140,85).val().translate((0,69,-106.5)))
# Preserve the rotating knee head's joint mouth. It is an articulation opening,
# not a slot along the pushrod's middle travel.
wall = wall.cut(cq.Solid.makeCylinder(42 if large else 38,44,cq.Vector(0,49.5,-170),cq.Vector(0,1,0)))
assert wall.isValid() and len(wall.Solids()) == 1
cq.exporters.export(wall, str(OUT / (prefix + '-thigh-web.step')))
cq.exporters.export(wall, str(OUT / (prefix + '-thigh-web.stl')))
v,f=wall.tessellate(.08,.08)
obstacle = trimesh.collision.CollisionManager()
obstacle.add_object('closed_thigh_web',trimesh.Trimesh(vertices=[q.toTuple() for q in v],faces=f,process=False))
names=['FL_pushrod','FL_input_pin','FL_output_pin','FL_input_crank','FL_shin_inner','FL_shin_outer']
names += [n for n in parts if n.startswith('FL_rod_bush_')]
meshes={n:mesh(parts[n]['mesh']) for n in names}
if large:
    # Relocate the rod-end pins with their proposed longer crank arms. The
    # production crank arms and shin fork still require a separate redesign.
    meshes['FL_input_pin'].apply_translation([6,0,0])
    angle=np.deg2rad(P['crank_phase_deg'])
    meshes['FL_output_pin'].apply_translation([6*np.cos(angle),0,-6*np.sin(angle)])
    names.remove('FL_input_crank')
rows=[]
for knee in range(-156,-47):
    q=uniform([0,0,knee]);inverse=np.linalg.inv(matrix(parts['FL_thigh_inner'],q))
    hits=[];distances={}
    for n in names:
        transform=inverse@matrix(parts[n],q)
        if obstacle.in_collision_single(meshes[n],transform=transform):hits.append(n)
        distances[n]=float(obstacle.min_distance_single(meshes[n],transform=transform))
    rows.append({'knee_deg':knee,'hits':hits,'distance_mm':distances})
report={'sections_z_x_y_width_depth_mm':sections,'web_z_extent_mm':[-149,-64], 'crank_radius_mm':P['crank_radius'],
        'source_model_sha256':hashlib.sha256((ROOT/'output/rounded-design/model.json').read_bytes()).hexdigest(),
        'web_stl_sha256':hashlib.sha256((OUT/(prefix+'-thigh-web.stl')).read_bytes()).hexdigest(),
        'samples':rows,'scope':'Experimental closed middle web only. Hip and knee end closures are not modeled. '+('28 mm crank geometry is kinematic only: rod and pins relocated; longer input arm and relocated integral shin fork are not rebuilt or qualified. Original shin shells checked as obstacles.' if large else 'Existing rod, crank and pin geometry retained.')+' Rigid mesh distance; no tolerance, debris, deflection or strength allowance.'}
(OUT/(prefix+'-audit.json')).write_text(json.dumps(report,indent=2))
for n in names:
    hit=[r['knee_deg'] for r in rows if n in r['hits']]
    print(n,'collision samples',len(hit),'range',([min(hit),max(hit)] if hit else None),'minimum gap',round(min(r['distance_mm'][n] for r in rows),3),flush=True)
