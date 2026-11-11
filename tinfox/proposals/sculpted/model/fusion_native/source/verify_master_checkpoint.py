"""Independently verify the saved master and its visible reference organization."""
import json,datetime
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];checkpoint=json.loads((ROOT/'audits/master-reference-visibility-checkpoint.json').read_text());expected=checkpoint['subsystem_versions'];expected_version=checkpoint['prior_version']+1
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'master');d=fusion.Design.cast(doc.products.itemByProductType('DesignProductType'));root=d.rootComponent;versions={o.attributes.itemByName('Tinfox','Subsystem').value:o.documentReference.version for o in root.occurrences};counts={'motor':0,'plug':0,'cable':0};references=[]
 for occ in root.allOccurrences:
  name=occ.component.name
  if name.endswith(('_roll_motor','_hip_motor','_knee_motor')):role='motor'
  elif '_port_' in name and name.endswith('_plug'):role='plug'
  elif '_port_' in name and name.endswith('_cable'):role='cable'
  else:continue
  c=occ.component;assert c.bRepBodies.count==1 and name in c.bRepBodies.item(0).name;counts[role]+=1;references.append({'name':name,'body':c.bRepBodies.item(0).name,'path':occ.fullPathName,'own_visibility':occ.isLightBulbOn})
 assert counts=={'motor':12,'plug':24,'cable':24}
 print(json.dumps({'file_id':doc.dataFile.id,'name':doc.name,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'read_only':doc.dataFile.isReadOnly,'editable_files':len(app.data.personalUseLimits.editableFiles),'subsystems':versions,'reference_counts':counts,'references':references}))
'''
r=rpc(s,'master-reference-save-verification',timeout=45,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);assert record['version']==expected_version and record['complete'] and not record['modified'] and not record['read_only'];assert record['subsystems']==expected;record['verified_utc']=datetime.datetime.now(datetime.UTC).isoformat();report=f"audits/master-v{record['version']}-save-verification.json";(ROOT/report).write_text(json.dumps(record,indent=2));p=ROOT/'manifests/native-master-status.json';status=json.loads(p.read_text());status.update(saved_version=record['version'],save_verification=report,assembly_audit='audits/native-master-shared-subsystem-refresh.json',subsystem_versions=record['subsystems'],updated_utc=record['verified_utc'],independent_reference_visibility='audits/master-reference-visibility-checkpoint.json');status['open_gates']=['Finish fixed-body hardware placement dependencies and remaining process-fit bindings.','Complete CNC straight-tool access review; suspect cassette guide windows and thigh return ledges remain unqualified.','Regenerate current native manufacturing/review outputs after final qualification.'];status['source_of_truth']=False;p.write_text(json.dumps(status,indent=2));p=ROOT/'manifests/subsystems.json';subs=json.loads(p.read_text());subs.update(master_saved_version=record['version'],master_save_verification=report);p.write_text(json.dumps(subs,indent=2));print({k:v for k,v in record.items() if k!='references'})
