"""Save the verified current low-profile native assembly in the existing Master."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
audit=json.loads((ROOT/'audits/current-master-assembly-refresh.json').read_text());assert audit['passed'] and audit['model_items']==684
script=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'master');doc.activate();d=fusion.Design.cast(app.activeProduct);capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);root=d.rootComponent;versions={o.attributes.itemByName('Tinfox','Subsystem').value:o.documentReference.version for o in root.occurrences};assert versions==VERSIONS;root.attributes.add('Tinfox','VisibleReviewScope','Current low-profile robot:683 visible physical/reference items,702 solids; one additional hidden electronics keepout. Optional raised head excluded.');root.attributes.add('Tinfox','AuthorityManifest','Current scope and final publication gates are recorded in fusion_native/manifests/source-authority.json and the versioned native whole export manifest.');root.attributes.add('Tinfox','QualificationScope','Native geometry and assembly. Material fits, cable routing, loaded strength and locomotion are separate physical qualification tasks.');before=doc.dataFile.versionNumber;assert doc.save('Current low-profile native assembly: four updated leg modules with independently hideable motor/connector references, current chassis and head. All684 records and703 solids bind the reference inventory, including one hidden auxiliary electronics keepout; actual native placements and eight targeted solid pairs pass. Geometry histories and moving-pose checks are retained in the linked subsystem checkpoints. Saved-reopen and downstream native export approval are recorded separately.');print(json.dumps({'previous_version':before,'version_at_return':doc.dataFile.versionNumber,'complete_at_return':doc.dataFile.isComplete,'modified_at_return':doc.isModified,'subsystem_versions':versions,'capacity':capacity,'full_robot_native_source_of_truth':False}))
'''.replace('KNOWN',repr(known_files())).replace('VERSIONS',repr({r['role']:r['version']for r in audit['subsystems']}))
reply=rpc(script,'current-native-master-checkpoint',timeout=300);assert reply[0]['success'],reply
record=json.loads(reply[0]['message']);(ROOT/'audits/current-native-master-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k!='capacity'})
