"""Export and compare the manufacturing-refined two-piece thigh candidate."""
import hashlib,importlib.util,json,shutil
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
import manufacturing_thigh as design
import build as b
from kinematics import ROOT,uniform

BASE=ROOT/'output/seamless-limb-work'
OUT=ROOT/'output/manufacturing-thigh-work'
OUT.mkdir(exist_ok=True)
for sub in ['step','stl']:shutil.copytree(BASE/sub,OUT/sub,dirs_exist_ok=True)
raw=(BASE/'model.json').read_bytes();data=json.loads(raw);exports=[];changes=[]
def volume(s):
    p=GProp_GProps();BRepGProp.VolumeProperties_s(s.wrapped,p,1e-9,True,False);return p.Mass()
for outer in [False,True]:
    key='thigh_'+('outer' if outer else 'inner');shape=design.thigh(outer)
    old=next(p for p in data['parts'] if p['mesh']==key)
    changes.append({'part':key,'source_volume_mm3':old['volume_mm3'],'candidate_volume_mm3':volume(shape)})
    for right in [False,True]:
        name=key+('_right' if right else '');s=shape.mirror('XZ') if right else shape
        assert s.isValid() and len(s.Solids())==1
        vertices,faces=s.tessellate(.1,.08);bb=s.BoundingBox();v=volume(s)
        data['meshes'][name]={'vertices':[list(p.toTuple()) for p in vertices],'faces':[list(f) for f in faces]}
        for part in data['parts']:
            if part['mesh']==name:part.update(volume_mm3=v,mass_kg=v*b.DENSITY[part['material']],
                com_mm=list(s.Center().toTuple()),bounds_mm=[bb.xlen,bb.ylen,bb.zlen],
                note='Two-piece structural thigh with analytic motor cup, blended straight service split, cutter-relieved nut pocket, shallow fixture contacts and motor-bore lead-in. Oriented print files are unsliced; fit and loaded strength need qualification.')
        path=OUT/'step'/(name+'.step');cq.exporters.export(s,str(path));restored=cq.importers.importStep(str(path)).val()
        error=abs(volume(restored)-v);assert restored.isValid() and len(restored.Solids())==1
        assert error<max(.1,v*.001),(name,error)
        cq.exporters.export(s,str(OUT/'stl'/(name+'.stl')),tolerance=.1,angularTolerance=.08)
        exports.append({'part':name,'valid_closed_solids':1,'roundtrip_volume_error_mm3':error})
        print('Export',name,round(v),flush=True)
data['parameters'].update(thigh_cnc_relief_tool_diameter_mm=3,thigh_split_blend_radius_mm=3,
    thigh_fixture_land_diameter_mm=8,thigh_fixture_land_y_mm=93.4,thigh_motor_bore_entry_chamfer_mm=1)
data['status']='Manufacturing-refined rounded thigh review candidate. Generated reference; CNC toolpaths, printed fit and strength remain unqualified.'
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
    'scope':'Nominal rigid parts at recorded samples; mating interfaces and rigid groups excluded. No continuous, tolerance, cable or loaded-motion qualification.'},indent=2))
fold=[]
for knee in range(-156,-47):
    hits,added,removed,count=compare(uniform([0,30,knee]));fold.append({'knee_pitch_deg':knee,
        'pairs':hits,'added_pairs':added,'removed_pairs':removed})
(OUT/'limb-folding.json').write_text(json.dumps({'model_sha256':stamp,'knee_samples':fold,
    'clear_samples':sum(not r['pairs'] for r in fold),'new_collision_sample_count':sum(bool(r['added_pairs']) for r in fold)},indent=2))
report={'model_sha256':stamp,'source_model_sha256':hashlib.sha256(raw).hexdigest(),
    'part_changes':changes,'clear_named_poses':[r['pose'] for r in poses[:8] if r['passed']],
    'previously_clear_poses_lost':[r['pose'] for r in poses if not r['source_hit_count'] and r['hits']],
    'added_collision_pairs':[{'pose':r['pose'],'pairs':r['added_pairs']} for r in poses if r['added_pairs']],
    'mass_change_whole_robot_kg':sum((r['candidate_volume_mm3']-r['source_volume_mm3'])*b.DENSITY['petg'] for r in changes)*4,
    'finished_thigh_halves_per_leg':2,
    'scope':'Machining reliefs and print preparation reduce specific manufacturing difficulties. No supplier quote, CAM/holder verification, sliced supports, tolerance or strength qualification.'}
(OUT/'manufacturing-thigh-review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
