"""Verify final saved frame exports against their frozen native migration targets."""
import json
from pathlib import Path
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1]
targets={p['key']:p for p in json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low']['custom_parts']}
for key in ['battery_cassette','chassis_lower_brace','electronics_shelf','belly_center_0','battery_skid']:
 label='frame-checkpoint-'+key;reference={'id':key,'source_step':targets[key]['files']['step']['path'],'source_reference_note':'Final saved native chassis checkpoint at frozen nominal dimensions.'};audit(key,label,reference);sections(key,label,reference)
