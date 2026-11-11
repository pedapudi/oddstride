"""Compare the shared-frame cassette with the immutable native migration target."""
import json,sys
from pathlib import Path
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1]
key='battery_cassette';target=next(p for p in json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low']['custom_parts'] if p['key']==key);label='frame-intent-battery-cassette'+(sys.argv[1] if len(sys.argv)>1 else '');reference={'id':key,'source_step':target['files']['step']['path'],'source_reference_note':'Frozen low battery cassette; native shared-frame profile with independently dimensioned pack details.'};audit(key,label,reference);sections(key,label,reference)
