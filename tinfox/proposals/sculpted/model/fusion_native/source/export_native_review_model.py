"""Build a review candidate from the exact native inputs used by the motion audit."""
import datetime,gzip,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
target=json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low']
audit=json.loads((ROOT/'audits/whole-native-robot-motion-service.json').read_text());assert audit['passed']
raw=gzip.decompress((ROOT/target['reference_model']).read_bytes());assert hashlib.sha256(raw).hexdigest()==audit['source_model_sha256'];model=json.loads(raw)
for key,row in audit['native_inputs'].items():
 path=ROOT/row['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
 if row['mesh_source']=='Fusion meshManager':
  path=ROOT/'exports/native-shin-outer-right-mesh.json.gz';assert hashlib.sha256(path.read_bytes()).hexdigest()==row['direct_mesh_sha256'];mesh=json.loads(gzip.decompress(path.read_bytes()));vertices,faces=mesh['vertices'],mesh['faces']
 else:
  data=np.load(ROOT/'audits/native-motion-mesh-cache'/(row['sha256']+'-002-004.npz'));vertices,faces=data['vertices'].tolist(),data['faces'].tolist()
 assert len(faces)==row['triangles'];model['meshes'][key]['vertices']=vertices;model['meshes'][key]['faces']=faces
model['native_migration']={'candidate':True,'authoritative':False,'source_reference_sha256':audit['source_model_sha256'],'saved_versions':{'master':60,'chassis':12,'leg':13,'head':22},'custom_geometry':'Native Fusion STEP exports, with validated native kernel mesh for the right outer shin.','hardware_geometry':'Frozen vendor and purchased hardware references.','comparison_report':'audits/whole-native-robot-motion-service.json','scope':'Frozen low-profile robot. Later browser limb revisions are excluded.'}
path=ROOT/'exports/native-review-model.json.gz';data=json.dumps(model,separators=(',',':')).encode();path.write_bytes(gzip.compress(data));report={'updated_utc':datetime.datetime.now(datetime.UTC).isoformat(),'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'model_sha256':hashlib.sha256(data).hexdigest(),'custom_keys':len(audit['native_inputs']),'source_of_truth':False,'native_inputs':audit['native_inputs'],'source_reference_sha256':audit['source_model_sha256']};(ROOT/'audits/native-review-model-export.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='native_inputs'})
