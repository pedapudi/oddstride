"""Save and export the mapped native robot assembly as an audited candidate."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1];assert json.loads((ROOT/'audits/current-native-master-assembly.json').read_text())['passed']
s=script_header()+'''
import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,time

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:7_ejr6qRQtezEex5HEj7xw';d=fusion.Design.cast(app.activeProduct);assert d.rootComponent.occurrences.count==3 and all(o.isReferencedComponent for o in d.rootComponent.occurrences);capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);tick=time.monotonic();previous=doc.dataFile.versionNumber;assert doc.save('Assemble the saved native Chassis, Leg and Head subsystems. Map all 100 custom instances and 330 reference items to the frozen robot and verify their nominal transforms. Preserve v58 as the archived library baseline. Migration remains a candidate pending whole-robot and family audits.');folder=os.path.join(tempfile.gettempdir(),'tinfox-native');paths=[]
 for filename,creator in [('Tinfox-native-robot-candidate.f3d',d.exportManager.createFusionArchiveExportOptions),('Tinfox-native-robot-candidate.step',d.exportManager.createSTEPExportOptions)]:
  p=os.path.join(folder,filename);assert d.exportManager.execute(creator(p));paths.append(p)
 camera=app.activeViewport.camera;camera.eye=core.Point3D.create(65,-65,40);camera.target=core.Point3D.create(0,0,-10);camera.upVector=core.Vector3D.create(0,0,1);camera.isFitView=True;camera.isSmoothTransition=False;app.activeViewport.camera=camera;app.activeViewport.refresh();p=os.path.join(folder,'Tinfox-native-robot-candidate.png');assert app.activeViewport.saveAsImageFile(p,1800,1200);paths.append(p);print(json.dumps({'save_requested':True,'previous_version':previous,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'paths':paths,'capacity':capacity,'elapsed_seconds':time.monotonic()-tick,'source_of_truth_changed':False}))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'native-master-checkpoint',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/native-master-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k!='capacity'})
for p in record['paths']:fetch(p,Path(p).name)
