"""Save the verified current four-leg assembly and retire obsolete displayed assemblies."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1];a=json.loads((ROOT/'audits/current-native-installed-all.json').read_text());assert a['passed'] and a['native_bodies']==604
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);before=doc.dataFile.versionNumber;retired=[];groups=[];tick=time.monotonic()
 def show_physical(o):
  count=o.component.bRepBodies.count
  for b in o.component.bRepBodies:b.isLightBulbOn=True
  for child in o.component.occurrences:count+=show_physical(child)
  o.isLightBulbOn=count>0
  return count
 for o in root.occurrences:
  if o.component.partNumber.startswith('CURRENT_ASSEMBLY_'):
   count=show_physical(o);assert count==151,(o.component.partNumber,count);groups.append({'part':o.component.partNumber,'bodies':count})
  else:
   if o.isLightBulbOn:retired.append({'part':o.component.partNumber,'name':o.name,'action':'Hidden current document occurrence; saved historical scope and required native feature parents retained.'})
   o.isLightBulbOn=False
 assert len(groups)==4;assert sum(r['bodies']for r in groups)==604;root.attributes.add('Tinfox','CurrentWholeTarget',TARGET);root.attributes.add('Tinfox','WholeAssemblyStatus','Current low-profile four-leg candidate. Standing identity/placement verified; final pose, Master integration and save/reopen gates pending.');assert doc.save('Install the current four native leg assemblies:104 native custom/cut-stock instances and488 individually identified purchased references. Ground each instance relative to six parameter-driven frames; all592 source items and604 solids pass standing placement checks. Hide the earlier displayed bench and obsolete assemblies while preserving native construction dependencies and the canonical Leg24 bench archive. Whole-robot authority remains pending.');print(json.dumps({'save_requested':True,'previous_version':before,'version_at_return':doc.dataFile.versionNumber,'complete_at_return':doc.dataFile.isComplete,'modified':doc.isModified,'visible_groups':groups,'hidden_previously_visible':retired,'capacity':capacity,'elapsed_seconds':time.monotonic()-tick,'full_robot_native_source_of_truth':False}))
'''.replace('KNOWN',repr(known_files())).replace('TARGET',repr(a['target_model_sha256']))
r=rpc(s,'current-four-leg-checkpoint',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-four-leg-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k!='capacity'})
