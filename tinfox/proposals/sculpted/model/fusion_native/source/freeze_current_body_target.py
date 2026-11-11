"""Freeze the authorized chassis revision without changing the protected limb target."""
import gzip,hashlib,json,shutil,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];source=ROOT.parent/'output/cohesive-chassis-work';sha='b6de90815c773509d8f9710feea44df1372e411e14cb830df839fd6190588693';raw=(source/'model.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==sha;model=json.loads(raw);inventory=json.loads((source/'reference-snapshot.json').read_text());assert inventory['model_sha256']==sha
keys=['body_center_0','belly_center_0','chassis_beam_102','chassis_beam_-102','chassis_crossmember_121','chassis_crossmember_-121'];hardware=[p['name'] for p in model['parts'] if p['name'].startswith(('body_service_screw_','chassis_tie_bolt_'))];folder=ROOT/'snapshots/body-revisions'/sha;folder.mkdir(parents=True,exist_ok=True);files={}
for key in keys+hardware:
 files[key]={}
 for sub,suffix in [('step','.step'),('stl','.stl'),('reference-brep','.brep')]:
  rel=f'{sub}/{key}{suffix}';file=source/rel
  if not file.exists():continue
  digest=hashlib.sha256(file.read_bytes()).hexdigest();assert inventory['files'].get(rel)==digest,(rel,digest,inventory['files'].get(rel));dest=folder/rel;dest.parent.mkdir(exist_ok=True);shutil.copyfile(file,dest);files[key][sub]={'path':str(dest.relative_to(ROOT)),'sha256':digest}
for name in ['cohesive_chassis.py','build.py','kinematics.py','parameters.json']:
 src=ROOT.parent/name;dst=folder/'source'/name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(src,dst)
(folder/'model.json.gz').write_bytes(gzip.compress(raw,mtime=0));shutil.copyfile(source/'reference-snapshot.json',folder/'reference-snapshot.json')
result={'updated_utc':datetime.datetime.now(datetime.UTC).isoformat(),'source_model_sha256':sha,'reference_model':str((folder/'model.json.gz').relative_to(ROOT)),'custom_keys':keys,'reference_hardware_keys':hardware,'removed_reference_keys':[f'chassis_tie_nut_{x}_{side}_{dx}' for x in [-121,121] for side in [-1,1] for dx in [-3,3]]+['sensor_root_nut_0','sensor_root_nut_1'],'files':files,'sources':{name:hashlib.sha256((folder/'source'/name).read_bytes()).hexdigest() for name in ['cohesive_chassis.py','build.py','kinematics.py','parameters.json']},'status':'Authorized native body migration target; no source-of-truth promotion. New thigh geometry is excluded pending a separate target.'};(ROOT/'manifests/current-body-target.json').write_text(json.dumps(result,indent=2));print({'custom_parts':len(keys),'reference_parts':len(hardware),'target':sha})
