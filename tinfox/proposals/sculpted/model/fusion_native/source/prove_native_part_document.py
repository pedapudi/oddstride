"""Verify that Fusion's native Save Copy As retains the editable stator history."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
SCRIPT='''import adsk,adsk.core as core,adsk.fusion as fusion,json,time,os,tempfile
def run(_context: str):
 app=core.Application.get();master=app.activeDocument;design=fusion.Design.cast(app.activeProduct)
 assert master.name.startswith('Tinfox - Native Master Assembly')
 source=next(o.component for g in design.rootComponent.occurrences for o in g.component.occurrences if o.component.partNumber=='motor_mount_ring')
 project=next(p for p in app.data.activeHub.dataProjects if p.id==PROJECT_ID)
 folder=next((f for f in project.rootFolder.dataFolders if f.name=='04 Native parts'),None)
 if folder is None:folder=project.rootFolder.dataFolders.add('04 Native parts')
 legs=next((f for f in folder.dataFolders if f.name=='Leg masters'),None)
 if legs is None:legs=folder.dataFolders.add('Leg masters')
 name='V0 - Knee motor stator plate';data_file=next((f for f in legs.dataFiles if f.name==name),None)
 if data_file is None:
  future=source.saveCopyAs(name,legs,'Native stator master. Editability proof must pass before replacing the embedded component.','')
  deadline=time.monotonic()+45
  while future.dataFile is None and time.monotonic()<deadline:adsk.doEvents();time.sleep(.1)
  data_file=future.dataFile
 if data_file is None:print(json.dumps({'stage':'upload_pending','folder_id':legs.id,'file_name':name,'passed':False}));return
 document=app.documents.open(data_file,True);d=fusion.Design.cast(app.activeProduct);component=d.rootComponent
 records={'stage':'native_editability_test','file_id':data_file.id,'file_name':data_file.name,'folder':'04 Native parts/Leg masters','sketches':component.sketches.count,'features':[{'name':f.name,'type':f.objectType} for f in component.features],'user_parameters':[p.name for p in d.userParameters],'part_number':component.partNumber}
 parameter=d.userParameters.itemByName('stator_thickness')
 if parameter is None:records['passed']=False;records['reason']='Driving parameter missing from native copy'
 else:
  old=parameter.expression;before=component.bRepBodies.item(0).volume*1000
  parameter.expression='3.3 mm';d.computeAll();changed=component.bRepBodies.item(0).volume*1000
  parameter.expression=old;d.computeAll();restored=component.bRepBodies.item(0).volume*1000
  records.update(before_volume_mm3=before,changed_volume_mm3=changed,restored_volume_mm3=restored,passed=component.sketches.count==3 and component.features.count==5 and abs(changed/before-1.1)<1e-7 and abs(restored-before)<1e-6)
 document.close(False);master.activate();print(json.dumps(records))
'''
def main():
 manifest=json.loads((ROOT/'manifests/parts.json').read_text());script=SCRIPT.replace('PROJECT_ID',repr(manifest['fusion_project']['id']))
 messages=rpc(script,'native-part-document-proof',timeout=120)
 if not messages[0].get('success',True):return
 result=json.loads(messages[0]['message']);(ROOT/'audits/native-part-document-proof.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
