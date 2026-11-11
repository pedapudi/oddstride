"""Checkpoint qualified hidden family definitions without replacing the published bench."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
from motor_complex_corrected_exports import COMPONENTS
ROOT=Path(__file__).resolve().parents[1]
assert json.loads((ROOT/'audits/whole-native-family-comparison.json').read_text())['passed'];assert json.loads((ROOT/'audits/whole-paired-family-edit-restore.json').read_text())['passed'];baseline=json.loads((ROOT/'audits/corrected-bench-saved-reopen.json').read_text())['snapshot']['parts']
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);errors={}
 for key,number in PARTS.items():
  c=next(c for c in d.allComponents if c.partNumber==number);b=c.bRepBodies.item(0);bb=b.boundingBox;ref=BASELINE[key];err=max(abs(a-b)for a,b in zip([v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]],ref['bounds_mm']));assert err<1e-5 and c.features.count==ref['features'] and b.faces.count==ref['faces'];errors[key]={'bounds_mm':err,'volume_difference_mm3':b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000-ref['volume_mm3']}
 variants=[c for c in d.allComponents if c.partNumber.startswith('CANDIDATE_wf_')];assert len(variants)==11;assert all(all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features)for c in variants);assert [o.component.partNumber for o in d.rootComponent.occurrences if o.isLightBulbOn]==['BENCH_MOTOR_COMPLEX'];d.userParameters.itemByName('pc_closure_bore').comment='Central closure clearance RADIUS in mm (legacy parameter name). Separate from motor-bore DIAMETER pc_motor_bore; do not uniformly scale vendor interfaces.';before=doc.dataFile.versionNumber;assert doc.save('Add eleven native linked handed/rear paired-bearing support families. Surface, section, cylindrical interface and shared motor-center edit/restore checks pass. Rear closure keeps stator clock; rear cup uses separately authored journal/web. Published Leg24 bench geometry and visible assembly are retained; full-robot installation remains pending.');print(json.dumps({'previous_version':before,'version_at_return':doc.dataFile.versionNumber,'complete_at_return':doc.dataFile.isComplete,'modified_at_return':doc.isModified,'qualified_family_definitions':11,'published_bench_bounds_preserved':True,'bench_property_diagnostics':errors,'capacity':capacity,'whole_robot_source_of_truth':False}))
'''.replace('KNOWN',repr(known_files())).replace('PARTS',repr({k:v[0]for k,v in COMPONENTS.items()})).replace('BASELINE',repr(baseline))
r=rpc(s,'whole-native-family-checkpoint',timeout=240);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/whole-native-family-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k not in ['capacity','bench_property_diagnostics']})
