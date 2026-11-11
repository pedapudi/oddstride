"""Build the opposed-output motor module as an independent browser proposal."""
import hashlib,importlib.util,json,math,shutil
from pathlib import Path
import cadquery as cq
import numpy as np
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
import integrated_pitch_proposal as proposal
import build as b
from kinematics import ROOT,uniform

BASE=ROOT/'output/limb-refinement';OUT=ROOT/'output/integrated-pitch-work'
for sub in ['step','stl']:(OUT/sub).mkdir(parents=True,exist_ok=True)
raw=(BASE/'model.json').read_bytes();data=json.loads(raw)
removed=[];kept=[]
for p in data['parts']:
    local=p['name'].split('_',1)[-1] if p.get('leg') else ''
    if local.startswith(('pod_sleeve_','pod_tie_','motor_mount_ring','thigh_clamp_nut_')) or local in ['sleeve_0','sleeve_1','bolt_0','bolt_1']:
        removed.append(p['name'])
    else:kept.append(p)
data['parts']=kept
transformed={}
for p in data['parts']:
    if not p.get('leg'):continue
    local=p['name'].split('_',1)[-1]
    change=(p['group'] in ['knee','rod','crank'] or local in ['knee_motor','knee_axle','axle_bolt','axle_nut','knee_inner_spacer'] or local.startswith('knee_port_'))
    if not change:continue
    key=p['mesh']
    if key not in transformed:
        original=data['meshes'][key];v=np.array(original['vertices'],float);side=1 if p['leg'].endswith('L') else -1
        # Move the fixed output pin with the shared 27 mm cam radius.
        if local in ['output_pin','output_pivot_nut']:
            phase=math.radians(-78);v[:,0]+=-math.cos(phase);v[:,2]+=math.sin(phase)
        if local=='input_pin':v[:,0]-=1
        v[:,1]=side*proposal.FLIP_Y-v[:,1]
        if local=='knee_motor' or local.startswith('knee_port_'):
            angle=math.radians(proposal.KNEE_CLOCK);rotation=np.array([[math.cos(angle),0,math.sin(angle)],[0,1,0],[-math.sin(angle),0,math.cos(angle)]])
            v=v@rotation.T
        mesh={'vertices':v.tolist(),'faces':[list(reversed(f)) for f in original['faces']]}
        transformed[key]=mesh;data['meshes'][key]=mesh
    mesh=transformed[key];v=np.array(mesh['vertices']);p['com_mm']=v.mean(0).tolist();p['bounds_mm']=(v.max(0)-v.min(0)).tolist()

def volume(s):
    p=GProp_GProps();BRepGProp.VolumeProperties_s(s.wrapped,p,1e-9,True,False);return p.Mass()

def replace(key,shape,material=None,note=''):
    assert shape.isValid() and len(shape.Solids())==1,key
    vertices,faces=shape.tessellate(.12,.08);v=volume(shape);bb=shape.BoundingBox()
    data['meshes'][key]={'vertices':[list(p.toTuple()) for p in vertices],'faces':[list(f) for f in faces]}
    for part in data['parts']:
        if part['mesh']!=key:continue
        mat=material or part['material'];part.update(material=mat,volume_mm3=v,mass_kg=v*b.DENSITY[mat],com_mm=list(shape.Center().toTuple()),bounds_mm=[bb.xlen,bb.ylen,bb.zlen],note=note)
        if key.startswith('thigh_'):part['appearance_role']='fox'
    cq.exporters.export(shape,str(OUT/'step'/(key+'.step')))
    reopened=cq.importers.importStep(str(OUT/'step'/(key+'.step'))).val()
    assert reopened.isValid() and len(reopened.Solids())==1,('STEP',key)
    cq.exporters.export(shape,str(OUT/'stl'/(key+'.stl')),tolerance=.12,angularTolerance=.08)
    print('Export',key,round(v),flush=True)

proposal.configure()
shapes={'hip_hub':proposal.hub(),'thigh_inner':proposal.halves()[0],'thigh_outer':proposal.halves()[1],
        'input_crank':proposal.crank(),'shin_inner':proposal.shin(False),'shin_outer':proposal.shin(True)}
for key,shape in shapes.items():
    for right in [False,True]:
        name=key+('_right' if right else '');s=shape.mirror('XZ') if right else shape
        replace(name,s,note='Opposed-output pitch-module proposal. Two longitudinal structural thigh halves incorporate the stator support and keyed hip-output pocket. No external motor tie cage. Review geometry; not a fabrication release.')

template=next(p for p in data['parts'] if p['name']=='FL_thigh_inner')
def add_ref(name,shape,leg,note):
    vertices,faces=shape.tessellate(.14,.1);v=volume(shape);bb=shape.BoundingBox()
    data['meshes'][name]={'vertices':[list(p.toTuple()) for p in vertices],'faces':[list(f) for f in faces]}
    data['parts'].append({**template,'name':name,'mesh':name,'group':'thigh','leg':leg,'material':'steel','appearance_role':None,'color':'#a1aaa4','mass_kg':v*b.DENSITY['steel'],'volume_mm3':v,'com_mm':list(shape.Center().toTuple()),'bounds_mm':[bb.xlen,bb.ylen,bb.zlen],'note':note,'check':True})

for leg in ['FL','FR','RL','RR']:
    right=leg.endswith('R')
    def handed(s):return s.mirror('XZ') if right else s
    for i,(y,z) in enumerate([(18,43),(77,43),(7,-91),(54,-91)]):
        bolt=b.cyl(2,30,(-19,y,z),(1,0,0)).fuse(b.cyl(3.5,4,(11,y,z),(1,0,0)))
        nut=b.hex_nut(7,3.2,0,0,0,2).rotate((0,0,0),(0,0,1),90).translate((-14,y,z))
        add_ref(leg+'_carrier_shell_bolt_'+str(i),handed(bolt),leg,'Ordinary M4 x 30 socket-head screw reference; transverse access with a hex key.')
        add_ref(leg+'_carrier_shell_nut_'+str(i),handed(nut),leg,'Ordinary M4 nut in an externally accessible pocket.')
    for angle in range(20,380,40):
        a=math.radians(angle-proposal.KNEE_CLOCK);x,z=36.5*math.cos(a),36.5*math.sin(a)
        screw=b.cyl(1.5,8,(x,46.9,z)).fuse(b.cyl(2.75,3,(x,43.9,z)))
        add_ref(leg+'_knee_stator_screw_'+str(angle),handed(screw),leg,'M3 x 8 mounting envelope. Final thread engagement requires the actuator drawing; no vendor blind-hole-depth qualification.')
data['parameters'].update(crank_radius=27,shin_y=proposal.FLIP_Y-67,rod_y=proposal.ROD_Y,
    opposed_knee_output_y_mm=proposal.KNEE_FACE,knee_motor_command_sign=-1)
data['source_model_sha256']=hashlib.sha256(raw).hexdigest()
data['status']='Opposed-output integrated pitch module: structural stator support and keyed hip interface; preliminary architectural proposal with unresolved fit, strength and assembly checks.'
encoded=json.dumps(data,separators=(',',':')).encode();stamp=hashlib.sha256(encoded).hexdigest();(OUT/'model.json').write_bytes(encoded)
spec=importlib.util.spec_from_file_location('viewer',ROOT.parents[2]/'viewer/serve.py');viewer=importlib.util.module_from_spec(spec);spec.loader.exec_module(viewer)
new,old=viewer.Engine(OUT/'model.json'),viewer.Engine(BASE/'model.json')
rows=[]
for row in json.loads((BASE/'audit.json').read_text())['motion_samples']:
    q=row['angles'];hits=new.check(q)['pairs'];oldhits=old.check(q)['pairs']
    added=sorted(set(map(tuple,hits))-set(map(tuple,oldhits)))
    rows.append({'pose':row['pose'],'angles':q,'hits':hits,'added_pairs':added,'source_hit_count':len(oldhits),'passed':not hits})
(OUT/'audit.json').write_text(json.dumps({'model_sha256':stamp,'motion_samples':rows,'scope':'Initial rigid-part screen of an architectural proposal. New interference is reported; assembly, tolerance and strength are not qualified.'},indent=2))
fold=[]
for knee in range(-156,-47):
    hits=new.check(uniform([0,30,knee]))['pairs'];fold.append({'knee_pitch_deg':knee,'pairs':hits})
(OUT/'limb-folding.json').write_text(json.dumps({'model_sha256':stamp,'knee_samples':fold,'colliding_samples':sum(bool(r['pairs']) for r in fold)},indent=2))
report={'model_sha256':stamp,'source_model_sha256':hashlib.sha256(raw).hexdigest(),
    'architecture':'Opposed actuator outputs; crank between hip and knee actuators. Two structural longitudinal thigh halves contain a keyed hip flange pocket and integral knee stator bulkhead.',
    'removed_mounting_layers':['Separate knee stator ring','Three long axial motor ties','Six tube segments around those ties'],
    'retained_custom_hardware':['Keyed metal hip-output insert','Metal crank and pivot hardware','Existing knee bearings, axle sleeve and spacer'],
    'changed_parameters':{'crank_radius_mm':27,'knee_motor_output_y_mm':46,'rod_plane_y_mm':proposal.ROD_Y,'foot_center_y_mm':proposal.FLIP_Y-67},
    'new_clear_pose_losses':[r['pose'] for r in rows if not r['source_hit_count'] and r['hits']],
    'nominal_width_basis':'Actual world-space part bounds in the standing pose; geometry only.',
    'manufacturing_limitations':['Longitudinal halves expose pockets, motor mounts and wiring. Print orientation and CNC setups require review.','No strength or screw engagement qualification.','Knee actuator direction reverses; encoder/control sign needs calibration.','Narrower foot spacing changes lateral stability; gait and load capability are not established.']}
from kinematics import matrix,P
def width(model):
    P.update(model['parameters']);ys=[]
    for p in model['parts']:
        if p.get('service_role') in ['keepout','withdrawal']:continue
        v=np.array(model['meshes'][p['mesh']]['vertices']);m=matrix(p,model['poses']['stand']);ys.extend((v@m[:3,:3].T+m[:3,3])[:,1])
    return max(ys)-min(ys)
report['source_standing_width_mm']=width(json.loads(raw));report['candidate_standing_width_mm']=width(data)
(OUT/'integrated-pitch-review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
