"""Compare the remaining body updates against the frozen low robot."""
import json
from pathlib import Path
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1]
targets={p['key']:p for p in json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low']['custom_parts']}
for key,label in [('chassis_crossmember_121','current-front-crossmember-native'),('lidar_lid','current-lidar-lid-native'),('belly_center_0','current-belly-native')]:
 reference={'id':key,'source_step':targets[key]['files']['step']['path'],'source_reference_note':'Frozen low robot 929c06ab624ed80192157e99ce43165c1416db414902cb0a36c19d6d2ad50da6. Native features; lower shell preserves archived native history.'};audit(key,label,reference);sections(key,label,reference)
