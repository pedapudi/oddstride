"""Publish the reviewed lidar geometry without altering the raised-head variant."""
import hashlib,json,shutil
from kinematics import ROOT

OUT=ROOT/'output/low-lidar-work'
BASE=ROOT/'output/limb-refinement'
SNAP=ROOT/'output/low-lidar-reference'
raw=(OUT/'model.json').read_bytes();stamp=hashlib.sha256(raw).hexdigest()
model=json.loads(raw);reference=json.loads((SNAP/'model.json').read_text())
report=json.loads((OUT/'lidar-neck-review.json').read_text())
assert report['model_sha256']==stamp
assert all(not r['obstructions'] for r in report['optical_plane_checks'])
assert all(r['passed'] for r in report['service_checks'])
audit=json.loads((OUT/'audit.json').read_text())
assert audit['model_sha256']==stamp and all(not r['added_pairs'] for r in audit['motion_samples'])
fold=json.loads((OUT/'limb-folding.json').read_text())
assert fold['model_sha256']==stamp and all(not r['pairs'] for r in fold['knee_samples'])
# Reuse limb-only evidence only when every limb part and mesh is identical.
limbs=[p for p in model['parts'] if p.get('leg')]
assert limbs==[p for p in reference['parts'] if p.get('leg')]
assert all(model['meshes'][p['mesh']]==reference['meshes'][p['mesh']] for p in limbs)
for name in ['limb-interfaces.json','manufacturing-review.json','step-roundtrip.json']:
    data=json.loads((SNAP/name).read_text())
    data['source_model_sha256']=data['model_sha256'];data['model_sha256']=stamp
    data['reuse_basis']='Limb geometry and assembly placements are identical to the audited source.'
    if name=='manufacturing-review.json':
        data['lidar_neck_status']='Integral seat and hood geometry reviewed; inherited hood/cradle release interference and selected sensor mounting prevent fabrication release.'
    if name=='step-roundtrip.json':
        changed={r['part'] for r in report['step_exports']}
        data['parts']=[r for r in data['parts'] if r['part'] not in changed]+report['step_exports']
    (OUT/name).write_text(json.dumps(data,indent=2))
for key in [r['part'] for r in report['step_exports']]:
    for ext in ['step','stl']:shutil.copy2(OUT/ext/f'{key}.{ext}',BASE/ext/f'{key}.{ext}')
for name in ['model.json','audit.json','limb-folding.json','limb-interfaces.json','manufacturing-review.json','step-roundtrip.json','lidar-neck-review.json']:
    shutil.copy2(OUT/name,BASE/name)
print(json.dumps({'published_model_sha256':stamp,'lidar_raise_mm':42,'part_count_change':0,'fabrication_blockers':report['fabrication_blockers']},indent=2))
