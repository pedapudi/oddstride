"""Save the corrected assembly dependency order after actual moving-body checks."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header, known_files

ROOT = Path(__file__).resolve().parents[1]
pose = json.loads((ROOT / 'audits/current-native-pose-edit-restore.json').read_text())
history = json.loads((ROOT / 'audits/current-pose-history-reorder.json').read_text())
assert pose['passed'] and history['passed']
script = script_header() + '\n' + (ROOT / 'source/native_documents.py').read_text() + '''
import adsk.core as core,adsk.fusion as fusion,json
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);root=d.rootComponent;assert d.userParameters.itemByName('qa_current_pose_case')is None;groups=[o for o in root.occurrences if o.isLightBulbOn];assert len(groups)==4 and all(o.component.partNumber.startswith('CURRENT_ASSEMBLY_')for o in groups);joints=[j for o in groups for j in o.component.joints];assert len(joints)==24 and all(j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState and not j.isSuppressed for j in joints)
 root.attributes.add('Tinfox','WholeAssemblyStatus','Current low-profile four-leg assembly. Native physical occurrences precede driven pose mates; asymmetric, folded and restored pose checks pass for all592 items. Whole Master publication remains pending.');before=doc.dataFile.versionNumber;assert doc.save('Correct native assembly dependency order: all physical instances precede the24 analytic pose mates. All592 custom and reference items follow their driven frames through asymmetric, folded and restored poses; native definition topology and boundary fingerprints are unchanged. Four current legs remain visible; archived bench and obsolete assemblies remain hidden. Whole Master authority is pending.');print(json.dumps({'previous_version':before,'version_at_return':doc.dataFile.versionNumber,'complete_at_return':doc.dataFile.isComplete,'modified_at_return':doc.isModified,'capacity':capacity,'whole_native_source_of_truth':False}))
'''.replace('KNOWN', repr(known_files()))
reply = rpc(script, 'current-pose-history-checkpoint', timeout=300)
assert reply[0]['success'], reply
record = json.loads(reply[0]['message'])
(ROOT / 'audits/current-pose-history-checkpoint.json').write_text(json.dumps(record, indent=2))
print({k:v for k,v in record.items() if k != 'capacity'})
