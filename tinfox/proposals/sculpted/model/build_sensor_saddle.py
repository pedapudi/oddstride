"""Build a low sensor saddle and verify geometry, removal and nominal optics."""
import copy,hashlib,importlib.util,json,shutil
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
import low_sensor_saddle as design
import build as b
from kinematics import ROOT,uniform,matrix

BASE=ROOT/'output/limb-refinement';SNAP=ROOT/'output/sensor-saddle-reference';OUT=ROOT/'output/sensor-saddle-work'
if not SNAP.exists():shutil.copytree(BASE,SNAP)
OUT.mkdir(exist_ok=True)
for sub in ['step','stl','print-stl']:shutil.copytree(SNAP/sub,OUT/sub,dirs_exist_ok=True)
raw=(SNAP/'model.json').read_bytes();model=json.loads(raw);oldmodel=copy.deepcopy(model)
removed=[p['name'] for p in model['parts'] if p['name'].startswith(('camera_hood_','front_fascia_screw_'))]
model['parts']=[p for p in model['parts'] if p['name'] not in removed]
shapes=design.parts()
def volume(s):
    p=GProp_GProps();BRepGProp.VolumeProperties_s(s.wrapped,p,1e-9,True,False);return p.Mass()
exports=[]
for key,s in shapes.items():
    assert s.isValid() and len(s.Solids())==1,key
    p=next((p for p in model['parts'] if p['name']==key),None)
    if p is None:
        p={'name':key,'mesh':key,'material':'steel','color':'#626a65','group':'body','leg':None,'check':True};model['parts'].append(p)
    vv,ff=s.tessellate(.1,.1);bb=s.BoundingBox();v=volume(s)
    model['meshes'][key]={'vertices':[list(x.toTuple()) for x in vv],'faces':[list(x) for x in ff]}
    p.update(mesh=key,volume_mm3=v,com_mm=list(s.Center().toTuple()),bounds_mm=[bb.xlen,bb.ylen,bb.zlen])
    if p['material']!='envelope':p['mass_kg']=v*b.DENSITY[p['material']]
    notes={'front_fascia':'Low continuous hood with integral lidar seat and four top-access M3 screws. Straight upward release. The retained face mounting holes are available for the sensor cartridge; selected sensor retention remains to be detailed.',
        'body_nose_surround':'Short cradle with two direct crossmember feet, four open-bottom M3 nut pockets and two recessed M4 mounting screws. Print top clamping lands down.',
        'body_center_0':'Rounded main cover with closed obsolete lidar opening and a separate forward service opening. Cover lifts independently of the sensor saddle.',
        'chassis_crossmember_121':'Existing metal crossmember with two additional 4.4 mm holes at X121,Y±24 for the sensor cradle. Deburr drilled holes; structural qualification remains outstanding.'}
    p['note']=notes.get(key,'Standard fastener envelope; verify exact purchased dimensions and thread engagement.' if key.startswith('sensor_') else 'Provisional lidar envelope. Seat Z80, horizontal optical band Z84–102; actual model, mounting pattern and beam angles remain unselected.')
    cq.exporters.export(s,str(OUT/'step'/f'{key}.step'));out=cq.importers.importStep(str(OUT/'step'/f'{key}.step')).val();err=abs(volume(out)-v)
    assert out.isValid() and len(out.Solids())==1 and err<max(.05,v*1e-5),(key,err)
    cq.exporters.export(s,str(OUT/'stl'/f'{key}.stl'),tolerance=.1,angularTolerance=.1)
    exports.append({'part':key,'closed_solids':1,'volume_error_mm3':err})
    print('export',key,round(v,2),flush=True)
model['meshes']={k:v for k,v in model['meshes'].items() if k in {p['mesh'] for p in model['parts']}}
model['parameters'].update(design.parameters());model['parameters']['low_lidar_raise_mm']=28
model['status']='Low sensor saddle candidate with direct frame mounting and independent hood/body-cover removal. Prototype, not a strength or production qualification.'
model['source_model_sha256']=hashlib.sha256(raw).hexdigest()
encoded=json.dumps(model,separators=(',',':')).encode();stamp=hashlib.sha256(encoded).hexdigest();(OUT/'model.json').write_bytes(encoded)
checks=[]
def fit(label,a,c):
    v=sum(volume(s) for s in a.intersect(c).Solids());checks.append({'interface':label,'overlap_mm3':v,'passed':v<.001})
hood=shapes['front_fascia'];cradle=shapes['body_nose_surround'];body=shapes['body_center_0'];beam=shapes['chassis_crossmember_121']
for name,s in [('cradle',cradle),('body cover',body),('crossmember',beam)]:fit('hood / '+name,hood,s)
fit('cradle / crossmember',cradle,beam);fit('cradle / body cover',cradle,body)
for key,s in shapes.items():
    if key.startswith('sensor_'):
        for label,solid in [('hood',hood),('cradle',cradle),('crossmember',beam)]:fit(key+' / '+label,s,solid)
for dz in [.2,1,3,5,10,20,40,80]:
    fit(f'hood upward removal {dz} mm',hood.translate((0,0,dz)),cradle.fuse(body))
    fit(f'main cover upward removal {dz} mm',body.translate((0,0,dz)),hood.fuse(cradle))
    fit(f'cradle upward removal {dz} mm',cradle.translate((0,0,dz)),beam)
for i,(x,y) in enumerate(design.SCREWS):fit(f'hood driver {i}',b.cyl(1.5,80,(x,y,76),(0,0,1)),hood.fuse(shapes['lidar_base'],shapes['lidar']))
for y in [-24,24]:fit(f'root driver Y{y}, hood removed',b.cyl(2,80,(121,y,58),(0,0,1)),cradle)
for dz in [.2,1,5,20,60]:fit(f'lidar upward withdrawal {dz} mm',shapes['lidar_base'].translate((0,0,dz)),hood)
# Broad clear cavity route turns aft above the crossmember rather than
# cutting a cable hole through its thin central web.
for name,tool in [('lidar entry',b.cyl(4,20,(121,0,64),(0,0,1))),('aft cable corridor',b.cyl(4,25,(97,0,64),(1,0,0))),('body cable drop',b.cyl(4,34,(100,0,30),(0,0,1)))]:
    fit(name,tool,hood.fuse(cradle,body,beam))
(OUT/'saddle-interfaces.json').write_text(json.dumps({'model_sha256':stamp,'checks':checks,'passed':all(r['passed'] for r in checks),'scope':'Exact nominal solids and sampled straight removal paths. Bolts removed for service-path checks; sensor mount and flexible cables are provisional.'},indent=2))
print('INTERFACE FAILURES',[r for r in checks if not r['passed']],flush=True)

spec=importlib.util.spec_from_file_location('review',ROOT.parents[2]/'viewer/serve.py');review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
current=review.Engine(OUT/'model.json');previous=review.Engine(SNAP/'model.json');motions=[]
for row in json.loads((SNAP/'audit.json').read_text())['motion_samples']:
    hits=current.check(row['angles'])['pairs'];old=previous.check(row['angles'])['pairs']
    motions.append({'pose':row['pose'],'angles':row['angles'],'hits':hits,'added_pairs':[p for p in hits if p not in old],'passed':not hits})
(OUT/'audit.json').write_text(json.dumps({'model_sha256':stamp,'motion_samples':motions,'scope':'Whole rigid assembly at listed poses. Existing extreme-pose limitations remain; no loaded-motion qualification.'},indent=2))
print('ADDED MOTION',[(r['pose'],r['added_pairs']) for r in motions if r['added_pairs']],flush=True)
fold=[]
for knee in range(-156,-47):
    hits=current.check(uniform([0,30,knee]))['pairs'];fold.append({'knee_pitch_deg':knee,'pairs':hits})
(OUT/'limb-folding.json').write_text(json.dumps({'model_sha256':stamp,'knee_samples':fold,'new_collision_sample_count':sum(bool(r['pairs']) for r in fold),'scope':'Knee -156 to -48 at hip30 and roll0, one-degree samples.'},indent=2))
optical=[]
for pose in ['stand','studio','raised','crouch']:
    q=next(r['angles'] for r in motions if r['pose']==pose)
    for level in [84,93,102]:
        blocked=[]
        for p in model['parts']:
            if p['name'].startswith('lidar') or p.get('service_role') in ['keepout','withdrawal']:continue
            mesh=model['meshes'][p['mesh']];v=trimesh.transform_points(np.array(mesh['vertices']),matrix(p,q))
            if v[:,2].min()>level or v[:,2].max()<level:continue
            if len(trimesh.intersections.mesh_plane(trimesh.Trimesh(v,mesh['faces'],process=False),[0,0,1],[121,0,level])):blocked.append(p['name'])
        optical.append({'pose':pose,'scan_height_z_mm':level,'obstructions':blocked})
print('OPTICAL',[r for r in optical if r['obstructions']],flush=True)
prints=[]
for key,angle,axis,orientation in [('body_nose_surround',180,(1,0,0),'Top clamping lands down; mounting feet up.'),('front_fascia',90,(0,1,0),'Camera face toward the bed; neck rises in the build direction. Use a brim and local supports under the curved face and recessed features.'),('body_center_0',180,(1,0,0),'Roof toward the bed; inspect local supports beneath the curved roof.')]:
    s=shapes[key].rotate((0,0,0),axis,angle);bb=s.BoundingBox();s=s.translate((-bb.xmin,-bb.ymin,-bb.zmin));bb=s.BoundingBox()
    assert bb.xlen<305 and bb.ylen<300 and bb.zlen<305
    cq.exporters.export(s,str(OUT/'print-stl'/f'{key}.stl'),tolerance=.1,angularTolerance=.1)
    prints.append({'part':key,'orientation':orientation,'size_mm':[bb.xlen,bb.ylen,bb.zlen]})
report={'model_sha256':stamp,'seat_z_mm':80,'lidar_center_x_mm':121,'scan_band_z_mm':[84,102],'lower_than_previous_mm':14,'optical_plane_checks':optical,'step_exports':exports,'print_parts':prints,
 'removed_hardware':removed,'assembly':['Drill and deburr the two 4.4 mm crossmember holes, or manufacture the revised metal part.','Fit the cradle with two M4 x20 socket-head screws, flat washers and accessible nuts below the crossmember.','Insert four M3 nuts through the open underside of the cradle. Route cables aft around the crossmember, with a disconnect and service slack.','Lower the hood onto its four lands and fit four M3 x20 socket-head screws from above. The lidar does not cover these access holes.','The main body cover and sensor hood lift independently. Remove the hood before accessing the two cradle mounting screws.'],
 'limits':['The selected lidar mounting pattern and camera cartridge retention remain to be detailed. Retained face holes are not counted as chassis fasteners.','Actual 3D sensor beam angles, printed strength, fastener preload, impact survival and cable bend radii remain unqualified.','The cradle is suitable for a simple flat print orientation; the compound-curved hood needs localized supports and is not claimed to be support-free or a simple two-setup CNC part.']}
(OUT/'lidar-neck-review.json').write_text(json.dumps(report,indent=2))
passed=all(r['passed'] for r in checks) and not any(r['added_pairs'] for r in motions) and not any(r['pairs'] for r in fold) and not any(r['obstructions'] for r in optical)
print(json.dumps({'model_sha256':stamp,'passed':passed,'interface_checks':len(checks),'exports':len(exports),'print_parts':prints},indent=2),flush=True)
if not passed:raise SystemExit('Candidate needs correction; not published.')
