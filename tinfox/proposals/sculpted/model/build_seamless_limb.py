"""Export and audit a coordinated rounded thigh and shin browser candidate."""
import hashlib,importlib.util,json,shutil
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
import seamless_limb as design
import build as b
from kinematics import ROOT,uniform

BASE=ROOT/'output/limb-refinement';OUT=ROOT/'output/seamless-limb-work'
OUT.mkdir(exist_ok=True)
for folder in ['step','stl']:shutil.copytree(BASE/folder,OUT/folder,dirs_exist_ok=True)
raw=(BASE/'model.json').read_bytes();data=json.loads(raw);changes=[];exports=[]
def volume(shape):
    p=GProp_GProps();BRepGProp.VolumeProperties_s(shape.wrapped,p,1e-9,True,False);return p.Mass()
for kind,fn in [('thigh',design.thigh),('shin',design.shin)]:
    for outer in [False,True]:
        key=kind+('_outer' if outer else '_inner');shape=fn(outer)
        old=next(p for p in data['parts'] if p['mesh']==key)
        changes.append({'part':key,'source_volume_mm3':old['volume_mm3'],'candidate_volume_mm3':volume(shape)})
        for right in [False,True]:
            name=key+('_right' if right else '');s=shape.mirror('XZ') if right else shape
            assert s.isValid() and len(s.Solids())==1
            vertices,faces=s.tessellate(.1,.08);bb=s.BoundingBox();v=volume(s)
            data['meshes'][name]={'vertices':[list(p.toTuple()) for p in vertices],'faces':[list(f) for f in faces]}
            for p in data['parts']:
                if p['mesh']==name:
                    p.update(volume_mm3=v,mass_kg=v*b.DENSITY[p['material']],com_mm=list(s.Center().toTuple()),bounds_mm=[bb.xlen,bb.ylen,bb.zlen],note='Coordinated rounded structural limb. Thigh motor cup and crowned face; shin rounded crosssection with integral cam and complete bearing seats. Original linkage and foot planes retained. Nominal fit/motion checks do not establish printed strength.')
                    p['appearance_role']='fox' if kind=='thigh' else 'charcoal'
            path=OUT/'step'/(name+'.step');cq.exporters.export(s,str(path));restored=cq.importers.importStep(str(path)).val()
            error=abs(volume(restored)-v);assert restored.isValid() and len(restored.Solids())==1
            assert error<max(.1,v*.001),(name,error,v)
            cq.exporters.export(s,str(OUT/'stl'/(name+'.stl')),tolerance=.1,angularTolerance=.08)
            exports.append({'part':name,'valid_closed_solids':1,'roundtrip_volume_error_mm3':error});print('Export',name,round(v),round(error,3),flush=True)
data['parameters'].update(seamless_thigh_face_radius_mm=design.FACE_RADIUS,seamless_thigh_outer_edge_radius_mm=8,seamless_shell_wall_mm=4,seamless_thigh_cap_y_mm=94)
data['status']='Coordinated rounded limb candidate retaining the established mechanism. Generated review geometry; native migration target and manufacturing qualification remain separate.'
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
    hits,added,removed,source_count=compare(row['angles'])
    poses.append({'pose':row['pose'],'angles':row['angles'],'hits':hits,'added_pairs':added,'removed_pairs':removed,'source_hit_count':source_count,'passed':not hits})
(OUT/'audit.json').write_text(json.dumps({'model_sha256':stamp,'motion_samples':poses,'scope':'All physical reference hardware retained. Listed mating interfaces and same rigid groups are excluded; this nominal sampled screen does not qualify continuous motion, tolerances or deflection.'},indent=2))
fold=[]
for knee in range(-156,-47):
    hits,added,removed,count=compare(uniform([0,30,knee]));fold.append({'knee_pitch_deg':knee,'pairs':hits,'added_pairs':added,'removed_pairs':removed})
(OUT/'limb-folding.json').write_text(json.dumps({'model_sha256':stamp,'knee_samples':fold,'clear_samples':sum(not r['pairs'] for r in fold),'new_collision_sample_count':sum(bool(r['added_pairs']) for r in fold)},indent=2))
report={'model_sha256':stamp,'source_model_sha256':hashlib.sha256(raw).hexdigest(),'part_changes':changes,
    'geometry':'Crowned thigh face, softened continuous perimeter and tapered motor cup; rounded shin crosssections and one uninterrupted cam-to-stem side profile. Both halves derive from each segment master.',
    'mechanism':'Original actuator orientation, 28 mm crank radius, pushrod plane, bearing positions and foot spacing retained.',
    'clear_named_poses':[r['pose'] for r in poses if r['passed']],
    'previously_clear_poses_lost':[r['pose'] for r in poses if not r['source_hit_count'] and r['hits']],
    'added_pairs_in_already_invalid_poses':[{k:r[k] for k in ['pose','added_pairs']} for r in poses if r['source_hit_count'] and r['added_pairs']],
    'knee_samples':len(fold),'clear_knee_samples':sum(not r['pairs'] for r in fold),
    'mass_change_whole_robot_kg':sum((r['candidate_volume_mm3']-r['source_volume_mm3'])*b.DENSITY['petg'] for r in changes)*4,
    'manufacturing_scope':'Two structural halves per segment, open internal pockets, complete bearing seats and retained extraction paths. Curved skins need ball-end finishing for CNC and slicer orientation/support review for printing. Existing metal ring/ties retained; no part-count or overall-width reduction claimed.',
    'unqualified':['material strength/fatigue','physical printed bearing fit','manufacturing variation and elastic deflection','thermal behavior and flexible cables']}
(OUT/'seamless-limb-review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
