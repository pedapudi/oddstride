"""Restore placed-occurrence visibility after timeline edits, then save the clean leg view."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1];assert json.loads((ROOT/'audits/current-native-pose-edit-restore.json').read_text())['passed']
script=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);changes=[];leaves=[]
 def show(occ):
  count=occ.component.bRepBodies.count
  for body in occ.component.bRepBodies:body.isLightBulbOn=True
  for child in occ.component.occurrences:count+=show(child.createForAssemblyContext(occ))
  wanted=count>0
  if occ.isLightBulbOn!=wanted:changes.append({'path':occ.fullPathName,'visible':wanted});occ.isLightBulbOn=wanted
  if occ.component.bRepBodies.count:leaves.append(occ)
  return count
 groups=[]
 for occ in root.occurrences:
  if occ.component.partNumber.startswith('CURRENT_ASSEMBLY_'):groups.append({'part':occ.component.partNumber,'bodies':show(occ)})
  else:occ.isLightBulbOn=False
 assert len(groups)==4 and all(g['bodies']==151 for g in groups);assert len(leaves)==592 and sum(o.component.bRepBodies.count for o in leaves)==604;assert all(o.isLightBulbOn and all(b.isLightBulbOn for b in o.component.bRepBodies)for o in leaves);assert all(o.component.partNumber.startswith('CURRENT_ASSEMBLY_')for o in root.occurrences if o.isLightBulbOn)
 root.attributes.add('Tinfox','VisiblePhysicalInventory','592 named current items,604 solids; actual occurrence bulbs verified after timeline edits. Obsolete assemblies and construction libraries remain hidden.');before=doc.dataFile.versionNumber;assert doc.save('Finalize current four-leg visibility after native history cleanup. All592 placed custom,stock and reference items/604 solids are visible; obsolete assemblies and required hidden construction remain separated. Geometry and asymmetric/fold/restored pose checks are unchanged from the verified preceding checkpoint.');print(json.dumps({'previous_version':before,'version_at_return':doc.dataFile.versionNumber,'complete_at_return':doc.dataFile.isComplete,'modified_at_return':doc.isModified,'changes':changes,'visible_items':592,'visible_bodies':604,'capacity':capacity,'geometry_changed':False}))
'''.replace('KNOWN',repr(known_files()))
reply=rpc(script,'current-leg-final-visibility-checkpoint',timeout=300);assert reply[0]['success'],reply;record=json.loads(reply[0]['message']);(ROOT/'audits/current-leg-final-visibility-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k not in ['capacity','changes']})
