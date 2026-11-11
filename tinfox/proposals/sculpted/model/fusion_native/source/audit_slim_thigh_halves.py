"""Compare final native thigh halves against the M5-retained frozen prototype."""
import hashlib,json
from pathlib import Path
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1];target=json.loads((ROOT/'manifests/bench-limb-native-target.json').read_text());rows=[]
for key,row in target['parts'].items():
 if not key.startswith('thigh_'):continue
 source=ROOT/row['source_step'];assert hashlib.sha256(source.read_bytes()).hexdigest()==row['sha256'];ref={'id':key,'source_step':str(source),'source_reference_note':'Frozen paired-bearing/M5-retention prototype '+target['model_sha256']+'; earlier V0 probe files belong to a different outer profile.','exact_face_sampling':True,'skip_legacy_probes':True,'volume_method':'gauss_kronrod_spans','volume_method_reason':'Converged span-aware volume for nonuniform cubic offset shell surfaces.','functional_clearance_cylinders':[[13.5,0,0,-170,0,1,0]],'functional_clearance_proof':'audits/slim-thigh-cavity-analytic-arc-proof.json'};label='slim-native-'+key
 a=audit(key,label,ref);b=sections(key,label,ref);rows.append({'part':key,'source_sha256':row['sha256'],'native_sha256':a['native_step_sha256'],'geometry':a['geometric_gate_passed'],'sections':b['section_gate_passed']})
report={'source_model_sha256':target['model_sha256'],'parts':rows,'passed':all(r['geometry']and r['sections']for r in rows),'scope':'Shape and cross-section comparison; native edits, hardware/service/motion and manufacturing access remain separate gates.'};(ROOT/'audits/slim-thigh-halves-comparison.json').write_text(json.dumps(report,indent=2));print(report)
