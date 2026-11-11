"""Compare a native bench component to its explicitly frozen print-fit target."""
import sys,json,hashlib
from pathlib import Path
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1];key=sys.argv[1];label=sys.argv[2];target=json.loads((ROOT/'manifests/motor-complex-native-target.json').read_text());row=target['parts'][key];source=ROOT/row['source_step'];assert hashlib.sha256(source.read_bytes()).hexdigest()==row['sha256'];ref={'id':key,'source_step':str(source),'skip_legacy_probes':True,'source_reference_note':'Frozen detached motor-complex fit target with explicit open driver/insertion corrections; not a strength or CNC release.'}
if key.startswith('thigh_'):ref.update(volume_method='gauss_kronrod_spans',volume_method_reason='Converged span-aware integration for the existing offset shell surfaces; same method as the qualified native parent.')
a=audit(key,label,ref);b=sections(key,label,ref);r={'part':key,'source_sha256':row['sha256'],'native_sha256':a['native_step_sha256'],'geometry_passed':a['geometric_gate_passed'],'sections_passed':b['section_gate_passed']};(ROOT/'audits'/('motor-complex-'+key+'-comparison.json')).write_text(json.dumps(r,indent=2));print(r)
