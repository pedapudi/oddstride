"""Stage and audit the low-profile hood with its integral raised lidar seat."""
import hashlib,importlib.util,json,shutil
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
import low_lidar_neck as neck
import build as b
from kinematics import ROOT,uniform,matrix

BASE=ROOT/'output/limb-refinement'
SNAP=ROOT/'output/low-lidar-reference'
OUT=ROOT/'output/low-lidar-work'
if not SNAP.exists():shutil.copytree(BASE,SNAP)
OUT.mkdir(exist_ok=True)
for sub in ['step','stl','print-stl']:
    shutil.copytree(SNAP/sub,OUT/sub,dirs_exist_ok=True)
raw=(SNAP/'model.json').read_bytes();model=json.loads(raw)
shapes=neck.parts()
def volume(s):
    props=GProp_GProps();BRepGProp.VolumeProperties_s(s.wrapped,props,1e-9,True,False)
    return props.Mass()
exports=[]
for key,shape in shapes.items():
    assert shape.isValid() and len(shape.Solids())==1,key
    vv,ff=shape.tessellate(.1,.1);bb=shape.BoundingBox()
    model['meshes'][key]={'vertices':[list(v.toTuple()) for v in vv],'faces':[list(f) for f in ff]}
    part=next(p for p in model['parts'] if p['name']==key)
    part.update(mesh=key,com_mm=list(shape.Center().toTuple()),bounds_mm=[bb.xlen,bb.ylen,bb.zlen],volume_mm3=volume(shape))
    if key=='front_fascia':
        part.update(mass_kg=volume(shape)*b.DENSITY['petg'],note='One removable camera hood and hollow lidar fairing. Integral seat at Z94; 18 mm cable opening into the neck. Remove the hood before lifting the main body cover. Sensor bolt pattern and printed strength require the selected lidar and physical qualification.')
    else:part['note']='Provisional lidar envelope raised 42 mm on the integral neck seat. Modeled optical band Z98–116; actual sensor beam geometry and bolt pattern are not selected.'
    cq.exporters.export(shape,str(OUT/'step'/f'{key}.step'))
    exported=cq.importers.importStep(str(OUT/'step'/f'{key}.step')).val()
    error=abs(volume(shape)-volume(exported))
    assert exported.isValid() and len(exported.Solids())==1 and error<max(.05,volume(shape)*1e-5),(key,error)
    exports.append({'part':key,'closed_solids':1,'volume_error_mm3':error})
    cq.exporters.export(shape,str(OUT/'stl'/f'{key}.stl'),tolerance=.1,angularTolerance=.1)
model['parameters'].update(neck.parameters())
model['status']='Low-profile candidate with integral raised lidar seat and revised bearing-supported limbs. Generated CAD remains authoritative pending native Fusion migration.'
model['source_model_sha256']=hashlib.sha256(raw).hexdigest()
encoded=json.dumps(model,separators=(',',':')).encode();stamp=hashlib.sha256(encoded).hexdigest()
(OUT/'model.json').write_bytes(encoded)
spec=importlib.util.spec_from_file_location('review',ROOT.parents[2]/'viewer/serve.py')
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
current=review.Engine(OUT/'model.json');previous=review.Engine(SNAP/'model.json')
motions=[]
for row in json.loads((SNAP/'audit.json').read_text())['motion_samples']:
    hits=current.check(row['angles'])['pairs'];old=previous.check(row['angles'])['pairs']
    added=[p for p in hits if p not in old]
    motions.append({'pose':row['pose'],'angles':row['angles'],'hits':hits,'added_pairs':added,'passed':not hits})
assert not any(r['added_pairs'] for r in motions),[(r['pose'],r['added_pairs']) for r in motions if r['added_pairs']]
(OUT/'audit.json').write_text(json.dumps({'model_sha256':stamp,'motion_samples':motions,'scope':'Whole rigid assembly at the listed poses. Existing extreme-pose collisions remain; no loaded or continuous-motion qualification.'},indent=2))
fold=[]
for knee in range(-156,-47):
    q=uniform([0,30,knee]);hits=current.check(q)['pairs'];old=previous.check(q)['pairs']
    fold.append({'knee_pitch_deg':knee,'pairs':hits,'added_pairs':[p for p in hits if p not in old]})
assert not any(r['pairs'] for r in fold),'Knee folding regression'
(OUT/'limb-folding.json').write_text(json.dumps({'model_sha256':stamp,'knee_samples':fold,'new_collision_sample_count':0,'scope':'Knee -156 to -48 degrees at hip pitch30 and roll0, sampled each degree.'},indent=2))

# Horizontal optical-plane intersections are stronger than sparse radial rays:
# any intersecting robot surface outside the sensor cylinder is an obstruction.
optical=[]
for pose in ['stand','studio','raised','crouch']:
    q=next(r['angles'] for r in motions if r['pose']==pose)
    for level in [98,107,116]:
        blocked=[]
        for part in model['parts']:
            if part['name'].startswith('lidar') or part.get('service_role') in ['keepout','withdrawal']:continue
            mesh=model['meshes'][part['mesh']]
            v=trimesh.transform_points(np.array(mesh['vertices']),matrix(part,q))
            if v[:,2].min()>level or v[:,2].max()<level:continue
            s=trimesh.Trimesh(v,mesh['faces'],process=False)
            segments=trimesh.intersections.mesh_plane(s,[0,0,1],[neck.LIDAR_X,0,level])
            if len(segments):blocked.append(part['name'])
        optical.append({'pose':pose,'scan_height_z_mm':level,'obstructions':blocked})
assert not any(r['obstructions'] for r in optical),optical
def overlap(a,c):return sum(volume(s) for s in a.intersect(c).Solids())
checks=[]
for key in ['body_nose_surround','body_center_0']:
    s=neck.reference(key);v=overlap(shapes['front_fascia'],s)
    checks.append({'interface':'hood / '+key,'overlap_mm3':v,'passed':v<.001})
for y in [-16,16]:
    v=overlap(shapes['front_fascia'],b.cyl(1.5,100,(136,y,57),(0,0,1)))
    checks.append({'interface':f'hood screw driver at Y{y}','overlap_mm3':v,'passed':v<.001})
for travel in [.1,1,5,15,30,60]:
    v=overlap(shapes['front_fascia'],shapes['lidar_base'].translate((0,0,travel)))
    checks.append({'interface':f'lidar upward withdrawal {travel} mm','overlap_mm3':v,'passed':v<.001})
assert all(c['passed'] for c in checks),checks
report={'model_sha256':stamp,'raise_mm':42,'seat_z_mm':94,'scan_band_z_mm':[98,116],
    'optical_plane_checks':optical,'service_checks':checks,'step_exports':exports,
    'assembly':['Route the lidar cable through the integral 18 mm opening into the open hood cavity.','Mount the selected lidar after specifying its bolt pattern; the displayed sensor is an envelope.','Install the combined camera hood and lidar assembly using the existing hood and face attachment points.','Remove the hood before lifting the main body cover; provide a disconnect and service slack in the lidar cable.'],
    'limits':['Horizontal nominal scan planes only. A selected 3D lidar may have downward beams that still see the robot.','Aggressive folded poses, cable motion, mounting tolerances, impact survival and printed strength remain unqualified.','The full hood is one printed part; support planning and sensor fasteners require a manufacturing review.']}
(OUT/'lidar-neck-review.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'model_sha256':stamp,'optical_checks':len(optical),'service_checks':len(checks),'exports':exports,'new_motion_pairs':0,'fold_samples':len(fold)},indent=2),flush=True)
