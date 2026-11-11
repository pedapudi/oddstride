"""Update the three saved native subsystem references and verify all placements."""
import json,gzip,sys
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent));import kinematics as k
target=json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low'];model=json.loads(gzip.decompress((ROOT/target['reference_model']).read_bytes()));custom={p['key'] for p in target['custom_parts']};reference=json.loads((ROOT/'manifests/current-hardware-references.json').read_text())['variants']['low'];names={p['name'] for mesh in reference['reference_meshes'] for p in mesh['instances']};expected={p['name']:{field:p.get(field) for field in ['name','mesh','leg','group']} for p in model['parts'] if p['mesh'] in custom or p['name'] in names};k.P.update(model['parameters']);frames={leg:{name:m.tolist() for name,m in k.frames(leg,model['poses']['stand'][leg]).items()} for leg in k.LEGS};versions={role:row['version'] for role,row in json.loads((ROOT/'manifests/subsystems.json').read_text())['subsystems'].items()};master_version=json.loads((ROOT/'manifests/native-master-status.json').read_text())['saved_version']
assembly_target_path=ROOT/'manifests/native-assembly-target.json'
if assembly_target_path.exists():
 assembly_target=json.loads(assembly_target_path.read_text());model=json.loads(gzip.decompress((ROOT/assembly_target['reference_model']).read_bytes()));custom=set(assembly_target['custom_keys']);names=set(assembly_target['reference_names']);expected={p['name']:{field:p.get(field) for field in ['name','mesh','leg','group']} for p in model['parts'] if p['mesh'] in custom or p['name'] in names};k.P.update(model['parameters']);frames={leg:{name:m.tolist() for name,m in k.frames(leg,model['poses']['stand'][leg]).items()} for leg in k.LEGS}
for role,version in versions.items():
 r=json.loads((ROOT/'audits'/f'{role}-v{version}-save-verification.json').read_text());assert r['complete'] and not r['modified']
header=(ROOT/'source/native_documents.py').read_text()+'\nimport adsk.core as core,adsk.fusion as fusion,json,time\n'+(ROOT/'source/native_master_inspection.py').read_text()
s=header+'''
def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'master');assert not doc.isModified
 if doc!=app.activeDocument:assert doc.activate()
 print(json.dumps({'active':doc.name,'version':doc.dataFile.versionNumber}))
'''
r=rpc(s,'activate-master-shared-subsystems',timeout=30);assert r[0]['success'],r
s=header+'''
def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'master');assert doc==app.activeDocument and doc.dataFile.versionNumber==MASTER_VERSION;d=fusion.Design.cast(app.activeProduct);tick=time.monotonic();before=[]
 for o in d.rootComponent.occurrences:
  attr=o.attributes.itemByName('Tinfox','Subsystem');assert attr;before.append({'role':attr.value,'version':o.documentReference.version})
 assert len(before)==3;assert doc.updateAllReferences();assert d.computeAll();updated=[]
 for o in d.rootComponent.occurrences:
  role=o.attributes.itemByName('Tinfox','Subsystem').value;assert o.documentReference.version==VERSIONS[role],(role,o.documentReference.version);updated.append({'role':role,'version':o.documentReference.version})
 result=inspect_native_master(d.rootComponent,EXPECTED,CUSTOM_KEYS,REFERENCE_NAMES,FRAMES);result.update(saved=False,source_of_truth=False,before=before,subsystems=updated,elapsed_seconds=time.monotonic()-tick,scope='Three linked native subsystems at restored frozen dimensions. Every source instance has its nominal transform and a native boundary vertex checked. Full robot motion/service and complete family resizing remain separate qualifications.');print(json.dumps(result))
'''.replace('MASTER_VERSION',str(master_version)).replace('VERSIONS',repr(versions)).replace('EXPECTED',repr(expected)).replace('CUSTOM_KEYS',repr(sorted(custom))).replace('REFERENCE_NAMES',repr(sorted(names))).replace('FRAMES',repr(frames))
# Replace placeholders only in the run body, not the helper's argument names.
helper=header;run=s[s.index('\ndef run(_context: str):'):];s=helper+run
r=rpc(s,'native-master-shared-subsystem-refresh',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);record['target_scope']=assembly_target if assembly_target_path.exists() else target;(ROOT/'audits/native-master-shared-subsystem-refresh.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k!='instances'})
