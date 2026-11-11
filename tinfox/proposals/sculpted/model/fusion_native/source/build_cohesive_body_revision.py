"""Author the authorized cover and lower wrap using compact native operations."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/n).read_text() for n in ['native_documents.py','intent_geometry.py','compact_cover_intent.py','cohesive_body_intent.py'])+'''
def run(_context: str):
 import json,time,tempfile,os
 app=core.Application.get();doc=authoring_document(app,'chassis');doc.activate();assert doc.dataFile.versionNumber==17 and not doc.isModified;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert d.activateRootComponent();assert not any(c.partNumber.startswith('CANDIDATE_') for c in d.allComponents);tick=time.monotonic();occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Coherent shoulder enclosure';c.partNumber='CANDIDATE_cc_body_center_0';body=CohesiveBodyIntent(IntentGeometry(d,c)).cover();old=next(c for c in d.allComponents if c.partNumber=='body_center_0');body.material=old.bRepBodies.item(0).material;body.appearance=old.bRepBodies.item(0).appearance
 belly=next(c for c in d.allComponents if c.partNumber=='belly_center_0');assert belly.features.count==15;CohesiveBodyIntent(IntentGeometry(d,belly)).trim_belly(belly.bRepBodies.item(0));rows=[]
 for component,label in [(c,'cover'),(belly,'belly')]:
  assert component.bRepBodies.count==1;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in component.features),[(f.name,f.errorOrWarningMessage) for f in component.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]
  for item in list(component.sketches)+list(component.constructionPlanes):item.isLightBulbOn=False
  path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-body-'+label+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,component));assert os.path.getsize(path)>10000;rows.append({'part':component.partNumber,'features':component.features.count,'sketches':component.sketches.count,'faces':component.bRepBodies.item(0).faces.count,'path':path})
 occ.isLightBulbOn=False;print(json.dumps({'saved':False,'parts':rows,'elapsed_seconds':time.monotonic()-tick,'scope':'Authorized current body revision. Cover is a separate candidate; lower-wrap trim is a reversible native feature on the existing part. Frame interfaces and hardware update are pending.'}))
'''
r=rpc(s,'cohesive-body-native-build',timeout=480);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-body-native-build.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
for row in record['parts']:fetch(row['path'],Path(row['path']).name)
