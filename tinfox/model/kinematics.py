"""Shared millimetre kinematics for CAD, collision checks and mass calculations."""
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
P=json.loads((ROOT/'parameters.json').read_text())
LEGS={'FL':(1,1), 'FR':(1,-1), 'RL':(-1,1), 'RR':(-1,-1)}

def translation(x=0,y=0,z=0):
    m=np.eye(4);m[:3,3]=(x,y,z);return m

def rotation(axis,degree):
    a=np.deg2rad(degree);c,s=np.cos(a),np.sin(a);m=np.eye(4)
    if axis=='x':m[:3,:3]=[[1,0,0],[0,c,-s],[0,s,c]]
    if axis=='y':m[:3,:3]=[[c,0,s],[0,1,0],[-s,0,c]]
    return m

def frames(leg,q):
    front,side=LEGS[leg];roll,hip,knee=q
    r=translation(front*P['hip_x'],side*P['roll_y'],0)@rotation('x',side*roll)
    p=r@translation(0,side*P['pitch_offset'],0)@rotation('y',hip)
    k=p@translation(0,0,-P['thigh'])@rotation('y',knee)
    a=knee+P['crank_phase_deg'];v=rotation('y',a)@np.array([P['crank_radius'],0,0,1])
    return {'mount':translation(front*P['hip_x'],side*P['roll_y'],0),'roll':r,'thigh':p,'knee':k,'crank':p@rotation('y',a),'rod':p@translation(*v[:3])}

def matrix(part,poses):
    if not part.get('leg'):return np.eye(4)
    return frames(part['leg'],poses[part['leg']])[part['group']]

def point(m,p):return (m@np.r_[p,1])[:3]

def contacts(leg,q):
    _,side=LEGS[leg];f=frames(leg,q)
    center=point(f['knee'],[0,side*P['shin_y'],-P['shank_to_foot_center']])
    foot=center+np.array([0,0,-P['foot_radius']])
    origins=[f['roll'][:3,3],f['thigh'][:3,3],f['knee'][:3,3]]
    axes=[f['roll'][:3,0]*side,f['thigh'][:3,1],f['knee'][:3,1]]
    return foot,origins,axes

def uniform(q):return {leg:list(q) for leg in LEGS}

POSES={
 'stand':uniform(P['nominal_pose_deg']),
 'raised':uniform([0,24,-48]),
 'crouch':uniform([0,65,-130]),
 'reach':{'FL':[8,-10,-75],'FR':[8,38,-76],'RL':[8,38,-76],'RR':[8,38,-76]},
 'fold':uniform([0,77,-154]),
 'splay':uniform([25,35,-70]),
 'side_reach':{'FL':[-60,-35,-70],'FR':[60,-35,-70],'RL':[-60,35,-70],'RR':[60,35,-70]},
}
