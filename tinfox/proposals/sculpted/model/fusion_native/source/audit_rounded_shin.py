"""Compare current native shin halves with the frozen open-washer-seat target."""
import hashlib,json
from pathlib import Path
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1]
target=json.loads((ROOT/'manifests/latest-shell-target.json').read_text())
for key,row in target['parts'].items():
 if not key.startswith('shin_'):continue
 source=ROOT/row['step']['path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==row['step']['sha256']
 ref={'id':key,'source_step':str(source),'source_reference_note':'Current open washer-seat shin '+target['source_model_sha256']}
 label='rounded-native-'+key
 audit(key,label,ref);sections(key,label,ref)
