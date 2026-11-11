"""Compare changed native frame parts against the immutable cleaned body target."""
import json,sys
from pathlib import Path
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1];target=json.loads((ROOT/'manifests/current-body-target.json').read_text())
rows=[('chassis_crossmember_121','front-tie'),('chassis_crossmember_-121','rear-tie'),('chassis_beam_102','right-rail'),('chassis_beam_-102','left-rail')]
for key,label in rows:
 if len(sys.argv)>1 and sys.argv[1] not in label:continue
 reference={'id':key,'source_step':str(ROOT/target['files'][key]['step']['path']),'source_reference_note':'Authorized cleaned body revision '+target['source_model_sha256']}
 audit(key,'cohesive-body-'+label,reference);sections(key,'cohesive-body-'+label,reference)
