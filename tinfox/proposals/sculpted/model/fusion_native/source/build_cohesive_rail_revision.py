"""Author the cleaned current rails with native sketches, cuts and a linked mirror."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/n).read_text() for n in ['native_documents.py','intent_geometry.py','compact_cover_intent.py','frame_deck_intent.py','frame_rail_intent.py','sensor_saddle_intent.py','frame_tie_intent.py','cohesive_frame_intent.py'])+'''
def run(_context: str):
 import json,time,tempfile,os
 app=core.Application.get();doc=authoring_document(app,'chassis');doc.activate();assert doc.dataFile.versionNumber==17;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert d.activateRootComponent();assert not any(c.partNumber=='CANDIDATE_cc_chassis_beam_102' for c in d.allComponents);tick=time.monotonic();right=root.occurrences.addNewComponent(core.Matrix3D.create());c=right.component;c.name='Right rail with accessible thread pads';c.partNumber='CANDIDATE_cc_chassis_beam_102';builder=CohesiveFrameIntent(IntentGeometry(d,c));body=builder.rail();old=next(c for c in d.allComponents if c.partNumber=='chassis_beam_102');body.material=old.bRepBodies.item(0).material;body.appearance=old.bRepBodies.item(0).appearance
 left=root.occurrences.addNewComponent(core.Matrix3D.create());lc=left.component;lc.name='Left rail with shared frame geometry';lc.partNumber='CANDIDATE_cc_chassis_beam_-102';objects=core.ObjectCollection.create();objects.add(body);copy=lc.features.copyPasteBodies.add(objects);copy.name='Shared native rail features';assert copy.isParametric;original=copy.bodies.item(0);objects=core.ObjectCollection.create();objects.add(original);inp=lc.features.mirrorFeatures.createInput(objects,lc.xZConstructionPlane);inp.isCombine=False;lc.features.mirrorFeatures.add(inp).name='Opposite side reflection';lc.features.removeFeatures.add(original).name='Keep the left manufacturing rail';rows=[]
 for occ,label in [(right,'right-rail'),(left,'left-rail')]:
  component=occ.component;assert component.bRepBodies.count==1;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in component.features)
  for item in list(component.sketches)+list(component.constructionPlanes):item.isLightBulbOn=False
  path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-body-'+label+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,component));assert os.path.getsize(path)>10000;rows.append({'part':component.partNumber,'features':component.features.count,'sketches':component.sketches.count,'path':path});occ.isLightBulbOn=False
 print(json.dumps({'saved':False,'parts':rows,'elapsed_seconds':time.monotonic()-tick,'native_left_link':copy.isParametric,'scope':'Current cleaned rail revision: no retired cover bosses or old top-flange tie bores. Pilot holes are tap-drill envelopes.'}))
'''
r=rpc(s,'cohesive-rails-native-build',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-rails-native-build.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
for row in record['parts']:fetch(row['path'],Path(row['path']).name)
