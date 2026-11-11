"""Publish the closed thigh and remove retired chassis mounting remnants."""
import hashlib,importlib.util,json,shutil
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
import closed_thigh as design
import build as b
from export_closed_mesh import closed_mesh
from kinematics import ROOT,uniform

BASE=design.BASE;OUT=ROOT/'output/closed-thigh-work';OUT.mkdir(exist_ok=True)
for sub in ['step','stl']:shutil.copytree(BASE/sub,OUT/sub,dirs_exist_ok=True)
(OUT/'reference-brep').mkdir(exist_ok=True)
raw=(BASE/'model.json').read_bytes();data=json.loads(raw);changes=[];exports=[]
def volume(s):
    p=GProp_GProps();BRepGProp.VolumePropertiesGK_s(s.wrapped,p,1e-9,True,True);return p.Mass()
def replace(key,s,note):
    assert s.isValid() and len(s.Solids())==1,key
    parts=[p for p in data['parts'] if p['mesh']==key];previous=sum(p['mass_kg'] for p in parts)
    v=volume(s);bb=s.BoundingBox()
    for p in parts:p.update(volume_mm3=v,mass_kg=v*b.DENSITY[p['material']],com_mm=list(s.Center().toTuple()),bounds_mm=[bb.xlen,bb.ylen,bb.zlen],note=note)
    s.exportBrep(str(OUT/'reference-brep'/(key+'.brep')))
    step,stl=OUT/'step'/(key+'.step'),OUT/'stl'/(key+'.stl')
    cq.exporters.export(s,str(step));cq.exporters.export(s,str(stl),tolerance=.08,angularTolerance=.1)
    mesh,mesh_check=closed_mesh(step,stl,v);data['meshes'][key]={'vertices':mesh.vertices.tolist(),'faces':mesh.faces.tolist()}
    restored=cq.importers.importStep(str(step)).val();error=abs(volume(restored)-v)
    assert restored.isValid() and len(restored.Solids())==1 and error<max(.1,v*1e-4),(key,error)
    exports.append({'part':key,'closed_solids':1,'roundtrip_volume_error_mm3':error,'mesh':mesh_check})
    changes.append({'part':key,'mass_change_kg':sum(p['mass_kg'] for p in parts)-previous,'volume_mm3':v})
    print('Export',key,round(v),flush=True)
s=design.thigh(True)
for right in [False,True]:
    replace('thigh_outer'+('_right' if right else ''),s.mirror('XZ') if right else s,
        'Continuous front wall and smooth outer face. The conservative full-sphere foot cut is omitted; validate against the modeled boot over the complete knee range. Original motor, crank, pushrod and bearing interfaces; two structural halves. Strength and production fits remain unqualified.')
for side in [-1,1]:replace('chassis_beam_'+str(side*102),design.rail(side),
    'Tapped metal motor rail with open rounded motor windows. Retired cover-boss roots, their pilot holes and obsolete top-flange tie holes are removed. Current cover and tie mounting datums retained. Frame strength and machining access remain unqualified.')
data['parameters'].update(thigh_spherical_foot_relief=False,thigh_foot_clearance_required_mm=1.5,chassis_retired_mounts_removed=True)
data['status']='Closed structural thigh candidate checked against the modeled boot. Continuous thigh front wall, retained service holes and no cosmetic waist depression. Frame remnant cleanup. Strength, actual boot behavior and machining access remain unqualified.'
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
    poses.append({'pose':row['pose'],'angles':row['angles'],'hits':hits,'added_pairs':added,'removed_pairs':removed,'source_hit_count':count,'passed':not hits})
(OUT/'audit.json').write_text(json.dumps({'model_sha256':stamp,'motion_samples':poses,
    'scope':'Rigid-part samples including modeled boot. Mating and fixed body/frame groups excluded; independent interface and service checks required. Manufacturing tolerances, flexible cables and loaded deflection unqualified.'},indent=2))
fold=[]
for knee in range(-156,-47):
    hits,added,removed,count=compare(uniform([0,30,knee]));fold.append({'knee_pitch_deg':knee,'pairs':hits,'added_pairs':added,'removed_pairs':removed})
(OUT/'limb-folding.json').write_text(json.dumps({'model_sha256':stamp,'knee_samples':fold,'clear_samples':sum(not r['pairs'] for r in fold)},indent=2))
report={'model_sha256':stamp,'source_model_sha256':hashlib.sha256(raw).hexdigest(),'changes':changes,
    'mass_change_kg':sum(r['mass_change_kg'] for r in changes),'previously_clear_poses_lost':[r['pose'] for r in poses if not r['source_hit_count'] and r['hits']],
    'added_motion_pairs':[{'pose':r['pose'],'pairs':r['added_pairs']} for r in poses if r['added_pairs']],
    'mechanism':'Original170mm link,28mm cranks, motor axes, pushrod, boot, bearings and nominal knee limits retained. The omitted spherical relief changes only the thigh wall; ordinary screw access and axle bores remain.',
    'scope':data['status']}
(OUT/'closed-thigh-review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
