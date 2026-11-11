"""Export the slimmer mounting structure and thigh; compare the complete robot."""
import hashlib,importlib.util,json,math,shutil
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
import slim_limb as design
import build as b
from kinematics import ROOT,uniform

BASE=design.BASE;OUT=ROOT/'output/slim-limb-work';OUT.mkdir(exist_ok=True)
for sub in ['step','stl']:shutil.copytree(BASE/sub,OUT/sub,dirs_exist_ok=True)
(OUT/'reference-brep').mkdir(exist_ok=True)
raw=(BASE/'model.json').read_bytes();data=json.loads(raw);changes=[];exports=[]
for leg in ['FL','FR','RL','RR']:
    template=dict(next(p for p in data['parts'] if p['name']==leg+'_thigh_clamp_nut_0'))
    template.update(name=leg+'_thigh_clamp_nut_1',mesh='thigh_clamp_nut_1'+('_right' if leg.endswith('R') else ''),
        volume_mm3=0,mass_kg=0,bounds_mm=[0,0,0],note='Standard M4 nut makes the front shell clamp a complete through-bolt joint.')
    data['parts'].append(template)
def volume(s):
    # Span-aware integration avoids the known whole-face NURBS quadrature
    # instability. Export comparison uses the same method on both solids.
    p=GProp_GProps();error=BRepGProp.VolumePropertiesGK_s(s.wrapped,p,1e-9,True,True)
    assert error>=0
    return p.Mass()
factories={'thigh_inner':lambda:design.thigh(False),'thigh_outer':lambda:design.thigh(True),
    'hip_hub':design.hub,'motor_mount_ring':design.plate}
for angle in b.POD_TIE_ANGLES:
    for prefix in ['pod_tie_','pod_sleeve_']:
        key=prefix+str(angle);factories[key]=lambda key=key,angle=angle:design.tie_part(key,angle)
for key in ['sleeve_0','bolt_0','thigh_clamp_nut_0']:factories[key]=lambda key=key:design.clamp_part(key)
for key in ['sleeve_1','bolt_1','thigh_clamp_nut_1']:factories[key]=lambda key=key:design.front_clamp_part(key)
for key in ['input_pin','output_pin']:factories[key]=lambda key=key:design.pin_part(key)
for key,fn in factories.items():
    shape=fn();old=next(p for p in data['parts'] if p['mesh']==key)
    changes.append({'part':key,'material':old['material'],'source_volume_mm3':old['volume_mm3'],
        'candidate_volume_mm3':volume(shape),'source_bounds_mm':old['bounds_mm']})
    for right in [False,True]:
        name=key+('_right' if right else '');s=shape.mirror('XZ') if right else shape
        expected=2 if key.startswith('pod_sleeve_') else 1
        assert s.isValid() and len(s.Solids())==expected,(name,s.isValid(),len(s.Solids()))
        vv,ff=s.tessellate(.08,.08);bb=s.BoundingBox();v=volume(s)
        data['meshes'][name]={'vertices':[list(p.toTuple()) for p in vv],'faces':[list(f) for f in ff]}
        for part in data['parts']:
            if part['mesh']==name:
                part.update(volume_mm3=v,mass_kg=v*b.DENSITY[part['material']],com_mm=list(s.Center().toTuple()),
                    bounds_mm=[bb.xlen,bb.ylen,bb.zlen])
                if key.startswith('thigh_'):
                    part['note']=f'Slender common-profile structural thigh: narrower motor cup, tapered web depth, full knee bearing backup and round clamp-access recesses. Two structural halves. Same motor/linkage/bearing datums and {design.TIE_RADIUS} mm tie circle; common through-bolt clamps. Printed fit and strength unqualified.'
                elif key in ['hip_hub','motor_mount_ring']:
                    part['note']=f'Rounded three-point aluminum mounting structure retaining the actuator bolt pattern. Tie circle radius {design.TIE_RADIUS} mm. Integral hub ribs and locally thickened tie pads support overturning loads; strength/fatigue remain unqualified.'
                elif key in ['sleeve_0','bolt_0','thigh_clamp_nut_0','sleeve_1','bolt_1','thigh_clamp_nut_1']:
                    part['note']='Common M4 x 25 screw, 18 mm compression sleeve and M4 nut stack. Both thigh clamps use the same dimensions; circular recesses expose the nuts. One standard nut is added at the previously incomplete front clamp.'
                elif key.startswith('pod_sleeve_'):
                    part['note']=f'5 mm OD / 3.4 mm ID metal tube segments, cut to 41 and 6 mm. The complete tie compression stack spans hub pad to stator pad to screw head; tie radius {design.TIE_RADIUS} mm. Two separately cut sleeves per tie.'
                elif key in ['input_pin','output_pin']:
                    part['note']='Existing 6 x 20 mm shoulder screw with excess M5 thread shortened to 7 mm and deburred. Loaded shoulder and 4 mm nut engagement remain unchanged, with 3 mm thread beyond the nut. Exact stock revision and grade require verification.'
                else:part['note']=part.get('note','')+f' Tie circle radius {design.TIE_RADIUS} mm; screw dimensions unchanged.'
        s.exportBrep(str(OUT/'reference-brep'/(name+'.brep')))
        cq.exporters.export(s,str(OUT/'stl'/(name+'.stl')),tolerance=.08,angularTolerance=.08)
        file=OUT/'step'/(name+'.step');cq.exporters.export(s,str(file));restored=cq.importers.importStep(str(file)).val()
        error=abs(volume(restored)-v);assert restored.isValid() and len(restored.Solids())==expected
        assert error<max(.1,v*.001),(name,error,v)
        exports.append({'part':name,'closed_solids':expected,'roundtrip_volume_error_mm3':error})
        print('Export',name,round(v),flush=True)
data['parameters'].update(slim_tie_radius_mm=design.TIE_RADIUS,slim_case_bore_radius_mm=design.CASE_BORE_RADIUS,
    slim_case_outer_radius_mm=design.CASE_OUTER_RADIUS,slim_wall_mm=design.WALL,
    slim_rear_clamp_xz_mm=list(design.REAR_CLAMP),slim_roof_bezier_control_points_mm=design.ROOF_BEZIER,
    slim_front_clamp_xz_mm=list(design.FRONT_CLAMP),slim_waist_outer_skin_maximum_mm=6,
    slim_inner_knee_pad_y_mm=[45,49],slim_knee_opening_y_mm=[50.5,86.5],
    slim_pin_thread_length_mm=7,slim_pin_tail_clearance_radial_mm=1.75,
    slim_stator_plate_outer_radius_mm=design.PLATE_OUTER_RADIUS,slim_stator_plate_boss_radius_mm=design.PLATE_BOSS_RADIUS)
data['status']='Slim structural limb review candidate. Rounded mounting profiles and tapered thigh around fixed motor, linkage and bearing datums. No physical strength or manufacturing qualification.'
data['source_model_sha256']=hashlib.sha256(raw).hexdigest()
encoded=json.dumps(data,separators=(',',':')).encode();stamp=hashlib.sha256(encoded).hexdigest();(OUT/'model.json').write_bytes(encoded)
(OUT/'step-roundtrip.json').write_text(json.dumps({'model_sha256':stamp,'parts':exports},indent=2))
spec=importlib.util.spec_from_file_location('review',ROOT.parents[2]/'viewer/serve.py');review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
new,old=review.Engine(OUT/'model.json'),review.Engine(BASE/'model.json')
def compare(q):
    a={tuple(x) for x in new.check(q)['pairs']};z={tuple(x) for x in old.check(q)['pairs']}
    return sorted(a),sorted(a-z),sorted(z-a),len(z)
poses=[]
for row in json.loads((BASE/'audit.json').read_text())['motion_samples']:
    hits,added,removed,count=compare(row['angles'])
    poses.append({'pose':row['pose'],'angles':row['angles'],'hits':hits,'added_pairs':added,
        'removed_pairs':removed,'source_hit_count':count,'passed':not hits})
(OUT/'audit.json').write_text(json.dumps({'model_sha256':stamp,'motion_samples':poses,
    'scope':'Nominal rigid hardware at recorded samples. Mating interfaces and rigidly attached groups excluded; no continuous, tolerance, cable or loaded-motion qualification.'},indent=2))
fold=[]
for knee in range(-156,-47):
    hits,added,removed,count=compare(uniform([0,30,knee]));fold.append({'knee_pitch_deg':knee,
        'pairs':hits,'added_pairs':added,'removed_pairs':removed})
(OUT/'limb-folding.json').write_text(json.dumps({'model_sha256':stamp,'knee_samples':fold,
    'clear_samples':sum(not r['pairs'] for r in fold),'new_collision_sample_count':sum(bool(r['added_pairs']) for r in fold)},indent=2))
delta=sum((r['candidate_volume_mm3']-r['source_volume_mm3'])*b.DENSITY[r['material']] for r in changes)*4
report={'model_sha256':stamp,'source_model_sha256':hashlib.sha256(raw).hexdigest(),'part_changes':changes,
    'clear_named_poses':[r['pose'] for r in poses[:8] if r['passed']],
    'previously_clear_poses_lost':[r['pose'] for r in poses if not r['source_hit_count'] and r['hits']],
    'added_collision_pairs':[{'pose':r['pose'],'pairs':r['added_pairs']} for r in poses if r['added_pairs']],
    'mass_change_whole_robot_kg':delta,'finished_thigh_halves_per_leg':2,'additional_standard_M4_nuts_per_leg':1,
    'mechanism':'Original actuator axes, actuator hole patterns, 43.5 mm tie radius, 28 mm cranks, 170 mm links, pushrod plane and complete bearing seats retained. Both shell clamps use a common through-bolt stack.',
    'scope':'Measured geometric slimming and sampled nominal fit/motion. New mounting load paths, printed strength, CNC toolpaths and loaded motion remain unqualified.'}
(OUT/'slim-limb-review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
