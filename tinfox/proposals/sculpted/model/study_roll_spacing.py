"""Current-robot bearing reactions with actuator-compatible and impact cases.

This is a load screen, not gait simulation, bearing-life or structure validation.
The future 20 kg payload platform is deliberately excluded.
"""
import hashlib,json,math
from pathlib import Path
import numpy as np
from kinematics import ROOT,P,frames,point,contacts,rotation

SOURCE=ROOT/'output/paired-roll-work/model.json'
raw=SOURCE.read_bytes();data=json.loads(raw);P.clear();P.update(data['parameters'])
mass=json.loads((SOURCE.parent/'torques.json').read_text())['mass']['base_kg']
groups={}
for p in data['parts']:
    if p['leg']!='FL' or p['group']=='mount' or p['mass_kg']<=0:continue
    g=groups.setdefault(p['group'],[0.,np.zeros(3)])
    g[0]+=p['mass_kg'];g[1]+=p['mass_kg']*np.array(p['com_mm'])
groups={name:(m,c/m) for name,(m,c) in groups.items()}
ratings={'Lily 6810-2RS':5764.99,'Koyo 6810 2RS':6100.0}
spacings=[7,8,9,10,12,14]
cases=[
    ('loaded_four_foot_hold',mass+1,.25,1,6,False),
    ('loaded_three_foot_walk',mass+1,1/3,1,17,False),
    ('loaded_stairs_60_percent',mass+1,.6,1,17,False),
    ('loaded_one_foot_screen',mass+1,1,1,17,False),
    ('unloaded_two_foot_trot',mass,.5,1.8,17,False),
    ('unloaded_push_off',mass,.5,2.5,17,False),
    ('unloaded_landing_nominal',mass,.5,3,17,True),
]

def centers(q):
    f=frames('FL',q)
    return {g:point(f[g],c)/1000 for g,(_,c) in groups.items()}
def grav(q):
    c=centers(q);out=[];eps=1e-4
    for j in range(3):
        a=list(q);z=list(q);a[j]+=math.degrees(eps);z[j]-=math.degrees(eps)
        ca,cz=centers(a),centers(z)
        out.append(sum(m*9.81*(ca[g][2]-cz[g][2])/(2*eps) for g,(m,_) in groups.items()))
    return c,np.array(out)

poses=[]
for roll in [-25,0,25]:
    for hip in [-15,0,15,30,45,60,75]:
        for knee in [-140,-125,-110,-95,-80,-65,-50]:poses.append([roll,hip,knee])
summaries={name:{'accepted':0,'rejected_by_motor_torque':0,'spacing':{str(s):{'max_reaction_N':0,'worst':None} for s in spacings}} for name,*_ in cases}
for i,q in enumerate(poses):
    com,G=grav(q);foot,origins,axes=contacts('FL',q)
    J=np.column_stack([np.cross(a,(foot-o)/1000) for a,o in zip(axes,origins)])
    for name,m,share,factor,limit,impact in cases:
        if impact:continue
        fz=m*9.81*share*factor
        for a in [None,*range(0,360,45)]:
            direction=np.array([0,0,1.]) if a is None else np.array([.4*math.cos(math.radians(a)),.4*math.sin(math.radians(a)),1])
            force=direction*fz;motor=np.abs(factor*G-J.T@force)/[1,1,P['knee_efficiency_assumption']]
            record=summaries[name]
            if np.max(motor)>limit+1e-8:record['rejected_by_motor_torque']+=1;continue
            record['accepted']+=1
            for s in spacings:
                # Preserve the front bearing face and move the rear support
                # forward as spacing decreases. This releases motor-side room.
                center=np.array([P['hip_x']-54-s/2,P['roll_y'],0])/1000
                F=force.copy();M=np.cross(foot/1000-center,force)
                for g,(gm,_) in groups.items():
                    fg=np.array([0,0,-gm*9.81*factor]);F+=fg;M+=np.cross(com[g]-center,fg)
                mm=s/1000
                rr=[np.hypot(-F[1]/2+M[2]/mm,-F[2]/2-M[1]/mm),np.hypot(-F[1]/2-M[2]/mm,-F[2]/2+M[1]/mm)]
                r=max(rr);p0=max(r,.6*r+.5*abs(F[0]))
                row=record['spacing'][str(s)]
                if p0>row['max_reaction_N']:
                    row.update(max_reaction_N=float(p0),worst=dict(q_deg=q,force_N=force.tolist(),net_force_N=F.tolist(),bearing_transverse_moment_Nm=float(np.linalg.norm(M[1:])),motor_Nm=motor.tolist()))
    if i%49==0:print('Pose group',i,flush=True)

# Landing loads remain even when they exceed commanded actuator torque: impacts
# cannot be bounded by a motor current limit. These use actual nominal stances.
impact=summaries['unloaded_landing_nominal']
for q in [P['nominal_pose_deg'],[0,24,-48],[0,45,-90]]:
    com,G=grav(q);foot,origins,axes=contacts('FL',q)
    J=np.column_stack([np.cross(a,(foot-o)/1000) for a,o in zip(axes,origins)])
    for a in [None,*range(0,360,45)]:
        fz=mass*9.81*1.5
        force=fz*(np.array([0,0,1.]) if a is None else np.array([.4*math.cos(math.radians(a)),.4*math.sin(math.radians(a)),1]))
        motor=np.abs(3*G-J.T@force)/[1,1,P['knee_efficiency_assumption']]
        impact['accepted']+=1
        for s in spacings:
            center=np.array([P['hip_x']-54-s/2,P['roll_y'],0])/1000
            F=force.copy();M=np.cross(foot/1000-center,force)
            # Only static limb weight is subtracted in this contact shock case;
            # joint and body accelerations are not presumed to reduce the load.
            for g,(gm,_) in groups.items():
                fg=np.array([0,0,-gm*9.81]);F+=fg;M+=np.cross(com[g]-center,fg)
            mm=s/1000
            r=max(np.hypot(-F[1]/2+M[2]/mm,-F[2]/2-M[1]/mm),np.hypot(-F[1]/2-M[2]/mm,-F[2]/2+M[1]/mm))
            p0=max(r,.6*r+.5*abs(F[0]));row=impact['spacing'][str(s)]
            if p0>row['max_reaction_N']:row.update(max_reaction_N=float(p0),worst=dict(q_deg=q,force_N=force.tolist(),bearing_transverse_moment_Nm=float(np.linalg.norm(M[1:])),motor_Nm=motor.tolist(),motor_over_peak=bool(np.max(motor)>17)))

combined=[]
for s in spacings:
    worst=max(summaries,key=lambda name:summaries[name]['spacing'][str(s)]['max_reaction_N'])
    p0=summaries[worst]['spacing'][str(s)]['max_reaction_N']
    combined.append(dict(spacing_mm=s,bearing_pack_mm=s+7,max_equivalent_static_N=p0,governing_case=worst,
        static_rating_ratios={name:rating/p0 for name,rating in ratings.items()}))
out=dict(model_sha256=hashlib.sha256(raw).hexdigest(),base_mass_kg=mass,payload_kg=1,moving_leg_mass_kg=sum(m for m,c in groups.values()),
    static_rating_target_ratio=2.0,bearings_C0_N=ratings,summary=combined,cases=summaries,
    assumptions=['Torque-compatible cases use17Nm peak and6Nm rated reference,90percent knee efficiency,rigid lumped CAD masses and0.4horizontal/vertical ground force.',
        'Rated torque is a datasheet reference,not an enclosed printed-motor thermal qualification.',
        'The independent3g contact-landing screen is retained even when motor torque is exceeded.',
        'Bearing pair takes the entire transverse wrench; motor-bearing load sharing is not credited.',
        'P0=max(Fr,0.6Fr+0.5Fa) per individual deep-groove bearing; entire axial load conservatively assigned to each bearing.',
        'Catalog ratio2 is a selected screening criterion,not complete component safety qualification.'],
    limitations=['No impulse/contact-time,oscillatory life,bearing stiffness,manufacturing fit,housing deflection,preload or full inverse dynamics.',
        'Pose grid is an instantaneous load envelope,not a collision-checked gait or demonstrated stair motion.',
        'Self-righting body contacts and side/inverted support require a separate test envelope.',
        'The future20kg payload robot is excluded and requires a newly selected bearing architecture.'])
OUT=ROOT/'output/roll-spacing-study';OUT.mkdir(exist_ok=True)
(OUT/'loads.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'summary':combined,'counts':{k:(v['accepted'],v['rejected_by_motor_torque']) for k,v in summaries.items()}},indent=2))
