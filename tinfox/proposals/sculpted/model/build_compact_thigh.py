"""Build and compare the integrated motor-cup thigh for browser review."""
import copy
import hashlib
import importlib.util
import json
import shutil
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
import compact_motor_thigh as design
import build as b
from kinematics import ROOT,uniform

BASE=ROOT/'output/limb-refinement'
OUT=ROOT/'output/compact-thigh-work'
OUT.mkdir(exist_ok=True)
for sub in ['step','stl']:shutil.copytree(BASE/sub,OUT/sub,dirs_exist_ok=True)
(OUT/'print-stl').mkdir(exist_ok=True)
raw=(BASE/'model.json').read_bytes();data=json.loads(raw)
def volume(s):
    p=GProp_GProps();BRepGProp.VolumeProperties_s(s.wrapped,p,1e-9,True,False);return p.Mass()
exports=[];comparisons=[]
for outer in [False,True]:
    key='thigh_outer' if outer else 'thigh_inner';shape=design.thigh(outer)
    old=next(p for p in data['parts'] if p['mesh']==key)
    comparisons.append({'part':key,'before_volume_mm3':old['volume_mm3'],'after_volume_mm3':volume(shape),
        'mass_change_g':(volume(shape)-old['volume_mm3'])*b.DENSITY['petg']*1000})
    for right in [False,True]:
        name=key+('_right' if right else '');s=shape.mirror('XZ') if right else shape
        vertices,faces=s.tessellate(.1,.08);box=s.BoundingBox();v=volume(s)
        data['meshes'][name]={'vertices':[list(p.toTuple()) for p in vertices],'faces':[list(f) for f in faces]}
        for p in data['parts']:
            if p['mesh']==name:p.update(volume_mm3=v,mass_kg=v*b.DENSITY['petg'],com_mm=list(s.Center().toTuple()),bounds_mm=[box.xlen,box.ylen,box.zlen],note='Integrated tapered motor cup and 6 mm slimmer outer cap. Rounded axial connector windows permit bare-motor insertion. Bearing and linkage datums retained. Review candidate; strength and thermal behavior unqualified.')
        path=OUT/'step'/(name+'.step');cq.exporters.export(s,str(path));reopened=cq.importers.importStep(str(path)).val()
        assert reopened.isValid() and len(reopened.Solids())==1
        error=abs(volume(reopened)-v)
        # Source spline integration is checked by a converged independent
        # method when ordinary adaptive integration is numerically unstable.
        assert error<max(.1,v*.001),(name,error,v)
        cq.exporters.export(s,str(OUT/'stl'/(name+'.stl')),tolerance=.1,angularTolerance=.08)
        # Broad outboard side toward the bed. The stepped seam and knee boss
        # require localized supports; inspect these starting orientations.
        printed=s.rotate((0,0,0),(1,0,0),-90 if not right else 90)
        bb=printed.BoundingBox();printed=printed.translate((-bb.xmin,-bb.ymin,-bb.zmin));bb=printed.BoundingBox()
        cq.exporters.export(printed,str(OUT/'print-stl'/(name+'.stl')),tolerance=.1,angularTolerance=.08)
        exports.append({'part':name,'valid_solid':True,'volume_roundtrip_error_mm3':error,'print_size_mm':[bb.xlen,bb.ylen,bb.zlen]})
        print('Export',name,round(v),round(error,4),flush=True)
data['parameters'].update(compact_thigh_cap_y_mm=94,compact_thigh_motor_cup_start_y_mm=9)
data['status']='Integrated motor-cup thigh candidate; generated comparison model, not a native Fusion migration target.'
data['source_model_sha256']=hashlib.sha256(raw).hexdigest()
encoded=json.dumps(data,separators=(',',':')).encode();stamp=hashlib.sha256(encoded).hexdigest();(OUT/'model.json').write_bytes(encoded)
(OUT/'step-roundtrip.json').write_text(json.dumps({'model_sha256':stamp,'parts':exports},indent=2))
spec=importlib.util.spec_from_file_location('viewer_check',ROOT.parents[2]/'viewer/serve.py');view=importlib.util.module_from_spec(spec);spec.loader.exec_module(view)
current,previous=view.Engine(OUT/'model.json'),view.Engine(BASE/'model.json')
def compare(q):
    a={tuple(p) for p in current.check(q)['pairs']};z={tuple(p) for p in previous.check(q)['pairs']}
    return sorted(a),sorted(a-z),sorted(z-a)
rows=[]
for row in json.loads((BASE/'audit.json').read_text())['motion_samples']:
    pairs,added,removed=compare(row['angles']);rows.append({'pose':row['pose'],'angles':row['angles'],'hits':pairs,'added_pairs':added,'removed_pairs':removed,'passed':not pairs})
fold=[]
for knee in range(-156,-47):
    pairs,added,removed=compare(uniform([0,30,knee]));fold.append({'knee_pitch_deg':knee,'pairs':pairs,'added_pairs':added,'removed_pairs':removed})
(OUT/'audit.json').write_text(json.dumps({'model_sha256':stamp,'motion_samples':rows,'scope':'Rigid source comparison at named and coupled joint samples; inherited extreme-pose collisions remain visible.'},indent=2))
(OUT/'limb-folding.json').write_text(json.dumps({'model_sha256':stamp,'knee_samples':fold,'new_collision_sample_count':sum(bool(r['added_pairs']) for r in fold),'scope':'One-degree knee samples, hip30/roll0; not a continuous full-body clearance proof.'},indent=2))
report={'model_sha256':stamp,'source_model_sha256':hashlib.sha256(raw).hexdigest(),'cap_reduction_mm':6,'root_start_before_mm':47,'root_start_after_mm':9,'parts':comparisons,'whole_robot_mass_change_kg':sum(r['mass_change_g'] for r in comparisons)*4/1000,'added_pose_pairs':[(r['pose'],r['added_pairs']) for r in rows if r['added_pairs']],'added_knee_pairs':[(r['knee_pitch_deg'],r['added_pairs']) for r in fold if r['added_pairs']],'manufacturing_scope':'Two structural thigh halves. Existing metal mounting plate, compression ties and bearing/axle stack retained. Printed strength, cooling and physical assembly remain unqualified.'}
(OUT/'compact-thigh-review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
baseline_samples={r['pose']:r['hits'] for r in json.loads((BASE/'audit.json').read_text())['motion_samples']}
report['previously_clear_poses_lost']=[r['pose'] for r in rows if not baseline_samples[r['pose']] and r['hits']]
report['print_orientation_note']='Broad side surfaces toward the bed. The stepped seam and curved knee boss need localized supports; oriented STL files require slicer review.'
(OUT/'compact-thigh-review.json').write_text(json.dumps(report,indent=2))
