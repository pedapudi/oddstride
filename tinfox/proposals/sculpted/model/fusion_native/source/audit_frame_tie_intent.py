"""Compare the native front/rear transverse ties with frozen interface solids."""
import json,sys
from pathlib import Path
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1];targets={p['key']:p for p in json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low']['custom_parts']};suffix=sys.argv[1] if len(sys.argv)>1 else ''
for side,key in [('front','chassis_crossmember_121'),('rear','chassis_crossmember_-121')]:
 label='frame-intent-'+side+'-tie'+suffix;reference={'id':key,'source_step':targets[key]['files']['step']['path'],'source_reference_note':'Frozen low robot transverse tie. Common parametric section and front-only sensor attachment bores.'};audit(key,label,reference);sections(key,label,reference)
