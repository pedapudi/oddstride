"""Checkpoint native datum links at the unchanged baseline before update tests."""
import json,sys
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1];role=sys.argv[1];assert role in ['leg','head']
qualified='--qualified' in sys.argv
if qualified:
 for phase in ['edited','restored']:assert json.loads((ROOT/'audits'/f'{role}-datum-propagation-{phase}.json').read_text())['passed']
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,ROLE);assert doc==app.activeDocument;d=fusion.Design.cast(app.activeProduct);capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);source=authoring_document(app,'chassis');sd=fusion.Design.cast(source.products.itemByProductType('DesignProductType'));assert abs(sd.userParameters.itemByName('robot_hip_x').value-18.5)<1e-8;assert abs(d.allParameters.itemByName('robot_hip_x_Ref').value-18.5)<1e-8;assert abs(d.allParameters.itemByName('robot_fastener_diametral_allowance_Ref').value-.04)<1e-8;assert d.rootComponent.features.deriveFeatures.count==1;feature=d.rootComponent.features.deriveFeatures.item(0);assert len(feature.sourceEntities)==1 and feature.sourceEntities[0].objectType=='adsk::fusion::ConstructionPlane';assert feature.bodies.count==0
 for c in d.allComponents:
  assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),c.name
  for plane in c.constructionPlanes:plane.isLightBulbOn=False
 assert doc.save('Shared native Chassis datum parameters and construction-plane dependency at frozen dimensions. '+('Actual shared hip and fastener edits/restores pass; explicit native selection refresh is required. Whole-chassis resizing remains unqualified.' if QUALIFIED else 'Cross-document propagation audit remains pending.'));paths=[]
 if QUALIFIED:
  path=os.path.join(tempfile.gettempdir(),'tinfox-native','Tinfox-'+ROLE.title()+'-family-linked-checkpoint.f3d');assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path));paths.append(path)
  if ROLE=='head':
   for key,label in [('front_fascia','current-sensor-hood-family-restored'),('body_nose_surround','current-sensor-cradle-family-restored')]:
    c=next(c for c in d.allComponents if c.partNumber==key);path=os.path.join(tempfile.gettempdir(),'tinfox-native',label+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>10000;paths.append(path)
 print(json.dumps({'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'role':ROLE,'capacity':capacity,'cross_document_propagation_qualified':QUALIFIED,'paths':paths}))
'''.replace('ROLE',repr(role)).replace('KNOWN',repr(known_files())).replace('QUALIFIED',repr(qualified))
r=rpc(s,role+'-shared-datum-checkpoint',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits'/f'{role}-shared-datum-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k!='capacity'})

for path in record.get('paths',[]):fetch(path,Path(path).name)
