"""Check restored frame-process bindings preserve the immutable target solids."""
import json
from pathlib import Path
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1]
targets={p['key']:p for p in json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low']['custom_parts']}
for key in ['chassis_lower_brace','electronics_shelf','belly_center_0','battery_skid']:
 label='frame-process-'+key+'-restored';reference={'id':key,'source_step':targets[key]['files']['step']['path'],'source_reference_note':'Frozen low geometry; shared-frame and independent process parameters restored to baseline.'};audit(key,label,reference);sections(key,label,reference)
