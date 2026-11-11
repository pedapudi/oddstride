"""Checkpoint restored subsystem references after the full native motion comparison."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
from personal_plan_preflight import script_header, known_files
ROOT=Path(__file__).resolve().parents[1]
for name in ['whole-native-robot-motion-service','native-master-shared-subsystem-refresh']:
    assert json.loads((ROOT/'audits'/f'{name}.json').read_text())['passed']
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,time

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'master');assert app.activeDocument==doc;d=fusion.Design.cast(app.activeProduct);capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);versions={}
 for occurrence in d.rootComponent.occurrences:
  role=occurrence.attributes.itemByName('Tinfox','Subsystem').value;versions[role]=occurrence.documentReference.version
 assert versions=={'chassis':12,'leg':13,'head':22},versions
 previous=doc.dataFile.versionNumber;assert previous==59
 assert doc.save('Refresh restored native Chassis v12, Leg v13 and Head v22. All 100 custom instances retain frozen placement; 35 robot motion samples, 109 knee samples and 24 service moves add no contacts versus the source. Shared hip and fastener parameter edit/restore passes with explicit Derive refresh. Whole-frame resizing and strength remain unqualified; generated CAD remains authoritative.')
 folder=os.path.join(tempfile.gettempdir(),'tinfox-native');paths=[]
 path=os.path.join(folder,'Tinfox-Master-v60-motion-audited.f3d');assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path));paths.append(path)
 chassis=authoring_document(app,'chassis');assert chassis.dataFile.versionNumber==12 and not chassis.isModified;cd=fusion.Design.cast(chassis.products.itemByProductType('DesignProductType'));path=os.path.join(folder,'Tinfox-Chassis-v12-family-linked.f3d');assert cd.exportManager.execute(cd.exportManager.createFusionArchiveExportOptions(path));paths.append(path)
 print(json.dumps({'previous_version':previous,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'subsystems':versions,'paths':paths,'capacity':capacity,'source_of_truth':False}))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'native-master-motion-checkpoint',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/native-master-motion-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k!='capacity'},flush=True)
for path in record['paths']:fetch(path,Path(path).name)
