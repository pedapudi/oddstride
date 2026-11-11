"""Build a native cassette candidate using shared frame datums and pack geometry."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/n).read_text() for n in ['native_documents.py','intent_geometry.py','compact_cover_intent.py','frame_deck_intent.py','frame_rail_intent.py','frame_cassette_intent.py'])+'''
def run(_context: str):
 import json,time,tempfile,os
 app=core.Application.get();doc=authoring_document(app,'chassis');doc.activate();assert doc==app.activeDocument and doc.dataFile.versionNumber==15;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert d.activateRootComponent();assert not any(c.partNumber.startswith('CANDIDATE_') for c in d.allComponents);tick=time.monotonic();occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.partNumber='CANDIDATE_battery_cassette';c.name='Shared-frame battery cassette';builder=FrameCassetteIntent(IntentGeometry(d,c));body=builder.build();old=next(c for c in d.allComponents if c.partNumber=='battery_cassette');body.material=old.bRepBodies.item(0).material;body.appearance=old.bRepBodies.item(0).appearance
 issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues
 for item in list(c.sketches)+list(c.constructionPlanes):item.isLightBulbOn=False
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','frame-intent-battery-cassette.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>10000;occ.isLightBulbOn=False;print(json.dumps({'saved':False,'part':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'volume_mm3':body.volume*1000,'path':path,'elapsed_seconds':time.monotonic()-tick,'source_of_truth':False}))
'''
r=rpc(s,'frame-cassette-native-intent-build',timeout=480);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/frame-cassette-native-intent-build.json').write_text(json.dumps(record,indent=2));print(record,flush=True);fetch(record['path'],Path(record['path']).name)
