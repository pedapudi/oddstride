"""Author the frozen low sensor cradle inside the existing Head design."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s=script_header()+'\n'+'\n'.join((ROOT/'source'/p).read_text() for p in ['intent_geometry.py','sensor_saddle_intent.py'])+'''
def run(_context: str):
 import json,time,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);assert not any(c.partNumber=='CANDIDATE_current_body_nose_surround' for c in d.allComponents);tick=time.monotonic();occ=d.rootComponent.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Current low sensor cradle';c.partNumber='CANDIDATE_current_body_nose_surround';g=IntentGeometry(d,c);body=SensorSaddleIntent(g).build();assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);body.name='Two-foot rail-mounted sensor cradle';path=os.path.join(tempfile.gettempdir(),'tinfox-native','current-sensor-cradle-native.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));print(json.dumps({'saved':False,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'volume_mm3':body.volume*1000,'elapsed_seconds':time.monotonic()-tick,'path':path,'scope':'Candidate matching frozen low sensor saddle; full shape, edit, service and assembly gates remain.'}))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'current-sensor-cradle-native-build',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-sensor-cradle-native-build.json').write_text(json.dumps(record,indent=2));print(record);fetch(record['path'],Path(record['path']).name)
