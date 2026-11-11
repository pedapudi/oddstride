"""Author the current low cover as a compact native Chassis component."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1];proof=json.loads((ROOT/'audits/compact-current-cover-semantic-replay.json').read_text());assert proof['passed']
s=script_header()+'\n'+'\n'.join((ROOT/'source'/p).read_text() for p in ['intent_geometry.py','sensor_body_delta_intent.py','compact_cover_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile,time
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:R7U8KNNBSA6o3YwVNF2ZQQ'
 assert doc.dataFile.versionNumber==3 and not doc.dataFile.isReadOnly;d=fusion.Design.cast(app.activeProduct);require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);root=d.rootComponent;assert not any(c.partNumber=='CANDIDATE_current_body_center_0' for c in d.allComponents);tick=time.monotonic();occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Current rounded body cover';c.partNumber='CANDIDATE_current_body_center_0';g=IntentGeometry(d,c);body=CompactCoverIntent(g).current();assert c.bRepBodies.count==1;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),[(f.name,int(f.healthState),f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];body.name='Single removable rounded cover';path=os.path.join(tempfile.gettempdir(),'tinfox-native','current-body-cover-native.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));app.activeViewport.fit();print(json.dumps({'saved':False,'part':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'volume_mm3':body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000,'path':path,'elapsed_seconds':time.monotonic()-tick,'source_target':'929c06ab624ed80192157e99ce43165c1416db414902cb0a36c19d6d2ad50da6','gate':'Native candidate pending full geometry and functional edit audit.'}))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'current-body-cover-native-build',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-body-cover-native-build.json').write_text(json.dumps(record,indent=2));print(record);fetch(record['path'],Path(record['path']).name)
