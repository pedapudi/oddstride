"""Publish the low saddle only after optical, assembly and service gates pass."""
import hashlib,json,shutil
from kinematics import ROOT
OUT=ROOT/'output/sensor-saddle-work';BASE=ROOT/'output/limb-refinement';SNAP=ROOT/'output/sensor-saddle-reference'
raw=(OUT/'model.json').read_bytes();stamp=hashlib.sha256(raw).hexdigest();model=json.loads(raw);old=json.loads((SNAP/'model.json').read_text())
def read(name):
    d=json.loads((OUT/name).read_text());assert d['model_sha256']==stamp,name;return d
interface=read('saddle-interfaces.json');service=read('sensor-service.json');audit=read('audit.json');fold=read('limb-folding.json');review=read('lidar-neck-review.json')
assert interface['passed'] and service['passed']
assert not any(r['added_pairs'] for r in audit['motion_samples'])
assert not any(r['pairs'] for r in fold['knee_samples'])
assert not any(r['obstructions'] for r in review['optical_plane_checks'])
limbs=[p for p in model['parts'] if p.get('leg')]
assert limbs==[p for p in old['parts'] if p.get('leg')]
assert all(model['meshes'][p['mesh']]==old['meshes'][p['mesh']] for p in limbs)
for name in ['limb-interfaces.json','manufacturing-review.json','step-roundtrip.json']:
    d=json.loads((SNAP/name).read_text());d['source_model_sha256']=d['model_sha256'];d['model_sha256']=stamp
    d['reuse_basis']='All limb geometry and assembly placements are identical to the audited source.'
    if name=='manufacturing-review.json':
        d.pop('lidar_neck_status',None)
        d['parts']=[p for p in d['parts'] if p['part'] not in {r['part'] for r in review['print_parts']}]+review['print_parts']
        d['sensor_assembly']=review['assembly'];d['sensor_limits']=review['limits']
    if name=='step-roundtrip.json':
        keys={p['part'] for p in review['step_exports']}
        d['parts']=[p for p in d['parts'] if p['part'] not in keys]+review['step_exports']
    (OUT/name).write_text(json.dumps(d,indent=2))
for p in review['step_exports']:
    key=p['part']
    for ext in ['step','stl']:shutil.copy2(OUT/ext/f'{key}.{ext}',BASE/ext/f'{key}.{ext}')
for p in review['print_parts']:shutil.copy2(OUT/'print-stl'/f"{p['part']}.stl",BASE/'print-stl'/f"{p['part']}.stl")
# Retire only obsolete sensor fastener exports in the active candidate.
# The frozen reference retains these files and their original assembly.
for key in review['removed_hardware']:
    for ext in ['step','stl']:(BASE/ext/f'{key}.{ext}').unlink(missing_ok=True)
for name in ['model.json','audit.json','limb-folding.json','limb-interfaces.json','manufacturing-review.json','step-roundtrip.json','lidar-neck-review.json','saddle-interfaces.json','sensor-service.json']:
    shutil.copy2(OUT/name,BASE/name)
print(json.dumps({'model_sha256':stamp,'interface_checks':len(interface['checks']),'assembly_removal_samples':len(service['samples']),'fold_samples':len(fold['knee_samples']),'revised_exports':len(review['step_exports'])},indent=2))
