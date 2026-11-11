"""Complete the frozen low robot's body inventory using native histories."""
import json,hashlib
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
archive=ROOT/'exports/belly_center_0.f3d';belly_sha=hashlib.sha256(archive.read_bytes()).hexdigest()
for suffix,gate in [('geometry','geometric_gate_passed'),('sections','section_gate_passed')]:assert json.loads((ROOT/'audits'/f'belly_center_0-{suffix}.json').read_text())[gate]
s=script_header()+'\n'+'\n'.join((ROOT/'source'/p).read_text() for p in ['intent_geometry.py','sensor_saddle_intent.py'])+'''
def run(_context: str):
 import json,time,os,tempfile,hashlib
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:R7U8KNNBSA6o3YwVNF2ZQQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);assert not doc.isModified;tick=time.monotonic();before=[{'part':c.partNumber,'features':c.features.count,'bodies':c.bRepBodies.count} for c in d.allComponents];assert not any(c.partNumber=='belly_center_0' for c in d.allComponents)
 # This archive was authored as Fusion sketches and features, not neutral BReps.
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','belly_center_0.f3d');assert hashlib.sha256(open(path,'rb').read()).hexdigest()==BELLY_SHA;assert app.importManager.importToTarget2(app.importManager.createFusionArchiveImportOptions(path),root) is not None;belly=next(c for c in d.allComponents if c.partNumber=='belly_center_0');assert belly.features.count==112 and belly.sketches.count==43 and belly.bRepBodies.count==1;assert belly.meshBodies.count==0 and not any('BaseFeature' in f.objectType for f in belly.features);belly.name='Lower body shell';belly.attributes.add('Tinfox','ConstructionQuality','Native archived history with matching shape. Semantic family binding and simplification remain open.')
 # The new cover has independent native construction; remove the retired cover.
 old=next(o for o in root.occurrences if o.component.partNumber=='body_center_0');assert old.component.features.count==279;assert old.deleteMe();cover=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_current_body_center_0');cover.partNumber='body_center_0';cover.name='Rounded upper body cover';assert d.computeAll();assert cover.bRepBodies.count==1 and cover.features.count==96
 beam=next(c for c in d.allComponents if c.partNumber=='chassis_crossmember_121');g=IntentGeometry(d,beam)
 for name,value in [('saddle_x',121),('saddle_foot_spacing',48),('saddle_root_nominal_diameter',4),('saddle_fastener_diametral_clearance',.4),('saddle_root_hole_radius',2.2),('saddle_sensor_seat_z',80),('saddle_sensor_lid_bottom_z',102)]:g.parameter(name,value,comment='Shared sensor interface; vendor diameter remains independent of body size. Physical fit is unqualified.')
 d.userParameters.itemByName('saddle_x').expression='cover_hip_x-64 mm';d.userParameters.itemByName('saddle_root_hole_radius').expression='(saddle_root_nominal_diameter+saddle_fastener_diametral_clearance)/2';d.userParameters.itemByName('saddle_sensor_lid_bottom_z').expression='saddle_sensor_seat_z+22 mm'
 sk=SensorSaddleIntent(g).circles('25 mm',[('saddle_x','-saddle_foot_spacing/2'),('saddle_x','saddle_foot_spacing/2')],'saddle_root_hole_radius','Sensor cradle M4 root holes');g.extrude_all(sk,'25 mm','Two M4 root clearances',fusion.FeatureOperations.CutFeatureOperation,[beam.bRepBodies.item(0)])
 lid=next(c for c in d.allComponents if c.partNumber=='lidar_lid');objects=core.ObjectCollection.create();objects.add(lid.bRepBodies.item(0));inp=lid.features.moveFeatures.createInput2(objects);assert inp.defineAsTranslateXYZ(g.value('saddle_x-82 mm'),g.value('0 mm'),g.value('saddle_sensor_lid_bottom_z-74 mm'),True);lid.features.moveFeatures.add(inp).name='Shared sensor seat placement';lid.name='Lidar upper cover'
 assert d.computeAll();rows=[]
 for c in d.allComponents:
  issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,(c.name,issues);rows.append({'part':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count})
 assert sum(r['bodies'] for r in rows)==18;paths=[]
 for c,label in [(beam,'current-front-crossmember-native'),(lid,'current-lidar-lid-native'),(belly,'current-belly-native')]:
  path=os.path.join(tempfile.gettempdir(),'tinfox-native',label+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));paths.append(path)
 print(json.dumps({'saved':False,'before':before,'after':rows,'paths':paths,'retired_cover_features_removed':279,'native_belly_history_imported':{'features':112,'sketches':43,'archive_sha256':BELLY_SHA},'elapsed_seconds':time.monotonic()-tick,'scope':'Frozen low-body geometry update. Front-beam position is still in its original construction; whole chassis family scaling and fabrication remain unqualified.'}))
'''.replace('KNOWN',repr(known_files())).replace('BELLY_SHA',repr(belly_sha))
r=rpc(s,'current-chassis-final-geometry',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-chassis-final-geometry.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k not in ['before','after']})
for path in record['paths']:fetch(path,Path(path).name)
