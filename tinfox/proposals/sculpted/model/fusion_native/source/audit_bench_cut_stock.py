"""Compare the native bench cut-stock parts with the frozen prototype."""
import hashlib,json
from pathlib import Path
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1]
target=json.loads((ROOT/'manifests/bench-limb-native-target.json').read_text())
rows=[]
for key,row in target['parts'].items():
 if not any(key.startswith(p) for p in ['knee_axle','sleeve_','pod_sleeve_']):continue
 path=ROOT/row['source_step'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
 ref={'id':key,'source_step':str(path),'source_reference_note':'Frozen paired-6810 bench prototype '+target['model_sha256']}
 label='bench-native-'+key
 a=audit(key,label,ref);b=sections(key,label,ref)
 rows.append({'part':key,'source_sha256':row['sha256'],'native_sha256':a['native_step_sha256'],'geometry_passed':a['geometric_gate_passed'],'sections_passed':b['section_gate_passed']})
report={'source_model_sha256':target['model_sha256'],'parts':rows,'passed':all(r['geometry_passed'] and r['sections_passed'] for r in rows),'scope':'Shape and critical cylindrical interface comparisons only; parameter edits and assembled clamp and tie stacks remain separate gates.'}
(ROOT/'audits/bench-cut-stock-comparison.json').write_text(json.dumps(report,indent=2));print(report)
