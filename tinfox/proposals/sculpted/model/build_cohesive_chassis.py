"""Export an enclosure/assembly candidate without replacing audited references."""
import hashlib,importlib.util,json,shutil
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
import cohesive_chassis as design
import build as b
from export_closed_mesh import closed_mesh
from kinematics import ROOT,uniform

BASE=design.BASE;OUT=ROOT/'output/cohesive-chassis-work'
OUT.mkdir(exist_ok=True)
for sub in ['step','stl']:shutil.copytree(BASE/sub,OUT/sub,dirs_exist_ok=True)
(OUT/'reference-brep').mkdir(exist_ok=True)
raw=(BASE/'model.json').read_bytes();data=json.loads(raw);exports=[];changes=[]
removed={p['name'] for p in data['parts'] if p['name'].startswith(('chassis_tie_nut_','body_service_screw_','sensor_root_nut_'))}
removed_mass=sum(p['mass_kg'] for p in data['parts'] if p['name'] in removed)
data['parts']=[p for p in data['parts'] if p['name'] not in removed]
template=dict(next(p for p in data['parts'] if p['name'].startswith('chassis_tie_bolt_')))
for x in [-64,64]:
    for side in [-1,1]:
        key=f'body_service_screw_{side}_{x}_18'
        data['parts'].append({**template,'name':key,'mesh':key,'mass_kg':0,'volume_mm3':0,'bounds_mm':[0,0,0]})

def volume(s):
    p=GProp_GProps();BRepGProp.VolumePropertiesGK_s(s.wrapped,p,1e-9,True,True);return p.Mass()

def replace(key,s,note):
    assert s.isValid() and len(s.Solids())==1,(key,'solid invalid')
    parts=[p for p in data['parts'] if p['mesh']==key];assert parts,key
    previous=sum(p['mass_kg'] for p in parts)
    vv,ff=s.tessellate(.08,.1);bb=s.BoundingBox();v=volume(s)
    data['meshes'][key]={'vertices':[list(x.toTuple()) for x in vv],'faces':[list(x) for x in ff]}
    for p in parts:p.update(volume_mm3=v,mass_kg=v*b.DENSITY[p['material']],com_mm=list(s.Center().toTuple()),bounds_mm=[bb.xlen,bb.ylen,bb.zlen],note=note)
    changes.append({'part':key,'mass_change_kg':sum(p['mass_kg'] for p in parts)-previous,'volume_mm3':v})
    s.exportBrep(str(OUT/'reference-brep'/(key+'.brep')))
    cq.exporters.export(s,str(OUT/'step'/(key+'.step')))
    cq.exporters.export(s,str(OUT/'stl'/(key+'.stl')),tolerance=.08,angularTolerance=.1)
    mesh,mesh_check=closed_mesh(OUT/'step'/(key+'.step'),OUT/'stl'/(key+'.stl'),v)
    data['meshes'][key]={'vertices':mesh.vertices.tolist(),'faces':mesh.faces.tolist()}
    restored=cq.importers.importStep(str(OUT/'step'/(key+'.step'))).val()
    error=abs(volume(restored)-v);assert restored.isValid() and len(restored.Solids())==1 and error<max(.1,v*1e-4),(key,error)
    exports.append({'part':key,'closed_solids':1,'roundtrip_volume_error_mm3':error,'mesh':mesh_check})
    print('Export',key,round(v),flush=True)

replace('body_center_0',design.cover(),'Continuous tangent shoulder opening with four lateral M3 x 10 screws into integral metal frame bosses at X +/-64, Z18. No cover tabs surround the fixed roll motor. Cover lifts upward after four screws are removed; motor frame remains assembled. Printed fit and strength unqualified.')
replace('belly_center_0',design.belly(),'Lower protective shell ends inside a rounded cassette perimeter. Thin motor-facing end crescents removed; actuator loads bypass this enclosure.')
for side in [-1,1]:
    replace('chassis_beam_'+str(side*102),design.rail(side),'Aluminum motor rail with integral tapped M3 tie pads and gusseted cover screw bosses. Tie screw axes Y +/-104; 6 mm nominal engagement in 8 mm pads. Print-only copies are unloaded fit mockups. Tapping, local bearing and frame fatigue require qualification.')
for front in [-1,1]:
    replace('chassis_crossmember_'+str(front*121),design.crossmember(front),'Removable transverse tie with fastener feet at X +/-115, Y +/-104 and M3 x 8 countersunk screws seating at Z36. Two screws per rail thread into integral metal pads. Front tie has two integral 6.8 mm M4 tapped sensor pads; sensor mounting remains independently removable.')
    for side in [-1,1]:
        for dx in [-3,3]:replace(f'chassis_tie_bolt_{front*121}_{side}_{dx}',design.tie_screw(front,side,dx),'Common M3 x 8 countersunk screw. Cone seats at Z34.7..36, tip Z28; nominal tapped metal engagement 6 mm. Exact purchased head geometry and tightening torque require verification.')
for x in [-64,64]:
    for side in [-1,1]:replace(f'body_service_screw_{side}_{x}_18',design.cover_screw(x,side),'Common M3 x 10 socket screw through the cover into a gusseted metal rail boss; lateral tool access after limb positioning. Hole geometry represents a nominal M3 tapped bore, without helical threads.')
for outer in [False,True]:
    s=design.smooth_thigh(outer);key='thigh_outer' if outer else 'thigh_inner'
    for right in [False,True]:replace(key+('_right' if right else ''),s.mirror('XZ') if right else s,'Continuous outer thigh face without the cosmetic waist depression. Six-millimetre outer waist skin, eight-millimetre sidewalls, original motor/crank/bearing datums and two structural halves. Strength remains unqualified.')
data['parameters'].update(body_cover_screw_x_mm=64,body_cover_screw_z_mm=18,chassis_tie_y_mm=104,chassis_tie_pad_x_mm=115,
    chassis_tie_pad_height_mm=8,chassis_tie_engagement_mm=6,slim_waist_divot_depth_mm=0,
    slim_roof_bezier_control_points_mm=[[[-117,94],[-108,94],[-105,94],[-90,94]],[[-90,94],[-76,94],[-61,94],[-45,94]]])
data['status']='Cohesive enclosure and frame-assembly review candidate. Continuous shoulder openings, integral tapped metal frame pads and a smooth thigh face. Physical strength, fastener tolerances and manufacturing processes remain unqualified.'
data['source_model_sha256']=hashlib.sha256(raw).hexdigest()
encoded=json.dumps(data,separators=(',',':')).encode();stamp=hashlib.sha256(encoded).hexdigest();(OUT/'model.json').write_bytes(encoded)
(OUT/'step-roundtrip.json').write_text(json.dumps({'model_sha256':stamp,'parts':exports},indent=2))
spec=importlib.util.spec_from_file_location('review',ROOT.parents[2]/'viewer/serve.py');review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
new,old=review.Engine(OUT/'model.json'),review.Engine(BASE/'model.json')
poses=[]
for row in json.loads((BASE/'audit.json').read_text())['motion_samples']:
    q=row['angles'];hits={tuple(x) for x in new.check(q)['pairs']};before={tuple(x) for x in old.check(q)['pairs']}
    poses.append({'pose':row['pose'],'angles':q,'hits':sorted(hits),'added_pairs':sorted(hits-before),
        'removed_pairs':sorted(before-hits),'source_hit_count':len(before),'passed':not hits})
(OUT/'audit.json').write_text(json.dumps({'model_sha256':stamp,'motion_samples':poses,
    'scope':'Nominal rigid parts at recorded poses. Mating/body-frame groups excluded; independent static and removal checks are required. No tolerance, flexible-cable or loaded-motion qualification.'},indent=2))
fold=[]
for knee in range(-156,-47):
    q=uniform([0,30,knee]);hits={tuple(x) for x in new.check(q)['pairs']};before={tuple(x) for x in old.check(q)['pairs']}
    fold.append({'knee_pitch_deg':knee,'pairs':sorted(hits),'added_pairs':sorted(hits-before)})
(OUT/'limb-folding.json').write_text(json.dumps({'model_sha256':stamp,'knee_samples':fold,'clear_samples':sum(not r['pairs'] for r in fold)},indent=2))
report={'model_sha256':stamp,'source_model_sha256':hashlib.sha256(raw).hexdigest(),'changes':changes,
    'removed_parts':sorted(removed),'mass_change_kg':sum(r['mass_change_kg'] for r in changes)-removed_mass,
    'previously_clear_poses_lost':[r['pose'] for r in poses if not r['source_hit_count'] and r['hits']],
    'added_motion_pairs':[{'pose':r['pose'],'pairs':r['added_pairs']} for r in poses if r['added_pairs']],
    'scope':data['status']}
(OUT/'chassis-review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
