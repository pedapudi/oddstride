"""Recover completed native uploads without rerunning their feature construction."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
script='''import adsk,adsk.core as core,adsk.fusion as fusion,json,os,tempfile,time
def run(_context: str):
 app=core.Application.get();master=next(d for d in app.documents if d.name.startswith('Tinfox - Native Master Assembly'));records=[]
 for key,group_name in [('sensor_bezel','Electronics and sensors'),('foot','Shared leg designs')]:
  document=next(d for d in app.documents if '['+key+']' in d.name);document.activate();d=fusion.Design.cast(app.activeProduct);c=d.rootComponent
  project=next(p for p in app.data.activeHub.dataProjects if p.name=='Tinfox');parent=next(f for f in project.rootFolder.dataFolders if f.name=='04 Native parts');folder_name='Leg masters' if key=='foot' else group_name;folder=next(f for f in parent.dataFolders if f.name==folder_name)
  name='V0 - '+key.replace('_',' ').capitalize()
  data_file=next((f for f in folder.dataFiles if f.name==name),None)
  if data_file is None:
   future=c.saveCopyAs(name,folder,'Native editable part upload recovery.','');deadline=time.monotonic()+60
   while future.dataFile is None and time.monotonic()<deadline:adsk.doEvents();time.sleep(.1)
   data_file=future.dataFile
  assert data_file is not None,(key,'Upload not complete')
  path=os.path.join(tempfile.gettempdir(),'tinfox-native');paths=[os.path.join(path,key+e) for e in ['.step','.stl','.f3d']]
  assert all(os.path.exists(p) for p in paths)
  records.append({'part':key,'label':data_file.name,'file_id':data_file.id,'file_name':data_file.name,'folder':'04 Native parts/'+('Leg masters' if key=='foot' else group_name),'sketches':c.sketches.count,'feature_count':c.features.count,'parameter_count':d.userParameters.count,'body_count':c.bRepBodies.count,'paths':paths,'features':[{'name':f.name,'type':f.objectType} for f in c.features]})
  master.activate();md=fusion.Design.cast(app.activeProduct);group=next(o.component for o in md.rootComponent.occurrences if o.component.name==group_name)
  if not any(o.component.partNumber==key for o in group.occurrences):group.occurrences.addByInsert(data_file,core.Matrix3D.create(),True)
  document.close(False)
 master.activate();master.save('Recovered completed native part uploads; migration gate remains open.')
 print(json.dumps(records))
'''
r=rpc(script,'recover-native-uploads');assert r[0].get('success'),r
records=json.loads(r[0]['message']);p=ROOT/'manifests/native-files.json';registry=json.loads(p.read_text())
for record in records:
 registry[record['part']]=record
 for path in record['paths']:fetch(path,Path(path).name)
p.write_text(json.dumps(registry,indent=2))
