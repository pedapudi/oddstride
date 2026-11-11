"""Assemble saved native subsystems and verify all frozen instance placements."""
import gzip,json,sys,hashlib
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent));import kinematics as k
target=json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low'];model=json.loads(gzip.decompress((ROOT/target['reference_model']).read_bytes()));custom={p['key'] for p in target['custom_parts']};reference=json.loads((ROOT/'manifests/current-hardware-references.json').read_text())['variants']['low'];refnames={p['name'] for mesh in reference['reference_meshes'] for p in mesh['instances']};expected={p['name']:{field:p.get(field) for field in ['name','mesh','leg','group']} for p in model['parts'] if p['mesh'] in custom or p['name'] in refnames};assert len(expected)==430;k.P.update(model['parameters']);frames={leg:{name:m.tolist() for name,m in k.frames(leg,model['poses']['stand'][leg]).items()} for leg in k.LEGS};subsystems=json.loads((ROOT/'manifests/subsystems.json').read_text())['subsystems'];files={role:row['file_id'] for role,row in subsystems.items()};baseline=ROOT/'exports/Tinfox-Master-v58-library-baseline.f3d';assert baseline.exists();baseline_sha=hashlib.sha256(baseline.read_bytes()).hexdigest();legacy=[p['id'].replace('-','_')+'_' for p in json.loads((ROOT/'manifests/parts.json').read_text())['parts']]
s=script_header()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:7_ejr6qRQtezEex5HEj7xw';assert doc.dataFile.versionNumber==58;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);before=[{'name':o.name,'part':o.component.partNumber,'children':o.component.occurrences.count} for o in root.occurrences];assert {r['part'] for r in before}=={'Body and chassis','Electronics and sensors','Shared leg designs','Purchased references'};assert d.allComponents.count==65;started=time.monotonic()
 # A rolled-back generated attempt restores all 65 original components but
 # leaves Fusion's modified flag set. The separate reconciliation records this
 # state; the immutable v58 archive precedes every cleanup attempt.
 for o in list(root.occurrences):assert o.deleteMe()
 assert root.occurrences.count==0;removed_parameters=[]
 for unused_pass in range(8):
  removed=[]
  for p in list(d.userParameters):
   if p.name.startswith(tuple(LEGACY_PREFIXES)) and p.isDeletable:removed.append(p.name);assert p.deleteMe()
  removed_parameters+=removed
  if not removed:break
 inserted=[]
 for role in ['chassis','leg','head']:
  source=next(doc for doc in app.documents if doc.dataFile and doc.dataFile.id==FILES[role]);assert not source.isModified and source.dataFile.isComplete,(role,source.name);occ=root.occurrences.addByInsert(source.dataFile,core.Matrix3D.create(),True);assert occ is not None and occ.isReferencedComponent;occ.isGrounded=True;occ.attributes.add('Tinfox','Subsystem',role);inserted.append({'role':role,'file_id':source.dataFile.id,'version':source.dataFile.versionNumber,'occurrence':occ.name})
 assert d.computeAll();actual={};unexpected=[]
 def matrix(values):
  m=core.Matrix3D.create();assert m.setWithArray([v*(.1 if j==3 and i<3 else 1) for i,row in enumerate(values) for j,v in enumerate(row)]);return m
 def visit(occ,leg=None,group=None):
  c=occ.component;attr=c.attributes.itemByName('Tinfox','KinematicFrame')
  if attr:leg,group=attr.value.split(':' if ':' in attr.value else '_',1)
  key=c.partNumber;name=None;kind=None
  if key in CUSTOM_KEYS and c.bRepBodies.count:
   source=occ.attributes.itemByName('Tinfox','SourceInstance');name=source.value if source else next((p['name'] for p in EXPECTED.values() if p['mesh']==key and p['leg']==leg and (p['group']==group or leg is None)),None);kind='custom'
  elif c.name in REFERENCE_NAMES:name=c.name;kind='reference'
  if name:
   assert name in EXPECTED and name not in actual,(name,occ.fullPathName);row=EXPECTED[name];expected=matrix(FRAMES[row['leg']][row['group']]) if row['leg'] else core.Matrix3D.create();error=max(abs(a-b) for a,b in zip(expected.asArray(),occ.transform2.asArray()));assert error<1e-7,(name,error,occ.fullPathName);vertex_error=None
   if c.bRepBodies.count:
    body=c.bRepBodies.item(0);point=body.vertices.item(0).geometry.copy();point.transformBy(expected);vertex=body.createForAssemblyContext(occ).vertices.item(0).geometry;vertex_error=point.distanceTo(vertex)*10;assert vertex_error<1e-6,(name,vertex_error)
   actual[name]={'part_key':row['mesh'],'kind':kind,'path':occ.fullPathName,'matrix_error_cm':error,'vertex_error_mm':vertex_error,'component_bodies':c.bRepBodies.count};return
  if c.bRepBodies.count:unexpected.append({'part':key,'name':c.name,'path':occ.fullPathName,'bodies':c.bRepBodies.count})
  for child in occ.childOccurrences:visit(child,leg,group)
 for o in root.occurrences:visit(o)
 assert set(actual)==set(EXPECTED),{'missing':sorted(set(EXPECTED)-set(actual)),'extra':sorted(set(actual)-set(EXPECTED))};assert not unexpected,unexpected;assert sum(r['kind']=='custom' for r in actual.values())==100
 root.attributes.add('Tinfox','SourceOfTruth','False. Native assembled candidate; geometry, global family and remaining robot audits must pass before promotion.');root.attributes.add('Tinfox','SourceModelSHA256','929c06ab624ed80192157e99ce43165c1416db414902cb0a36c19d6d2ad50da6');root.attributes.add('Tinfox','ArchivedMasterV58_SHA256',BASELINE_SHA);root.attributes.add('Tinfox','MassMetrology','Global Fusion mass is not qualified; reference estimates and converged custom BRep mass integration remain separate.');print(json.dumps({'passed':True,'saved':False,'removed_library_groups':before,'removed_unused_generated_parameters':removed_parameters,'inserted':inserted,'instances':actual,'source_items':430,'custom_instances':100,'reference_items':330,'nonphysical_reference_items':['electronics_clearance'],'elapsed_seconds':time.monotonic()-started,'scope':'Three saved linked native subsystems with every frozen instance mapped and nominal native placement verified. Previous Master remains in cloud v58 and local native archive. No source-of-truth or fabrication promotion.'}))
'''.replace('KNOWN',repr(known_files())).replace('FILES',repr(files)).replace('FRAMES',repr(frames)).replace('EXPECTED',repr(expected)).replace('CUSTOM_KEYS',repr(sorted(custom))).replace('REFERENCE_NAMES',repr(sorted(refnames))).replace('BASELINE_SHA',repr(baseline_sha)).replace('LEGACY_PREFIXES',repr(legacy))
r=rpc(s,'current-native-master-assembly',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-native-master-assembly.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k not in ['instances','removed_unused_generated_parameters']})
