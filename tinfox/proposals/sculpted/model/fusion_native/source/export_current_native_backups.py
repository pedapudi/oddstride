"""Export versioned native-document backups without flattening linked designs."""
import hashlib,json,zipfile
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
from verify_native_archive import verify
ROOT=Path(__file__).resolve().parents[1]
script=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,os,hashlib,time
def run(_context:str):
 app=core.Application.get();folder=os.path.join(os.path.expanduser('~'),'Library','Caches','Tinfox','native-versioned-backups');os.makedirs(folder,exist_ok=True);rows=[];tick=time.monotonic()
 for role in ['leg','chassis','head','master']:
  doc=authoring_document(app,role);assert doc.dataFile.isComplete and not doc.isModified;doc.activate();d=fusion.Design.cast(app.activeProduct);version=doc.dataFile.versionNumber;path=os.path.join(folder,'Tinfox-'+role.title()+'-v'+str(version)+'.f3d');references=[{'file_id':r.dataFile.id,'name':r.dataFile.name,'version':r.version}for r in doc.allDocumentReferences];row={'role':role,'file_id':doc.dataFile.id,'saved_version':version,'references':references,'supported_api':'ExportManager.createFusionArchiveExportOptions + execute','reference_scope':'Native document snapshot; linked-reference closure is not established by an F3D filename. Owning subsystem archives are exported separately; canonical cloud documents remain authoritative.'}
  try:
   options=d.exportManager.createFusionArchiveExportOptions(path);assert options;ok=d.exportManager.execute(options)
   if ok and os.path.isfile(path):row.update(exported=True,path=path,bytes=os.path.getsize(path),sha256=hashlib.sha256(open(path,'rb').read()).hexdigest())
   else:row.update(exported=False,error='Supported archive export returned false or did not create the requested file.')
  except RuntimeError as error:row.update(exported=False,error=str(error))
  assert not doc.isModified;rows.append(row)
 master=authoring_document(app,'master');master.activate();camera=app.activeViewport.camera;camera.eye=core.Point3D.create(65,-65,40);camera.target=core.Point3D.create(0,0,-10);camera.upVector=core.Vector3D.create(0,0,1);camera.isFitView=True;camera.isSmoothTransition=False;app.activeViewport.camera=camera;app.activeViewport.refresh();preview=os.path.join(folder,'Tinfox-Master-v'+str(master.dataFile.versionNumber)+'.png');assert app.activeViewport.saveAsImageFile(preview,1800,1200);assert not master.isModified;print(json.dumps({'preview':{'path':preview,'sha256':hashlib.sha256(open(preview,'rb').read()).hexdigest(),'saved_master_version':master.dataFile.versionNumber},'archives':rows,'all_exports_completed':all(r['exported']for r in rows),'self_contained_distributed_archive_claimed':False,'new_cloud_documents':0,'flattened_custom_geometry':False,'elapsed_seconds':time.monotonic()-tick}))
'''
reply=rpc(script,'current-native-versioned-backups',timeout=1200,read_only=True);assert reply[0]['success'],reply;record=json.loads(reply[0]['message']);(ROOT/'audits/current-native-versioned-backups.json').write_text(json.dumps(record,indent=2))
for row in record['archives']:
    if not row['exported']:continue
    relative='backups/'+Path(row['path']).name;fetch(row['path'],relative);path=ROOT/'exports'/relative;assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'];row['local_path']=str(path.relative_to(ROOT));row['zip_archive']=zipfile.is_zipfile(path)
    if row['zip_archive']:
        row['archive_integrity']=verify(path)
preview=record['preview'];relative='backups/'+Path(preview['path']).name;fetch(preview['path'],relative);preview['local_path']='exports/'+relative;assert hashlib.sha256((ROOT/preview['local_path']).read_bytes()).hexdigest()==preview['sha256']
(ROOT/'manifests/current-native-backups.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k!='archives'});print([(r['role'],r['saved_version'],r['exported'])for r in record['archives']])
