"""Compare the native two-foot cradle with its immutable low-robot target."""
import json,sys
from pathlib import Path
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1]
target=next(p for p in json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low']['custom_parts'] if p['key']=='body_nose_surround')
r={'id':'current_body_nose_surround','source_step':target['files']['step']['path'],'source_reference_note':'Frozen current low sensor saddle, model 929c06ab624ed80192157e99ce43165c1416db414902cb0a36c19d6d2ad50da6. Semantic native load feet, rails, web and screw bosses.'}
label=sys.argv[1] if len(sys.argv)>1 else 'current-sensor-cradle-native'
audit('current_body_nose_surround',label,r);sections('current_body_nose_surround',label,r)
