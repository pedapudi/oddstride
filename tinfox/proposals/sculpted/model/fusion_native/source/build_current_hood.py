"""Author the current low sensor hood in the existing Head subsystem."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text() for p in ['intent_geometry.py','sensor_saddle_intent.py','current_hood_intent.py'])+'''
def run(_context: str):
 import json,time,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);assert not any(c.partNumber=='CANDIDATE_current_front_fascia' for c in d.allComponents);face=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_current_front_face_master').bRepBodies.item(0);occ=d.rootComponent.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Current low sensor hood';c.partNumber='CANDIDATE_current_front_fascia';tick=time.monotonic();body=CurrentHoodIntent(IntentGeometry(d,c)).build(face);issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues;body.name='Removable hood with integral compound face';path=os.path.join(tempfile.gettempdir(),'tinfox-native','current-sensor-hood-native.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));print(json.dumps({'saved':False,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'native_volume_mm3':body.volume*1000,'path':path,'elapsed_seconds':time.monotonic()-tick,'gate':'Native hood candidate requires full fidelity, parameter, service and assembly checks.'}))
'''
r=rpc(s,'current-sensor-hood-native-build',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-sensor-hood-native-build.json').write_text(json.dumps(record,indent=2));print(record);fetch(record['path'],Path(record['path']).name)
