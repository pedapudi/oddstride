"""Refresh the existing Master to current saved native subsystems and bind its visible instances."""
import gzip,json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];target=json.loads((ROOT/'manifests/whole-robot-integration-target.json').read_text());model=json.loads(gzip.decompress((ROOT/target['reference_model']).read_bytes()));mapping=json.loads((ROOT/'manifests/whole-native-component-map-candidate.json').read_text())['parts'];refs=json.loads((ROOT/'manifests/whole-purchased-reference-groups.json').read_text());reference_names={p['name']for p in refs['parts']};expected={p['name']:{k:p.get(k)for k in ['name','mesh','leg','group']}for p in model['parts']if p['name']in reference_names or p['mesh']in mapping or p['mesh'].startswith('bench_stock_')};assert len(expected)==684
leg=json.loads((ROOT/'audits/current-native-installed-all.json').read_text());body=json.loads((ROOT/'audits/current-body-reference-binding.json').read_text());pose=json.loads((ROOT/'audits/current-native-pose-edit-restore.json').read_text());assert leg['passed']and body['passed']and pose['passed'];versions={r:v['version']for r,v in json.loads((ROOT/'manifests/subsystems.json').read_text())['subsystems'].items()};prior=json.loads((ROOT/'manifests/native-master-status.json').read_text())['saved_version']
s=(ROOT/'source/native_documents.py').read_text()+'\nimport adsk.core as core,adsk.fusion as fusion,json,time\n'+(ROOT/'source/current_master_inspection.py').read_text()+'''
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'master');assert doc.dataFile.versionNumber==PRIOR
 if doc.isModified:
  assert RECONCILED,(doc.name,'Unknown unsaved Master work')
 for role,version in VERSIONS.items():
  source=authoring_document(app,role);assert source.dataFile.versionNumber==version and source.dataFile.isComplete and not source.isModified,(role,source.dataFile.versionNumber,source.isModified)
 doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;tick=time.monotonic();before=[{'role':o.attributes.itemByName('Tinfox','Subsystem').value,'version':o.documentReference.version}for o in root.occurrences];assert len(before)==3
 if any(r['version']!=VERSIONS[r['role']]for r in before):assert doc.updateAllReferences()
 assert d.computeAll();visibility=[]
 def show_current_physical(occ):
  count=occ.component.bRepBodies.count
  for child in occ.component.occurrences:count+=show_current_physical(child.createForAssemblyContext(occ))
  desired=count>0
  if occ.isLightBulbOn!=desired:occ.isLightBulbOn=desired;visibility.append({'path':occ.fullPathName,'visible':desired})
  return count
 for subsystem in root.occurrences:
  role=subsystem.attributes.itemByName('Tinfox','Subsystem').value;assert subsystem.documentReference.version==VERSIONS[role],(role,subsystem.documentReference.version);subsystem.isLightBulbOn=True
  if role=='leg':
   for child in subsystem.component.occurrences:
    cp=child.createForAssemblyContext(subsystem);desired=child.component.partNumber.startswith('CURRENT_ASSEMBLY_');old=cp.isLightBulbOn
    if old!=desired:cp.isLightBulbOn=desired;visibility.append({'path':cp.fullPathName,'visible':desired})
    if desired:assert show_current_physical(cp)==151
 result,leaves=inspect_current_master(d,EXPECTED,CUSTOM,LEG_ROWS,BODY_ROWS);tm=fusion.TemporaryBRepManager.get();solid_checks=[]
 def world_body(name):
  occ=leaves[name];assert occ.component.bRepBodies.count==1;body=tm.copy(occ.component.bRepBodies.item(0));assert tm.transform(body,occ.transform2);return body
 for leg in ['FL','FR','RL','RR']:
  for first,second in [(leg+'_roll_stator_bolt_0','chassis_beam_'+('102'if leg.endswith('L')else'-102')),(leg+'_hip_hub',leg+'_knee_motor')]:
   a=world_body(first);b=world_body(second);before_volume=a.volume*1000;assert tm.booleanOperation(a,b,fusion.BooleanTypes.DifferenceBooleanType);after_volume=a.volume*1000;overlap=before_volume-after_volume;assert abs(overlap)<.00001,(first,second,overlap);solid_checks.append({'pair':[first,second],'overlap_mm3':max(0,overlap),'signed_volume_difference_mm3':overlap,'checker':'Actual installed native solids; temporary Boolean difference, source bodies unchanged.'})
 for name,role in [('body_wordmark','nonmanufacturing_display_reference'),('body_serial','nonmanufacturing_display_reference'),('sensor_window','provisional_optical_backing_envelope'),('electronics_clearance','auxiliary_clearance_envelope')]:leaves[name].attributes.add('Tinfox','GeometryRole',role)
 root.attributes.add('Tinfox','CurrentWholeTarget',TARGET);root.attributes.add('Tinfox','WholeAssemblyStatus','Current low-profile native assembly candidate; saved/reopen and final export comparison gates remain pending.');result.update(before=before,saved=False,visibility_changes=visibility,critical_native_solid_checks=solid_checks,source_target_sha256=TARGET,elapsed_seconds=time.monotonic()-tick,scope='Current low-profile robot only. Exact native linked versions, visible physical/reference identities, root transforms, same-vertex placement and eight targeted solid checks. Optional raised head and physical strength qualification are excluded.');print(json.dumps(result))
'''.replace('RECONCILED',repr(json.loads((ROOT/'audits/current-master-update-reconciliation.json').read_text())['passed'])).replace('PRIOR',str(prior)).replace('VERSIONS',repr(versions)).replace('EXPECTED',repr(expected)).replace('CUSTOM',repr(list(mapping))).replace('LEG_ROWS',repr(leg['instances'])).replace('BODY_ROWS',repr(body['parts'])).replace('TARGET',repr(target['model_sha256']))
compile(s,'refresh_current_master_assembly.py','exec');r=rpc(s,'current-master-assembly-refresh',timeout=900);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-master-assembly-refresh.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k!='instances'})
