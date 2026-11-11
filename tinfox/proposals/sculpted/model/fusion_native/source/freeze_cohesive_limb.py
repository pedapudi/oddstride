"""Freeze the authorized cohesive limb revision separately from original V0."""
import datetime,gzip,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];MODEL=ROOT.parent;source=MODEL/'output/low-lidar-reference';raw=(source/'model.json').read_bytes();expected='7a30dd8d92258b011e043f6fb43992ff9ac718232dd030ec2a7c79b33f68d63a';assert hashlib.sha256(raw).hexdigest()==expected
out=ROOT/'snapshots/cohesive-limb';assert not (out/'reference.json').exists(),'Frozen snapshot already exists'
for folder in ['step','stl','source','audits']:(out/folder).mkdir(parents=True,exist_ok=True)
data=json.loads(raw);names={p['mesh'] for p in data['parts'] if p.get('leg') and any(token in p['mesh'] for token in ['thigh_','shin_','motor_carrier','bearing_','knee_','input_crank','pushrod','output_pivot','connector'])};files=[]
for key in sorted(names):
 for fmt in ['step','stl']:
  path=source/fmt/f'{key}.{fmt}'
  if path.exists():
   target=out/fmt/path.name;shutil.copyfile(path,target);files.append({'path':str(target.relative_to(out)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
for path in MODEL.glob('*.py'):
 target=out/'source'/path.name;shutil.copyfile(path,target);files.append({'path':str(target.relative_to(out)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
for name in ['limb-interfaces.json','step-roundtrip.json','knee-design-review.json','limb-folding.json','manufacturing-review.json','audit.json','torques.json']:
 path=source/name
 if path.exists():shutil.copyfile(path,out/'audits'/name)
(out/'model.json.gz').write_bytes(gzip.compress(raw,mtime=0))
record={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model_sha256':expected,'authorized_scope':'Current cohesive limb native revision inside existing Leg document. Preserve original V0 archive. Candidate until shape, parameters, assembly and service gates pass.','files':files,'mesh_names':sorted(names),'instances':[p for p in data['parts'] if p.get('leg') and p['mesh'] in names],'source_of_truth_changed':False};(out/'reference.json').write_text(json.dumps(record,indent=2));print(json.dumps({'step_files':len(list((out/'step').glob('*.step'))),'stl_files':len(list((out/'stl').glob('*.stl'))),'source_files':len(list((out/'source').glob('*.py'))),'instances':len(record['instances']),'hash':expected}))
