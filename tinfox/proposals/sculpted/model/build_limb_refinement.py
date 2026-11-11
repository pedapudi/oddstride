"""Publish a limb-only candidate without changing the reference body or sensor pod."""
import hashlib,importlib.util,json,os,shutil
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
import cohesive_limb as cohesive
import build as b
from kinematics import ROOT,P,uniform

BASE=ROOT/'output/integrated-candidate';OUT=ROOT/'output'/os.environ.get('TINFOX_LIMB_OUTPUT','limb-refinement')
for folder in [OUT,OUT/'step',OUT/'stl']:folder.mkdir(exist_ok=True)
raw=(BASE/'model.json').read_bytes();model=json.loads(raw);P.update(model['parameters'])
# Preserve the accepted body revision while regenerating the limbs. The
# sensor saddle has a different part set from the frozen integrated source.
published=ROOT/'output/limb-refinement'
body_revision=json.loads((published/'model.json').read_text()) if (published/'model.json').exists() else {}
preserve_saddle='sensor_saddle_split_z_mm' in body_revision.get('parameters',{})
if preserve_saddle:
    body_parts=[p for p in body_revision['parts'] if not p.get('leg')]
    model['parts']=[p for p in model['parts'] if p.get('leg')]+body_parts
    for p in body_parts:
        model['meshes'][p['mesh']]=body_revision['meshes'][p['mesh']]
        for sub,ext in [('step','step'),('stl','stl')]:
            src=published/sub/f"{p['mesh']}.{ext}";dst=OUT/sub/src.name
            if src.exists() and src.resolve()!=dst.resolve():shutil.copy2(src,dst)
    model['parameters'].update({k:v for k,v in body_revision['parameters'].items() if k.startswith(('low_lidar_','sensor_'))})
comparisons=[]
roundtrips=[]
def precise_volume(shape):
    props=GProp_GProps()
    BRepGProp.VolumeProperties_s(shape.wrapped,props,1e-9,True,False)
    return props.Mass()
def verify_step(key,shape):
    exported=cq.importers.importStep(str(OUT/'step'/(key+'.step'))).val()
    expected=precise_volume(shape);error=abs(precise_volume(exported)-expected)
    assert exported.isValid() and len(exported.Solids())==1,('STEP must reopen as one valid solid',key)
    assert error<max(.05,expected*1e-5),('STEP volume changed',key,error)
    roundtrips.append({'part':key,'closed_solids':len(exported.Solids()),'volume_error_mm3':error})
for kind,fn in [('thigh',cohesive.thigh),('shin',cohesive.shin)]:
    for outer in [False,True]:
        shape=fn(outer);key=kind+('_outer' if outer else '_inner')
        old=cq.importers.importStep(str(BASE/'step'/(key+'.step'))).val()
        assert shape.isValid() and len(shape.Solids())==1,key
        row={'part':key,'volume_before_mm3':old.Volume(),'volume_after_mm3':shape.Volume(),
             'mass_change_g':(shape.Volume()-old.Volume())*b.DENSITY['petg']*1000}
        if kind=='shin':
            bore=b.cyl(13.999,8.998 if outer else 10.998,(0,77.001 if outer else 50.001,0))
            row['bearing_bore_intrusion_mm3']=shape.intersect(bore).Volume()
            row['extraction_hole_intrusion_mm3']=[shape.intersect(b.cyl(1.299,15.998,(x,61.001,0))).Volume() for x in [-12.7,12.7]]
            assert row['bearing_bore_intrusion_mm3']<.001
            assert max(row['extraction_hole_intrusion_mm3'])<.001
        comparisons.append(row)
        for right in [False,True]:
            s=shape.mirror('XZ') if right else shape;k=key+('_right' if right else '')
            vertices,faces=s.tessellate(.12,.1);bb=s.BoundingBox()
            model['meshes'][k]={'vertices':[list(v.toTuple()) for v in vertices],'faces':[list(f) for f in faces]}
            for p in model['parts']:
                if p['mesh']==k:p.update(volume_mm3=s.Volume(),mass_kg=s.Volume()*b.DENSITY[p['material']],com_mm=list(s.Center().toTuple()),bounds_mm=[bb.xlen,bb.ylen,bb.zlen],note='Shared clamshell silhouette and tangent bearing-to-pushrod crown. Structural halves retain bearing datums and extraction access. See interface and folding audits before fabrication or choosing operating limits.')
            cq.exporters.export(s,str(OUT/'step'/(k+'.step')))
            verify_step(k,s)
            cq.exporters.export(s,str(OUT/'stl'/(k+'.stl')),tolerance=.12,angularTolerance=.1)
        print(key,'valid',row,flush=True)
def replace(key,shape,note):
    vertices,faces=shape.tessellate(.12,.1);bb=shape.BoundingBox()
    model['meshes'][key]={'vertices':[list(v.toTuple()) for v in vertices],'faces':[list(f) for f in faces]}
    for part in model['parts']:
        if part['mesh']==key:part.update(volume_mm3=shape.Volume(),mass_kg=part['mass_kg'] if key.startswith('bearing_') or part['material']=='envelope' else shape.Volume()*b.DENSITY[part['material']],com_mm=list(shape.Center().toTuple()),bounds_mm=[bb.xlen,bb.ylen,bb.zlen],note=note)
    cq.exporters.export(shape,str(OUT/'step'/(key+'.step')))
    verify_step(key,shape)
    cq.exporters.export(shape,str(OUT/'stl'/(key+'.stl')),tolerance=.12,angularTolerance=.1)
for front in [1,-1]:
    shape=cohesive.carrier(front)
    for right in [False,True]:
        replace('motor_carrier_'+str(front)+('_right' if right else ''),shape.mirror('XZ') if right else shape,'Shallow rounded bridge relief gives the rotating pod-tie screw tips nominal clearance without changing fastener length or motor datums.')
for key in ['sleeve_0','bolt_0','thigh_clamp_nut_0']:
    shape=cq.importers.importStep(str(BASE/'step'/(key+'.step'))).val().translate((2,0,0))
    for right in [False,True]:
        replace(key+('_right' if right else ''),shape.mirror('XZ') if right else shape,'Thigh clamp moved into the shared broad housing-to-limb root; original fastener and sleeve sizes retained.')
for key,shape in cohesive.bearing_revisions().items():
    for right in [False,True]:
        replace(key+('_right' if right else ''),shape.mirror('XZ') if right else shape,'Bearings repositioned inside the existing shin width; 16 mm inner-race spacer. Complete bearing seats and solid axial shoulders remain outside the pushrod channel.')
model['parameters'].update(cohesive.geometry_parameters())
import low_lidar_neck
if not preserve_saddle:
    for key,shape in low_lidar_neck.parts().items():
        replace(key,shape,'Integral raised lidar neck candidate. Seat Z94, nominal scan band Z98–116. Selected sensor mounting and hood/cradle disassembly require qualification.')
    model['parameters'].update(low_lidar_neck.parameters())
model['status']='Limb refinement with the published low-profile body; no native Fusion source-of-truth change.'
model['source_model_sha256']=hashlib.sha256(raw).hexdigest()
encoded=json.dumps(model,separators=(',',':')).encode();stamp=hashlib.sha256(encoded).hexdigest();(OUT/'model.json').write_bytes(encoded)
(OUT/'step-roundtrip.json').write_text(json.dumps({'model_sha256':stamp,'parts':roundtrips,'scope':'Every revised STEP reimported as one valid closed solid with bounded volume error.'},indent=2))
spec=importlib.util.spec_from_file_location('review',ROOT.parents[2]/'viewer/serve.py');review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
current=review.Engine(OUT/'model.json');previous=review.Engine(BASE/'model.json')
changed={p['name'] for p in model['parts'] if any(p['mesh'].startswith(k) for k in ['thigh_inner','thigh_outer','shin_inner','shin_outer'])}
def compare(q):
    new={tuple(p) for p in current.check(q)['pairs']};old={tuple(p) for p in previous.check(q)['pairs']}
    return sorted(new),sorted(new-old),sorted(old-new)
motion=[]
for row in json.loads((BASE/'audit.json').read_text())['motion_samples']:
    hits,added,removed=compare(row['angles']);motion.append({**row,'hits':hits,'added_pairs':added,'removed_pairs':removed,'passed':not hits})
fold=[]
for knee in range(-156,-47):
    q=uniform([0,30,knee]);hits,added,removed=compare(q)
    fold.append({'knee_pitch_deg':knee,'added_pairs':added,'removed_pairs':removed,
                 'limb_pairs':[p for p in hits if all(current.parts[n].get('leg')=='FL' for n in p) and any(n in changed for n in p)]})
report={'model_sha256':stamp,'motion_samples':motion,'scope':'Full physical-part collision checks at the listed poses. Existing reference collisions remain visible. No strength, tolerance, flexible-cable or thermal qualification.'}
(OUT/'audit.json').write_text(json.dumps(report,indent=2))
(OUT/'limb-folding.json').write_text(json.dumps({'model_sha256':stamp,'part_comparisons':comparisons,'knee_samples':fold,'new_collision_sample_count':sum(bool(r['added_pairs']) for r in fold),'scope':'Knee sampled at one-degree steps from -156 to -48 degrees, hip pitch 30 degrees and roll zero. This is a sampled folding check, not an unrestricted whole-robot motion envelope.'},indent=2))
print('NEW POSE PAIRS',[(r['pose'],r['added_pairs']) for r in motion if r['added_pairs']],flush=True)
print('NEW FOLDING PAIRS',[(r['knee_pitch_deg'],r['added_pairs']) for r in fold if r['added_pairs']],flush=True)
