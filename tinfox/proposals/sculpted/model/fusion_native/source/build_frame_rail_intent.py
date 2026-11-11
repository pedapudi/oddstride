"""Build the verified shared-datum rail as a native internal candidate."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
assert json.loads((ROOT/'audits/frame-rail-intent-local-replay.json').read_text())['passed']
s='\n'.join((ROOT/'source'/n).read_text() for n in ['native_documents.py','intent_geometry.py','compact_cover_intent.py','frame_deck_intent.py','frame_rail_intent.py'])+'''
def run(_context: str):
 import json,time,os,tempfile
 app=core.Application.get();doc=authoring_document(app,'chassis');assert doc==app.activeDocument and doc.dataFile.versionNumber==13;d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();assert not any(c.partNumber.startswith('CANDIDATE_') for c in d.allComponents);tick=time.monotonic();occ=d.rootComponent.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.partNumber='CANDIDATE_chassis_beam_102';c.name='Shared-datum right motor rail';body=FrameRailIntent(IntentGeometry(d,c)).build();assert c.bRepBodies.count==1;issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues;old=next(c0 for c0 in d.allComponents if c0.partNumber=='chassis_beam_102');body.material=old.bRepBodies.item(0).material;body.appearance=old.bRepBodies.item(0).appearance
 for item in list(c.sketches)+list(c.constructionPlanes)+list(c.constructionAxes):item.isLightBulbOn=False
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','frame-intent-right-rail.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>10000;occ.isLightBulbOn=False;print(json.dumps({'saved':False,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'volume_mm3':body.volume*1000,'path':path,'elapsed_seconds':time.monotonic()-tick,'source_of_truth':False}))
'''
r=rpc(s,'frame-rail-native-intent-build',timeout=480);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/frame-rail-native-intent-build.json').write_text(json.dumps(record,indent=2));print(record,flush=True);fetch(record['path'],Path(record['path']).name)
