"""Check every modeled front-limb component against the fixed body and frame."""
import hashlib
import json
import time
import sys

import numpy as np
import trimesh
from kinematics import ROOT, P, POSES, matrix, uniform

def inspect(folder):
    start = time.perf_counter()
    out = ROOT / 'output' / folder
    raw = (out / 'model.json').read_bytes()
    data = json.loads(raw)
    P.update(data['parameters'])
    parts = {p['name']: p for p in data['parts']
             if p.get('service_role') not in ['keepout','withdrawal']}
    meshes = {}
    for p in parts.values():
        key = p['mesh']
        if key not in meshes:
            m = data['meshes'][key]
            meshes[key] = trimesh.Trimesh(vertices=m['vertices'], faces=m['faces'], process=False)
    fixed = {n:p for n,p in parts.items() if not p.get('leg') or p['group']=='mount'}
    moving = {n:p for n,p in parts.items() if p.get('leg') in ['FL','FR'] and p['group'] in ['thigh','knee','rod','crank']}
    # No check-flag, fastener, bearing, pin or axle exclusions apply here.
    body = trimesh.collision.CollisionManager()
    limbs = trimesh.collision.CollisionManager()
    knee_hardware = trimesh.collision.CollisionManager()
    hardware = {n:p for n,p in moving.items() if n.split('_',1)[1] in {
        'knee_axle','axle_bolt','axle_nut','knee_inner_spacer','bearing_inner',
        'bearing_outer','output_pin','output_pivot_nut','shin_clamp_sleeve_37',
        'shin_clamp_bolt_37','shin_clamp_nut_37','shin_clamp_sleeve_105',
        'shin_clamp_bolt_105','shin_clamp_nut_105'} or n.startswith(('FL_rod_bush_output','FR_rod_bush_output'))}
    for n,p in fixed.items(): body.add_object(n,meshes[p['mesh']],transform=matrix(p,POSES['stand']))
    for n,p in moving.items(): limbs.add_object(n,meshes[p['mesh']])
    for n,p in hardware.items(): knee_hardware.add_object(n,meshes[p['mesh']])
    def check(q, distance=False):
        for n,p in moving.items():
            transform=matrix(p,q);limbs.set_transform(n,transform)
            if n in hardware:knee_hardware.set_transform(n,transform)
        _, pairs=limbs.in_collision_other(body,return_names=True)
        row={'hits':sorted([list(pair) for pair in pairs]),
             'knee_hardware_hits':sorted([list(pair) for pair in pairs if pair[0] in hardware])}
        if distance:
            gap,names=knee_hardware.min_distance_other(body,return_names=True)
            row.update(knee_hardware_gap_mm=float(gap),nearest_knee_hardware_pair=list(names))
        return row
    named=[]
    for name,q in POSES.items():
        row={'pose':name,'angles':q,**check(q,True)};named.append(row)
        print(folder,name,'pairs',len(row['hits']),'knee',row['knee_hardware_hits'],
              'gap',round(row['knee_hardware_gap_mm'],3),row['nearest_knee_hardware_pair'],flush=True)
    sampled=[]
    prior=json.loads((out/'audit.json').read_text())
    for sample in prior['motion_samples']:
        sampled.append({'pose':sample['pose'],'angles':sample['angles'],**check(sample['angles'],True)})
    sweeps={}
    for name,axis,values,base in [
        ('hip_pitch_knee_60',1,range(-90,201),[0,30,-60]),
        ('hip_pitch_knee_130',1,range(-90,201),[0,30,-130]),
        ('hip_roll_stand',0,range(-60,61),[0,30,-60])]:
        rows=[]
        for angle in values:
            q=list(base);q[axis]=angle
            rows.append({'angle_deg':angle,**check(uniform(q))})
        sweeps[name]={'fixed_angles_roll_hip_knee_deg':base,'axis_index':axis,'step_deg':1,'samples':rows}
        print(folder,name,'colliding',sum(bool(r['hits']) for r in rows),
              'hardware_colliding',sum(bool(r['knee_hardware_hits']) for r in rows),flush=True)
    report={'model_sha256':hashlib.sha256(raw).hexdigest(),'moving_components':list(moving),
            'fixed_components':list(fixed),'knee_hardware_components':list(hardware),
            'named_poses':named,'prior_sample_poses':sampled,'sweeps':sweeps,
            'elapsed_seconds':time.perf_counter()-start,
            'scope':'All modeled front thigh, crank, rod and shin components versus the complete fixed body/frame, including modeled fasteners and purchased-part envelopes regardless of prior check flags. Fixed roll motors and cartridges are obstacles. Hip-roll carriers are outside this targeted check. Rigid triangle meshes at sampled positions; no continuous-motion, tolerance, cable-flex, ground or loaded-deflection qualification. Each model uses its own crank radius and geometry.'}
    (out/'front-body-audit.json').write_text(json.dumps(report,indent=2))
    print(folder,'DONE',round(report['elapsed_seconds'],2),flush=True)

if __name__=='__main__':
    for folder in (sys.argv[1:] or ['v0-rounded-body','rounded-design']):inspect(folder)
