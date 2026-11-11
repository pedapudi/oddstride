"""Record candidate native surface exports without changing authority."""
import json,hashlib,gzip
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((ROOT/'manifests/motor-complex-native-exports.json').read_text());report=json.loads((ROOT/'audits/motor-complex-native-direct-exports.json').read_text());version=report['checkpoint_version_at_export']
for row in report['custom_parts']:
 p=ROOT/'exports/motor-complex-native'/Path(row['path']).name;assert sha(p)==row['sha256'];record=manifest['parts'][row['part']];record.update(native_3mf=str(p.relative_to(ROOT)),native_3mf_sha256=sha(p),saved_version=version,native_bounds_mm=row['native_bounds_mm'],native_volume_mm3=row['native_volume_mm3'],state='saved_geometry_candidate_pending_final_publication_gates',native_feature_count=row['features'],native_sketch_count=row['sketches'])
manifest['stock_references']=[]
for row in report['optional_fit_stock']:
 p=ROOT/'exports/motor-complex-native'/Path(row['path']).name;assert sha(p)==row['sha256'];manifest['stock_references'].append({**row,'native_3mf':str(p.relative_to(ROOT)),'native_3mf_sha256':sha(p),'saved_version':version})
p=ROOT/'exports/motor-complex-native/native-bench-review.json.gz';raw=gzip.decompress(p.read_bytes());assert hashlib.sha256(raw).hexdigest()==report['review_model']['model_sha256'];manifest.update(review_model=str(p.relative_to(ROOT)),review_model_sha256=hashlib.sha256(raw).hexdigest(),review_model_gzip_sha256=sha(p),latest_leg_checkpoint=version,native_source_of_truth=False,authority='Saved native geometry candidate; final edit/restore, native interfaces, visibility checkpoint and saved reopen gates pending.',motion_enabled=False)
(ROOT/'manifests/motor-complex-native-candidate.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Candidate:',version,13,'parts',manifest['review_model'])
