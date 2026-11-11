"""Check native handed families against explicit transformed qualified parent solids."""
import json,hashlib
from pathlib import Path
import cadquery as cq
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1];record=json.loads((ROOT/'audits/whole-paired-native-variants.json').read_text())
parents={'CANDIDATE_pr_roll_cartridge_1':'paired-native-roll_cartridge_1.step','CANDIDATE_pr_roll_stator_backplate_1':'paired-native-roll_stator_backplate_1.step','CANDIDATE_rc_hip_stator_closure_1':'recessed-restored-hip_stator_closure_1.step','CANDIDATE_rc_motor_carrier_1':'recessed-restored-motor_carrier_1.step','CANDIDATE_rc_motor_carrier_-1':'recessed-restored-motor_carrier_-1.step'}
folder=ROOT/'snapshots/whole-native-family-reference';folder.mkdir(exist_ok=True);rows=[]
for row in record['parts']:
 parent=ROOT/'exports'/parents[row['parent']];shape=cq.importers.importStep(str(parent)).val()
 if row['rear']:shape=shape.mirror('YZ')if row['rear_method']=='mirror'else shape.translate((-10,0,0))
 if row['right']:shape=shape.mirror('XZ')
 key=row['key'];target=folder/(key+'.step');cq.exporters.export(shape,str(target));reference={'id':key,'source_step':str(target),'volume_method':'gauss_kronrod_spans','volume_method_reason':'Qualified trimmed native parent; use span-aware integration consistently.','skip_legacy_probes':True,'source_reference_note':'Explicit handed transform of qualified native parent '+parents[row['parent']]}
 result=audit(key,'whole-family-'+key,reference);sec=sections(key,'whole-family-'+key,reference)
 rows.append({'part':key,'parent_sha256':hashlib.sha256(parent.read_bytes()).hexdigest(),'reference_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'native_sha256':result['native_step_sha256'],'rear_method':row['rear_method']if row['rear']else'none','right_mirror':row['right'],'geometry_passed':result['geometric_gate_passed'],'sections_passed':sec['section_gate_passed']});print(rows[-1],flush=True)
report={'passed':all(x['geometry_passed']and x['sections_passed']for x in rows),'parts':rows,'scope':'Native family handed geometry and interface preservation only; whole assembly placement and motion pending.'};(ROOT/'audits/whole-native-family-comparison.json').write_text(json.dumps(report,indent=2));assert report['passed']
