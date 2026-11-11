"""Apply a checked limb revision to both current body variants."""
import copy,hashlib,importlib.util,json,shutil
from pathlib import Path
import cadquery as cq
from kinematics import ROOT,uniform
WORK=ROOT/'output/cohesive-limb-work'
LOW=ROOT/'output/limb-refinement';HIGH=ROOT/'output/shoulder-head-prototype'
spec=importlib.util.spec_from_file_location('review',ROOT.parents[2]/'viewer/serve.py');review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
raw=(WORK/'model.json').read_bytes();stamp=hashlib.sha256(raw).hexdigest();limb=json.loads(raw)
interfaces=json.loads((WORK/'limb-interfaces.json').read_text())
assert interfaces['model_sha256']==stamp and interfaces['passed'],'Limb interface audit is not current/passing'
roundtrips=json.loads((WORK/'step-roundtrip.json').read_text())
assert roundtrips['model_sha256']==stamp and all(r['closed_solids']==1 for r in roundtrips['parts'])
fold=json.loads((WORK/'limb-folding.json').read_text())
assert fold['model_sha256']==stamp and fold['new_collision_sample_count']==0
lowaudit=json.loads((WORK/'audit.json').read_text())
assert all(not r['hits'] for r in lowaudit['motion_samples'] if r['pose'] in ['stand','studio','raised','crouch','fold'])
# Publishable print orientations keep motor, axle and bearing axes vertical.
print_rows=[];print_folder=WORK/'print-stl';print_folder.mkdir(exist_ok=True)
for kind in ['thigh','shin']:
 for outer in [False,True]:
  for right in [False,True]:
   key=kind+('_outer' if outer else '_inner')+('_right' if right else '')
   s=cq.importers.importStep(str(WORK/'step'/(key+'.step'))).val()
   angle=(-90 if outer else 90)*(-1 if right else 1)
   upright=s.rotate((0,0,0),(1,0,0),angle);bb=upright.BoundingBox()
   upright=upright.translate((-bb.xmin,-bb.ymin,-bb.zmin));bb=upright.BoundingBox()
   assert bb.xlen<325 and bb.ylen<320 and bb.zlen<325
   cq.exporters.export(upright,str(print_folder/(key+'.stl')),tolerance=.12,angularTolerance=.1)
   print_rows.append({'part':key,'orientation':'Exterior face down; open cavity up.','build_envelope_mm':[bb.xlen,bb.ylen,bb.zlen],'solid_count':len(s.Solids()),'face_count':len(s.Faces()),'notes':'Vertical bearing/axle bores. Inspect supports at rounded perimeter transitions and local counterbore roofs in the slicer; these exports are not qualified print settings.'})
manufacturing={'model_sha256':stamp,'parts':print_rows,'structural_halves_per_limb':4,'shared_split_plane_y_mm':67,'status':'Geometry review prototype; not released for manufacture.','assembly':['Bench-fit the bearings and spacers before installing the motors.','Install the hip hub, three metal tie sleeves and knee stator plate; verify actuator thread engagement and clamp preload separately.','Install the pushrod bushings, shoulder screws and captured nuts with the shells open.','Seat each shin bearing in its complete circular bore. Close the shin halves around the spacer and metal clamp sleeves.','Fit the shin between the thigh bearing stops, insert the knee axle sleeve and through-bolt, then close the thigh.','For bearing service, remove the knee axle and open the two structural halves. Use the rear extraction holes to press on the outer race.'],'limits':['Printed strength, fatigue, motor heat, clamp preload, actual press fits and accumulated tolerances remain unqualified.','Metal parts need wall/pocket optimization and a supplier tool-access review before CNC ordering.','The nominal foot and motor envelopes are retained; their final retention and wiring details require hardware selection.']}
(WORK/'manufacturing-review.json').write_text(json.dumps(manufacturing,indent=2))
# Keep the body/head geometry exactly as published; transfer the complete leg
# set so carriers and relocated clamp hardware cannot diverge between variants.
highraw=(HIGH/'model.json').read_bytes();high=json.loads(highraw)
previous_high_hash=hashlib.sha256(highraw).hexdigest()
newlegs={p['name']:p for p in limb['parts'] if p.get('leg')}
assert set(newlegs)=={p['name'] for p in high['parts'] if p.get('leg')}
high['parts']=[copy.deepcopy(newlegs[p['name']]) if p.get('leg') else p for p in high['parts']]
high['parameters'].update({k:v for k,v in limb['parameters'].items() if k.startswith('knee_')})
for p in newlegs.values():high['meshes'][p['mesh']]=limb['meshes'][p['mesh']]
high['meshes']={k:v for k,v in high['meshes'].items() if k in {p['mesh'] for p in high['parts']}}
high['limb_source_model_sha256']=stamp;high.setdefault('previous_body_variant_sha256',previous_high_hash)
encoded=json.dumps(high,separators=(',',':')).encode();highhash=hashlib.sha256(encoded).hexdigest()
stage=ROOT/'output/shoulder-limb-work';stage.mkdir(exist_ok=True);(stage/'model.json').write_bytes(encoded)
engine=review.Engine(stage/'model.json');previous=review.Engine(HIGH/'model.json');motions=[]
for row in lowaudit['motion_samples']:
 result=engine.check(row['angles']);old=previous.check(row['angles'])
 hits=result['pairs'];before={tuple(p) for p in old['pairs']}
 motions.append({'pose':row['pose'],'angles':row['angles'],'hits':hits,'added_pairs':[p for p in hits if tuple(p) not in before],'passed':not hits})
assert all(not r['hits'] for r in motions if r['pose'] in ['stand','studio','raised','crouch'])
highfold=[]
for knee in range(-156,-47):
 q=uniform([0,30,knee]);result=engine.check(q)
 highfold.append({'knee_pitch_deg':knee,'pairs':result['pairs']})
assert all(not r['pairs'] for r in highfold),'Raised-head folding regression'
# Only after both variants pass the specified gates are the visible files updated.
for target in [LOW,HIGH]:
 for sub in ['step','stl','print-stl']:
  (target/sub).mkdir(exist_ok=True)
  for p in (WORK/sub).iterdir():
   if p.is_file():shutil.copy2(p,target/sub/p.name)
for name in ['model.json','audit.json','limb-folding.json','limb-interfaces.json','manufacturing-review.json','step-roundtrip.json','knee-design-review.json']:
 shutil.copy2(WORK/name,LOW/name)
(HIGH/'model.json').write_bytes(encoded)
(HIGH/'audit.json').write_text(json.dumps({'model_sha256':highhash,'motion_samples':motions,'scope':lowaudit['scope']},indent=2))
for name in ['limb-interfaces.json','manufacturing-review.json','step-roundtrip.json']:
 report=json.loads((WORK/name).read_text());report['limb_source_model_sha256']=stamp;report['model_sha256']=highhash;(HIGH/name).write_text(json.dumps(report,indent=2))
(HIGH/'limb-folding.json').write_text(json.dumps({'model_sha256':highhash,'knee_samples':highfold,'scope':'Whole raised-head assembly, knee -156 to -48 degrees in one-degree steps at hip pitch 30 and roll zero. No continuous or loaded-motion claim.'},indent=2))
print(json.dumps({'low_profile_sha256':stamp,'raised_head_sha256':highhash,'interface_checks':len(interfaces['checks']),'fold_samples_per_variant':len(highfold),'print_parts':len(print_rows)},indent=2))
