"""Sample the assembled closed-thigh candidate, retaining hardware in the check."""
import hashlib
import json
import time
import numpy as np
import trimesh
from kinematics import ROOT, P, POSES, matrix, uniform, frames, point, LEGS

out=ROOT/'output/integrated-candidate'
raw=(out/'model.json').read_bytes();data=json.loads(raw);P.update(data['parameters'])
parts={p['name']:p for p in data['parts'] if p.get('service_role') not in ['keepout','withdrawal']}
meshes={k:trimesh.Trimesh(vertices=m['vertices'],faces=m['faces'],process=False) for k,m in data['meshes'].items()}
manager=trimesh.collision.CollisionManager()
for n,p in parts.items():manager.add_object(n,meshes[p['mesh']])
poses={**POSES}
for r in [-45,0,45]:
    for h in [0,30,65]:
        for k in [-140,-90,-60]:poses[f'sample_{r}_{h}_{k}']=uniform([r,h,k])
known_interfaces=[{'roll_motor','motor_carrier'},{'motor_carrier','roll_bearing'},{'hip_motor','hip_hub'},{'knee_motor','input_crank'}]
for b in ['bearing_inner','bearing_outer']:
    known_interfaces.extend([{'knee_axle',b},{'knee_inner_spacer',b}])
results=[];closure=[]
for name,q in poses.items():
    for n,p in parts.items():manager.set_transform(n,matrix(p,q))
    _,pairs=manager.in_collision_internal(return_names=True)
    hits=[]
    for a,b in pairs:
        pa,pb=parts[a],parts[b]
        if not pa.get('leg') and not pb.get('leg'):continue
        if pa['group'] in ['body','mount'] and pb['group'] in ['body','mount']:continue
        if pa.get('leg')==pb.get('leg'):
            ends={a.split('_',1)[-1],b.split('_',1)[-1]}
            if ends in known_interfaces:continue
            if pa['group']==pb['group'] and not (pa.get('service_role') or pb.get('service_role')):continue
            if '_port_' in a and '_port_' in b and a.rsplit('_',1)[0]==b.rsplit('_',1)[0]:continue
        hits.append(sorted([a,b]))
    results.append({'pose':name,'angles':q,'hits':sorted(hits),'passed':not hits})
    for leg,(_,side) in LEGS.items():
        f=frames(leg,q[leg]);phase=np.deg2rad(P['crank_phase_deg']);r=P['crank_radius'];yy=side*70
        upper=point(f['crank'],[r,yy,0]);lower=point(f['knee'],[r*np.cos(phase),yy,-r*np.sin(phase)])
        errors=[np.linalg.norm(upper-point(f['rod'],[0,yy,0])),np.linalg.norm(lower-point(f['rod'],[0,yy,-170]))]
        assert max(errors)<1e-8,(name,leg,errors)
        closure.append({'pose':name,'leg':leg,'eye_pin_error_mm':list(map(float,errors))})
    print(name,len(hits),flush=True)
# Dense knee sweep isolates internal linkage clearance from body range limits.
local = {n:p for n,p in parts.items() if p.get('leg')=='FL' and p['group'] in ['thigh','knee','rod','crank']}
local_manager=trimesh.collision.CollisionManager()
for n,p in local.items():local_manager.add_object(n,meshes[p['mesh']])
knee_sweep=[]
for knee in range(-156,-47):
    q=uniform([0,30,knee])
    for n,p in local.items():local_manager.set_transform(n,matrix(p,q))
    _,pairs=local_manager.in_collision_internal(return_names=True)
    hits=[]
    for a,b in pairs:
        if local[a]['group']==local[b]['group']:continue
        if {a.split('_',1)[-1],b.split('_',1)[-1]} in known_interfaces:continue
        hits.append(sorted([a,b]))
    knee_sweep.append({'knee_deg':knee,'hits':sorted(hits)})
print('DENSE KNEE SWEEP',sum(bool(r['hits']) for r in knee_sweep),'colliding samples',flush=True)
report={'knee_sweep':knee_sweep,'model_sha256':hashlib.sha256(raw).hexdigest(),'motion_samples':results,'linkage_closure':closure,
        'scope':'Sampled assembled rigid meshes, including modeled bolts, nuts and bearings regardless of earlier check flags. Same rigid group pairs, stationary body/frame pairs and explicitly listed mating interfaces are excluded. Fixed fits, service paths, tolerances, flexibility and strength require separate checks.',
        'excluded_mating_interfaces':[sorted(x) for x in known_interfaces]}
(out/'audit.json').write_text(json.dumps(report,indent=2))
print('AUDIT WRITTEN',flush=True)
