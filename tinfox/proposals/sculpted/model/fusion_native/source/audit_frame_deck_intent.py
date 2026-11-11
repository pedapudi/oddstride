"""Check the compact native brace/deck against immutable source solids."""
import json,sys
from pathlib import Path
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1]
targets={p['key']:p for p in json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low']['custom_parts']}
suffix='-final' if '--final' in sys.argv else ('-restored' if '--restored' in sys.argv else '')
for key in ['chassis_lower_brace','electronics_shelf']:
 label='frame-intent-'+key+suffix;reference={'id':key,'source_step':targets[key]['files']['step']['path'],'source_reference_note':'Frozen low model 929c06ab624ed80192157e99ce43165c1416db414902cb0a36c19d6d2ad50da6. Compact native patterns share frame/deck attachment datums.'};audit(key,label,reference);sections(key,label,reference)
