"""Create a shared native transverse tie and its front sensor mounting variant."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/n).read_text() for n in ['native_documents.py','intent_geometry.py','compact_cover_intent.py','frame_deck_intent.py','frame_rail_intent.py','sensor_saddle_intent.py','frame_tie_intent.py'])+'''
def run(_context: str):
 import json,time,tempfile,os
 app=core.Application.get();doc=authoring_document(app,'chassis');assert doc==app.activeDocument and doc.dataFile.versionNumber==14;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert d.activateRootComponent();assert not any(c.partNumber.startswith('CANDIDATE_') for c in d.allComponents);tick=time.monotonic();front=root.occurrences.addNewComponent(core.Matrix3D.create());fc=front.component;fc.partNumber='CANDIDATE_chassis_crossmember_121';fc.name='Shared front transverse tie';builder=FrameTieIntent(IntentGeometry(d,fc));body=builder.base();old=next(c for c in d.allComponents if c.partNumber=='chassis_crossmember_121');body.material=old.bRepBodies.item(0).material;body.appearance=old.bRepBodies.item(0).appearance
 rear=root.occurrences.addNewComponent(core.Matrix3D.create());rc=rear.component;rc.partNumber='CANDIDATE_chassis_crossmember_-121';rc.name='Shared rear transverse tie';objects=core.ObjectCollection.create();objects.add(body);copy=rc.features.copyPasteBodies.add(objects);copy.name='Native common tie before the sensor-specific bores';assert copy.isParametric;original=copy.bodies.item(0);objects=core.ObjectCollection.create();objects.add(original);inp=rc.features.mirrorFeatures.createInput(objects,rc.yZConstructionPlane);inp.isCombine=False;mirror=rc.features.mirrorFeatures.add(inp);mirror.name='Rear transverse tie reflection';rc.features.removeFeatures.add(original).name='Keep the rear tie only';assert rc.bRepBodies.count==1
 # The rear copy precedes this front-only feature in the native history.
 body=builder.front_sensor_holes(body);assert fc.bRepBodies.count==1;rows=[]
 for occ,label in [(front,'front'),(rear,'rear')]:
  c=occ.component;issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,(c.name,issues)
  for item in list(c.sketches)+list(c.constructionPlanes):item.isLightBulbOn=False
  path=os.path.join(tempfile.gettempdir(),'tinfox-native','frame-intent-'+label+'-tie.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>10000;occ.isLightBulbOn=False;rows.append({'part':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'volume_mm3':c.bRepBodies.item(0).volume*1000,'path':path})
 print(json.dumps({'saved':False,'parts':rows,'elapsed_seconds':time.monotonic()-tick,'native_mirror_link':copy.isParametric,'source_of_truth':False}))
'''
r=rpc(s,'frame-tie-native-intent-build',timeout=360);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/frame-tie-native-intent-build.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
for row in record['parts']:fetch(row['path'],Path(row['path']).name)
