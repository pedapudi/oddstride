"""Check actual frame seating, tool corridors and changed enclosure interfaces."""
import hashlib,json,sys
from pathlib import Path
from functools import cache
import numpy as np
import trimesh
import cadquery as cq
import cohesive_chassis as design
import build as b
from kinematics import ROOT,P,matrix,uniform

OUT=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'output/cohesive-chassis-work'
raw=(OUT/'model.json').read_bytes();data=json.loads(raw)
P.update(data['parameters']);parts={p['name']:p for p in data['parts'] if p.get('service_role') not in ['keepout','withdrawal']}
old=json.loads((design.BASE/'model.json').read_text());q=uniform([0,30,-60]);rows=[]
@cache
def solid(key):
    path=OUT/'step'/(key+'.step')
    return cq.importers.importStep(str(path)).val() if path.exists() else design.source(key)

def meshes(model):
    result={}
    for p in model['parts']:
        if p.get('service_role') in ['keepout','withdrawal']:continue
        m=model['meshes'][p['mesh']];s=trimesh.Trimesh(m['vertices'],m['faces'],process=False)
        s.apply_transform(matrix(p,q));result[p['name']]=s
    return result
new_meshes,old_meshes=meshes(data),meshes(old)
changed=['body_center_0','belly_center_0','chassis_beam_-102','chassis_beam_102','chassis_crossmember_-121','chassis_crossmember_121']
def static_pairs(meshes):
    manager=trimesh.collision.CollisionManager()
    for key,m in meshes.items():manager.add_object(key,m)
    pairs=set()
    for key in changed:
        _,names=manager.in_collision_single(meshes[key],return_names=True)
        for name in names:
            if name!=key:pairs.add(tuple(sorted([key,name])))
    return pairs
before,after=static_pairs(old_meshes),static_pairs(new_meshes)
added=sorted(after-before)

# A thread cylinder overlaps its tapped receiving body by design. The
# references represent outside thread envelopes, not helical material cuts.
expected=[];unexpected=[]
for a,c in added:
    screw=next((n for n in [a,c] if n.startswith(('chassis_tie_bolt_','body_service_screw_','sensor_root_screw_'))),None)
    other=c if screw==a else a
    if screw and other.startswith('chassis_beam_'):expected.append([a,c])
    elif screw and screw.startswith('sensor_root_screw_') and other=='chassis_crossmember_121':expected.append([a,c])
    elif screw and other=='body_center_0':
        p=parts[screw];s=cq.importers.importStep(str(OUT/'step'/(p['mesh']+'.step'))).val()
        overlap=solid('body_center_0').intersect(s).Volume()
        if overlap<.001:expected.append([a,c])
        else:unexpected.append([a,c])
    else:unexpected.append([a,c])

for front in [-1,1]:
    tie=solid('chassis_crossmember_'+str(front*121))
    for side in [-1,1]:
        rail=solid('chassis_beam_'+str(side*102))
        for dx in [-3,3]:
            x=design.FRAME_PAD_X*front+dx;y=side*104
            # Full 6 mm nominal engaged length has a complete supporting
            # annulus. This is geometric engagement, not thread strength.
            annulus=b.cyl(2.8,6,(x,y,28),(0,0,1)).cut(b.cyl(1.501,8,(x,y,27),(0,0,1)))
            fraction=rail.intersect(annulus).Volume()/annulus.Volume()
            overlap=rail.intersect(tie).Volume()
            rows.append({'interface':'M3 tie screw seat and tapped pad','front':front,'side':side,'dx':dx,
                'nominal_engagement_mm':6,'annular_support_fraction':fraction,'pad_tie_overlap_mm3':overlap,
                'head_under_cone_z_mm':34.7,'tie_countersink_start_z_mm':34.7,
                'passed':fraction>.999 and overlap<.001})
for y in [-24,24]:
    pad=b.cyl(3.5,6.8,(121,y,34),(0,0,1)).cut(b.cyl(2.001,9,(121,y,33),(0,0,1)))
    fraction=solid('chassis_crossmember_121').intersect(pad).Volume()/pad.Volume()
    rows.append({'interface':'M4 sensor root tapped boss','y_mm':y,'nominal_engagement_mm':6.8,
        'annular_support_fraction':fraction,'passed':fraction>.999})

manager=trimesh.collision.CollisionManager()
for name,m in new_meshes.items():
    if name.startswith(('body_center_0','body_service_screw_','chassis_tie_bolt_')):continue
    manager.add_object(name,m)
def mesh(shape):
    vv,ff=shape.tessellate(.08,.1)
    return trimesh.Trimesh([p.toTuple() for p in vv],ff,process=False)
for front in [-1,1]:
    for side in [-1,1]:
        for dx in [-3,3]:
            x=front*design.FRAME_PAD_X+dx;y=side*104
            tool=mesh(b.cyl(2.5,60,(x,y,36.1),(0,0,1)))
            _,names=manager.in_collision_single(tool,return_names=True)
            rows.append({'interface':'top-down tie screw driver','x_mm':x,'y_mm':y,'tool_radius_mm':2.5,
                'travel_mm':60,'obstacles':sorted(names),'passed':not names})
for x in [-64,64]:
    for side in [-1,1]:
        tool=mesh(b.cyl(3.5,70,(x,side*114.3,18),(0,side,0)))
        _,names=manager.in_collision_single(tool,return_names=True)
        rows.append({'interface':'lateral cover screw driver','x_mm':x,'side':side,
            'tool_radius_mm':3.5,'travel_mm':70,'obstacles':sorted(names),'passed':not names})

report={'model_sha256':hashlib.sha256(raw).hexdigest(),'checks':rows,'new_static_pairs':added,
    'expected_thread_or_seating_contacts':expected,'unexpected_new_static_pairs':unexpected,
    'inherited_static_pairs':sorted(before&after),'passed':all(r['passed'] for r in rows) and not unexpected,
    'scope':'Geometric thread support and straight driver access with upper cover removed, robot standing. Static contacts compared against the previous model without the viewer body/mount exclusion. Intended thread-envelope contacts are listed separately. No preload, thread stripping, material strength, flexible-wire or hand-access qualification.'}
(OUT/'chassis-assembly.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
