"""Publish saved subsystem updates and verify hideable references in the master."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
versions={role:row['version'] for role,row in json.loads((ROOT/'manifests/subsystems.json').read_text())['subsystems'].items()};prior=json.loads((ROOT/'manifests/native-master-status.json').read_text())['saved_version'];assembly=json.loads((ROOT/'audits/native-master-shared-subsystem-refresh.json').read_text());assert assembly['passed'] and {r['role']:r['version'] for r in assembly['subsystems']}==versions
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'master');doc.activate();assert doc.dataFile.versionNumber==PRIOR;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;tick=time.monotonic();capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);actual={o.attributes.itemByName('Tinfox','Subsystem').value:o.documentReference.version for o in root.occurrences};assert actual==VERSIONS,actual;shared={};source_doc=authoring_document(app,'chassis');source=fusion.Design.cast(source_doc.products.itemByProductType('DesignProductType'))
 for role in ['leg','head']:
  original=authoring_document(app,role);assert original.dataFile.versionNumber==VERSIONS[role] and original.dataFile.isComplete and not original.isModified;design=fusion.Design.cast(original.products.itemByProductType('DesignProductType'));rows=[]
  for parameter in design.derivedParameters:
   name=parameter.name.removesuffix('_Ref');p=source.userParameters.itemByName(name);assert p is not None;error=abs(parameter.value-p.value);assert error<1e-9,(role,name,error);rows.append({'parameter':parameter.name,'source':name,'value':parameter.value,'unit':parameter.unit,'internal_error':error})
  assert len(rows)==8;shared[role]=rows
 counts={'motor':0,'plug':0,'cable':0};references=[];structural=[o for o in root.allOccurrences if o.component.partNumber in ['motor_carrier_1','thigh_inner','thigh_outer']];structural_lights={o.fullPathName:o.isLightBulbOn for o in structural};assert len(structural)>=5
 selected=[]
 for occ in root.allOccurrences:
  name=occ.component.name
  if name.endswith(('_roll_motor','_hip_motor','_knee_motor')):role='motor'
  elif '_port_' in name and name.endswith('_plug'):role='plug'
  elif '_port_' in name and name.endswith('_cable'):role='cable'
  else:continue
  selected.append((occ,role))
 assert len(selected)==60
 for occ,role in selected:
  c=occ.component;assert c.bRepBodies.count==1;body=c.bRepBodies.item(0);assert c.name in body.name,(c.name,body.name);before={other.fullPathName:other.isLightBulbOn for other,_ in selected};visible=occ.isLightBulbOn;occ.isLightBulbOn=False;assert not occ.isLightBulbOn
  for other,_ in selected:
   if other.fullPathName!=occ.fullPathName:assert other.isLightBulbOn==before[other.fullPathName],(c.name,other.fullPathName)
  for other in structural:assert other.isLightBulbOn==structural_lights[other.fullPathName]
  occ.isLightBulbOn=visible;assert occ.isLightBulbOn==visible;counts[role]+=1;references.append({'component':c.name,'body':body.name,'path':occ.fullPathName,'role':role,'independent_visibility_verified':True})
 assert counts=={'motor':12,'plug':24,'cable':24}
 assert doc.save('Refresh the saved native subsystem versions and verify all one hundred custom instances and purchased references at the explicitly recorded assembly target placement; motors, XT30 connectors and cable bodies remain individually named and independently hideable in the Master. Shared family values agree across subsystem references. Frame hardware placement dependencies, CNC access, physical fits and strength remain unqualified; generated CAD remains authoritative.');print(json.dumps({'passed':True,'save_requested':True,'prior_version':PRIOR,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'subsystem_versions':actual,'shared_parameters':shared,'counts':counts,'references':references,'capacity':capacity,'elapsed_seconds':time.monotonic()-tick,'source_of_truth':False}))
'''.replace('PRIOR',str(prior)).replace('VERSIONS',repr(versions)).replace('KNOWN',repr(known_files()))
r=rpc(s,'master-reference-visibility-checkpoint',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/master-reference-visibility-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k not in ['references','shared_parameters','capacity']})
