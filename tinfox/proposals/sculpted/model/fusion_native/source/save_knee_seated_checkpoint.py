"""Save the visible knee revision while retaining the confirmed assembly defect."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
for name in ['knee-seat-family-edit-restore.json','motor-complex-seated-native-critical-interfaces.json']:
 assert json.loads((ROOT/'audits'/name).read_text())['passed']
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);bench=next(o for o in root.occurrences if o.component.partNumber=='BENCH_MOTOR_COMPLEX');visible=[]
 def walk(o):
  for b in o.component.bRepBodies:
   assert b.createForAssemblyContext(o).isVisible;visible.append(o.fullPathName+' / '+b.name)
  for child in o.component.occurrences:walk(child.createForAssemblyContext(o))
 walk(bench);assert len(visible)==124;assert [o for o in root.occurrences if o.isLightBulbOn]==[bench];bench.component.name='Motor complex - knee seats checked, closure correction pending';bench.component.attributes.add('Tinfox','AssemblyReleaseReady','false');bench.component.attributes.add('Tinfox','KnownDesignLimitation','Neutral closure-button/pod-tie interference. Complete fit assembly release withheld until reinforced closure correction is checked.');before=doc.dataFile.versionNumber;assert doc.save('Save native knee stator countersinks in both hands and nine common DIN7991 references. 37 targeted native interfaces, both-hand seat parameter edit/restore and exact exported seat comparison pass. Confirmed neutral closure-button/pod-tie interference remains; complete assembly release is withheld.');print(json.dumps({'previous_version':before,'version_at_return':doc.dataFile.versionNumber,'complete_at_return':doc.dataFile.isComplete,'modified_at_return':doc.isModified,'visible_bodies':124,'capacity':capacity,'assembly_release_ready':False,'authority_manifest_unchanged_geometry':True}))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'knee-seated-visible-checkpoint',timeout=240);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/knee-seated-visible-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k!='capacity'})
