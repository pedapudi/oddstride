"""Export a review-only assembly from native part STLs and frozen V0 placement."""
import json,gzip,sys,hashlib
from pathlib import Path
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'snapshots/source'))
import kinematics
def build():
 manifest=json.loads((ROOT/'manifests/parts.json').read_text());reference_path=manifest.get('reference_model','snapshots/reference-model.json.gz')
 model=json.loads(gzip.decompress((ROOT/reference_path).read_bytes()));keys={p['id'] for p in manifest['parts']};native={}
 for key in sorted(keys):
  path=ROOT/'exports'/f'{key}.stl'
  if not path.exists():continue
  mesh=trimesh.load_mesh(path,process=True)
  native[key]={'vertices':np.round(mesh.vertices,6).tolist(),'faces':mesh.faces.tolist(),'stl_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 parts=[]
 for part in model['parts']:
  if part['name']=='electronics_clearance' or part['name'].endswith(('_keepout','_withdrawal')):continue
  key=part['mesh'];parts.append({**part,'transform':kinematics.matrix(part,kinematics.POSES['stand']).tolist(),'native_status':'built' if key in native else 'missing' if key in keys else 'reference'})
 payload={'design_revision':'V0','migration_gate_passed':False,'source_of_truth':'CadQuery V0 with authorized cover delta until migration gate passes','source_reference_url':'../'+reference_path,'source_model_sha256':manifest['source_model_sha256'],'native_geometry_count':len(native),'custom_geometry_count':len(keys),'parts':parts,'meshes':native}
 output=ROOT/'exports/native-preview.json.gz';output.write_bytes(gzip.compress(json.dumps(payload,separators=(',',':')).encode(),compresslevel=6));print(len(native),'native geometries, review file',output.stat().st_size,'bytes')
 downloads=[]
 for path in sorted((ROOT/'exports').glob('*.f3d')):
  key=path.stem;part=next((p for p in manifest['parts'] if p['id']==key),None)
  label=part['label'] if part else 'Earlier partial master — not the completed assembly'
  downloads.append({'file':path.name,'part':key if part else None,'label':label,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'release_status':'Review only; native editability and assembly gates remain open.'})
 (ROOT/'exports/native-downloads.json').write_text(json.dumps({'archives':downloads,'scope':'Editable native feature archives. The partial master predates later individual part files; it is not a current complete robot assembly.'},indent=2))
if __name__=='__main__':build()
