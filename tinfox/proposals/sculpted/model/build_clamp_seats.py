"""Publish structural shell washer seats and retain the closed foot-clearance wall."""
import hashlib,importlib.util,json,shutil
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
import clamp_seats as design
import build as b
from export_closed_mesh import closed_mesh
from kinematics import ROOT,uniform

BASE=design.BASE;OUT=ROOT/'output/clamp-seat-work';OUT.mkdir(exist_ok=True)
for sub in ['step','stl']:shutil.copytree(BASE/sub,OUT/sub,dirs_exist_ok=True)
(OUT/'reference-brep').mkdir(exist_ok=True)
raw=(BASE/'model.json').read_bytes();data=json.loads(raw);changes=[];exports=[]
clamps=[('thigh',0,(-36,-66)),('thigh',1,(5,-70)),('shin',37,(2,-30)),('shin',105,(2,-105))]
washers={}
for kind,index,center in clamps:
    for outer in [False,True]:
        key=f'{kind}_clamp_washer_{index}_'+('outer' if outer else 'inner');washers[key]=(center,outer)
        for leg in ['FL','FR','RL','RR']:
            template=dict(next(p for p in data['parts'] if p['name']==leg+('_thigh_clamp_nut_0' if kind=='thigh' else '_shin_clamp_nut_37')))
            template.update(name=leg+'_'+key,mesh=key+('_right' if leg.endswith('R') else ''),volume_mm3=0,mass_kg=0,bounds_mm=[0,0,0])
            data['parts'].append(template)

def volume(s):
    p=GProp_GProps();BRepGProp.VolumePropertiesGK_s(s.wrapped,p,1e-9,True,True);return p.Mass()
def replace(key,s,note,step_source=None):
    assert s.isValid() and len(s.Solids())==1,key
    parts=[p for p in data['parts'] if p['mesh']==key];previous=sum(p['mass_kg'] for p in parts)
    v=volume(s);bb=s.BoundingBox()
    for p in parts:p.update(volume_mm3=v,mass_kg=v*b.DENSITY[p['material']],com_mm=list(s.Center().toTuple()),bounds_mm=[bb.xlen,bb.ylen,bb.zlen],note=note)
    s.exportBrep(str(OUT/'reference-brep'/(key+'.brep')))
    step,stl=OUT/'step'/(key+'.step'),OUT/'stl'/(key+'.stl')
    if step_source:shutil.copy2(step_source,step)
    else:cq.exporters.export(s,str(step))
    cq.exporters.export(s,str(stl),tolerance=.08,angularTolerance=.1)
    mesh,mesh_check=closed_mesh(step,stl,v);data['meshes'][key]={'vertices':mesh.vertices.tolist(),'faces':mesh.faces.tolist()}
    restored=cq.importers.importStep(str(step)).val();error=abs(volume(restored)-v)
    assert restored.isValid() and len(restored.Solids())==1 and error<max(.1,v*1e-4),(key,error)
    exports.append({'part':key,'closed_solids':1,'roundtrip_volume_error_mm3':error,'mesh':mesh_check})
    changes.append({'part':key,'mass_change_kg':sum(p['mass_kg'] for p in parts)-previous,'volume_mm3':v})
    print('Export',key,round(v),flush=True)
for kind,fn in [('thigh',design.thigh),('shin',design.shin)]:
    for outer in [False,True]:
        s=fn(outer);key=kind+('_outer' if outer else '_inner')
        for right in [False,True]:replace(key+('_right' if right else ''),s.mirror('XZ') if right else s,
            'Two structural halves with open 12.4 mm washer-access counterbores and annular plastic bearing floors. Common M4 x 25 screws, 18 mm metal sleeves, 12 x 4.3 x 1 mm washers and ordinary M4 nuts. Thigh retains continuous foot-clearance wall; rear contour broadens smoothly for counterbore support. Controlled compression-stack tolerances, preload, creep and structural load capacity remain unqualified.')
hardware=['bolt_0','bolt_1','thigh_clamp_nut_0','thigh_clamp_nut_1',
    'shin_clamp_bolt_37','shin_clamp_bolt_105','shin_clamp_nut_37','shin_clamp_nut_105']
for key in hardware:
    s=design.shifted_hardware(key)
    for right in [False,True]:replace(key+('_right' if right else ''),s.mirror('XZ') if right else s,
        'Standard M4 x 25 button-head screw or M4 hex nut shifted for the paired 1 mm large-series washers. Nominal nut engagement 3.2 mm and thread projection 1.8 mm. Exact purchased dimensions and tightening/preload remain unverified.')
for key,(center,outer) in washers.items():
    s=design.washer(center,outer)
    for right in [False,True]:replace(key+('_right' if right else ''),s.mirror('XZ') if right else s,
        'Common large-series M4 flat washer, nominal 12 mm OD x 4.3 mm ID x 1 mm thickness. It spans the 8.2 mm sleeve bore and bears on plastic outside the metal limiter. Nominal reference envelope; actual DIN 9021 tolerances, stock and compression-stack fit require verification.')
for side in [-1,1]:
    key='chassis_beam_'+str(side*102);file=ROOT/'fusion_native/snapshots/body-cleanup-target'/(key+'.step')
    s=cq.importers.importStep(str(file)).val();replace(key,s,
        'Tapped metal rail. Retired cover roots and old tie bores removed locally; current cover gussets and lower diaphragm ledges retained. New tie seating cuts are limited to the mating interfaces. Load and machining qualification pending.',step_source=file)
data['parameters'].update(clamp_washer_od_mm=12,clamp_washer_id_mm=4.3,clamp_washer_thickness_mm=1,
    clamp_counterbore_diameter_mm=12.4,clamp_inner_floor_y_mm=58,clamp_outer_floor_y_mm=76,
    clamp_limiter_length_mm=18,clamp_nominal_free_span_mm=18,clamp_compression_stack_qualified=False,
    thigh_rear_flare_mm=design.REAR_FLARE_MM)
data['status']='Structural shell washer-seat candidate. Continuous thigh wall with open counterbores and metal compression sleeves. Nominal bearing footprints require audit; controlled stack tolerance, preload, creep, load capacity and CNC access remain unqualified.'
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
    'scope':'Nominal rigid parts including washer references. Listed mating/body-frame groups excluded; seating, tool and removal checks are separate. Tolerances, flexible cables and loaded deflection unqualified.'},indent=2))
fold=[]
for knee in range(-156,-47):
    hits,added,removed,count=compare(uniform([0,30,knee]));fold.append({'knee_pitch_deg':knee,'pairs':hits,'added_pairs':added,'removed_pairs':removed})
(OUT/'limb-folding.json').write_text(json.dumps({'model_sha256':stamp,'knee_samples':fold,'clear_samples':sum(not r['pairs'] for r in fold)},indent=2))
report={'model_sha256':stamp,'source_model_sha256':hashlib.sha256(raw).hexdigest(),'changes':changes,
    'mass_change_kg':sum(r['mass_change_kg'] for r in changes),'washers_total':32,
    'previously_clear_poses_lost':[r['pose'] for r in poses if not r['source_hit_count'] and r['hits']],
    'added_motion_pairs':[{'pose':r['pose'],'pairs':r['added_pairs']} for r in poses if r['added_pairs']],
    'scope':data['status']}
(OUT/'clamp-seat-review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
