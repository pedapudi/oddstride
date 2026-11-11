"""Build native revised ties and integral sensor thread pads in the chassis document."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/n).read_text() for n in ['native_documents.py','intent_geometry.py','compact_cover_intent.py','frame_deck_intent.py','frame_rail_intent.py','sensor_saddle_intent.py','frame_tie_intent.py','cohesive_frame_intent.py'])+'''
def run(_context: str):
 import json,time,tempfile,os
 app=core.Application.get();doc=authoring_document(app,'chassis');doc.activate();assert doc.dataFile.versionNumber==17;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert d.activateRootComponent();assert not any(c.partNumber=='CANDIDATE_cc_chassis_crossmember_121' for c in d.allComponents);tick=time.monotonic();front=root.occurrences.addNewComponent(core.Matrix3D.create());c=front.component;c.name='Transverse tie with integral sensor pads';c.partNumber='CANDIDATE_cc_chassis_crossmember_121';builder=CohesiveFrameIntent(IntentGeometry(d,c));body=builder.tie_base();old=next(c for c in d.allComponents if c.partNumber=='chassis_crossmember_121');body.material=old.bRepBodies.item(0).material;body.appearance=old.bRepBodies.item(0).appearance
 rear=root.occurrences.addNewComponent(core.Matrix3D.create());rc=rear.component;rc.name='Rear transverse tie';rc.partNumber='CANDIDATE_cc_chassis_crossmember_-121';objects=core.ObjectCollection.create();objects.add(body);copy=rc.features.copyPasteBodies.add(objects);copy.name='Shared bridge before front sensor pads';assert copy.isParametric;original=copy.bodies.item(0);objects=core.ObjectCollection.create();objects.add(original);inp=rc.features.mirrorFeatures.createInput(objects,rc.yZConstructionPlane);inp.isCombine=False;rc.features.mirrorFeatures.add(inp).name='Rear tie reflection';rc.features.removeFeatures.add(original).name='Keep the rear manufacturing tie';body=builder.front_sensor_pads(body);rows=[]
 for occ,label in [(front,'front-tie'),(rear,'rear-tie')]:
  component=occ.component;assert component.bRepBodies.count==1;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in component.features)
  for item in list(component.sketches)+list(component.constructionPlanes):item.isLightBulbOn=False
  path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-body-'+label+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,component));assert os.path.getsize(path)>10000;rows.append({'part':component.partNumber,'features':component.features.count,'sketches':component.sketches.count,'path':path});occ.isLightBulbOn=False
 print(json.dumps({'saved':False,'parts':rows,'elapsed_seconds':time.monotonic()-tick,'native_rear_link':copy.isParametric,'scope':'Revised source tie geometry. Pilot holes represent tap-drill envelopes, not manufactured threads or load qualification.'}))
'''
r=rpc(s,'cohesive-ties-native-build',timeout=480);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-ties-native-build.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
for row in record['parts']:fetch(row['path'],Path(row['path']).name)
