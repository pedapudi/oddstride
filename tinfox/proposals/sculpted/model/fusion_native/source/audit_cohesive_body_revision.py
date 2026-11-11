"""Compare the authorized enclosure revision with its frozen source solids."""
import json
from pathlib import Path
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1];target=json.loads((ROOT/'manifests/current-body-target.json').read_text())
for key,label in [('body_center_0','cohesive-body-cover'),('belly_center_0','cohesive-body-belly')]:
 reference={'id':key,'source_step':str(ROOT/target['files'][key]['step']['path']),'source_reference_note':'Authorized body revision '+target['source_model_sha256']+'; not the old protected low-profile body.'};audit(key,label,reference);sections(key,label,reference)
