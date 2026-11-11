"""Retain reference import history and retire old occurrences with Remove features."""
import base64,hashlib,json,zlib
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];target=json.loads((ROOT/'manifests/current-body-target.json').read_text());payload=[];metrology=json.loads((ROOT/'manifests/cohesive-body-hardware-metrology.json').read_text())
for name in target['reference_hardware_keys']:
 item=target['files'][name]['step'];raw=(ROOT/item['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==item['sha256'];payload.append({'name':name,'sha256':item['sha256'],'expected':metrology[name],'data':base64.b64encode(zlib.compress(raw,9)).decode()})
old_covers=[f'body_service_screw_{side}_{x}_22' for side in [-1,1] for x in [-112,112]]
remove=old_covers+[n for n in target['reference_hardware_keys'] if n.startswith('chassis_tie_bolt_')]+target['removed_reference_keys']
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,time,base64,zlib,hashlib
def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');doc.activate();assert doc.dataFile.versionNumber==17;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert d.activateRootComponent();tick=time.monotonic();removed=[];added=[];frames={o.component.partNumber:o for o in root.occurrences if o.component.partNumber.startswith('BODY_PLACEMENT_')};assert all('BODY_PLACEMENT_cover_'+str(front)+'_'+str(side) in frames for front in [-1,1] for side in [-1,1])
 for name in REMOVE:
  matches=[o for o in root.allOccurrences if o.component.partNumber==name or o.component.name==name];assert len(matches)==1,(name,len(matches));o=matches[0];removed.append({'name':name,'path':o.fullPathName});feature=root.features.removeFeatures.add(o);assert feature;feature.name='Retire standard hardware '+name
 rules={};library=root.occurrences.addNewComponent(core.Matrix3D.create());library.component.name='Current chassis fastener import history';library.component.partNumber='REFERENCE_CURRENT_CHASSIS_SCREWS';library.isLightBulbOn=False
 folder=os.path.join(tempfile.gettempdir(),'tinfox-native','reference-hardware');os.makedirs(folder,exist_ok=True)
 for item in PAYLOAD:
  name=item['name'];data=zlib.decompress(base64.b64decode(item['data']));assert hashlib.sha256(data).hexdigest()==item['sha256'];path=os.path.join(folder,'cohesive-'+name+'.step');open(path,'wb').write(data);c=library.component;assert c.occurrences.count==0;options=app.importManager.createSTEPImportOptions(path);options.isViewFit=False;assert app.importManager.importToTarget2(options,c) is not None;assert c.occurrences.count==1;occ=c.occurrences.item(0);c=occ.component;c.name=name;c.partNumber=name
  assert c.bRepBodies.count==1,(name,c.bRepBodies.count,c.occurrences.count);c.bRepBodies.item(0).name=name+' standard fastener reference';c.attributes.add('Tinfox','GeometryRole','Standard fastener reference only');c.attributes.add('Tinfox','SourceSTEP_SHA256',item['sha256'])
  body=c.bRepBodies.item(0);bb=body.boundingBox;bounds=[getattr(p,a)*10 for p in [bb.minPoint,bb.maxPoint] for a in ['x','y','z']];assert max(abs(a-b) for a,b in zip(bounds,item['expected']['bounds_mm']))<.0001,(name,bounds);assert abs(body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000-item['expected']['volume_mm3'])<.001,name
  if name.startswith('body_service_screw_'):
   side,x,_=map(int,name.rsplit('_',3)[1:]);group=f'cover_{1 if x>0 else -1}_{side}'
  else:
   x,side,_=map(int,name.rsplit('_',3)[1:]);group=f'corner_{1 if x>0 else -1}_{side}'
  result=occ.moveToComponent(frames['BODY_PLACEMENT_'+group]);assert result;proxy=result if result.assemblyContext else result.createForAssemblyContext(frames['BODY_PLACEMENT_'+group]);proxy.isGroundToParent=True;proxy.attributes.add('Tinfox','SourceInstance',name);proxy.attributes.add('Tinfox','PlacementFrame',group);added.append({'name':name,'group':group,'sha256':item['sha256'],'path':proxy.fullPathName})
  proxy.isLightBulbOn=True
 assert d.computeAll();actual=[o for o in root.allOccurrences if o.component.name in [item['name']for item in PAYLOAD]];retained_old=[o.component.name for o in root.allOccurrences if o.component.name.startswith(('chassis_tie_nut_','sensor_root_nut_'))];issues=[(j.name,j.errorOrWarningMessage)for j in root.joints if j.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];checks={'actual':[(o.component.name,o.component.bRepBodies.count,o.fullPathName)for o in actual],'retained_old_nuts':retained_old,'history_children':library.component.occurrences.count,'joint_issues':issues};print(json.dumps({'saved':False,'passed':len(actual)==12 and all(o.component.bRepBodies.count==1 for o in actual) and not retained_old and not issues,'checks':checks,'removed':removed,'added':added,'placement_rules':rules,'elapsed_seconds':time.monotonic()-tick,'scope':'Twelve standard screw references replaced, ten obsolete loose nuts removed. Custom geometry is not imported. Thread engagement and stock are separate qualification items.'}))
'''.replace('REMOVE',repr(remove)).replace('PAYLOAD',repr(payload))
r=rpc(s,'cohesive-body-hardware-repair',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);record['source_model_sha256']=target['source_model_sha256'];(ROOT/'audits/cohesive-body-hardware-repair.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k not in ['added','removed']});print('Added',len(record['added']),'removed',len(record['removed']))
