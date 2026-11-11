"""Build two compact native motor interfaces without disturbing the saved leg module."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/n).read_text() for n in ['native_documents.py','intent_geometry.py','cohesive_limb_intent.py','slim_mount_intent.py'])+'''
def run(_context: str):
 import json,time,tempfile,os
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();assert doc.dataFile.versionNumber==14 and not doc.isModified;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert d.activateRootComponent();assert not any(c.partNumber.startswith('CANDIDATE_sl_') for c in d.allComponents);tick=time.monotonic();rows=[]
 for key,method,title in [('motor_mount_ring','stator','Tangent-lobed knee stator mount'),('hip_hub','hub','Rounded ribbed hip output hub')]:
  occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name=title;c.partNumber='CANDIDATE_sl_'+key;builder=SlimMountIntent(IntentGeometry(d,c));body=getattr(builder,method)();old=next(c0 for c0 in d.allComponents if c0.partNumber==key);body.material=old.bRepBodies.item(0).material;body.appearance=old.bRepBodies.item(0).appearance;assert c.bRepBodies.count==1;issues=[(f.name,f.errorOrWarningMessage)for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,(key,issues)
  for item in list(c.sketches)+list(c.constructionPlanes):item.isLightBulbOn=False
  path=os.path.join(tempfile.gettempdir(),'tinfox-native','slim-native-'+key+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>10000;rows.append({'part':key,'component':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'path':path});occ.isLightBulbOn=False
 print(json.dumps({'saved':False,'parts':rows,'elapsed_seconds':time.monotonic()-tick,'scope':'Current slim motor mount candidates only; no roll-bearing/carrier replacement or latest full-leg publication.'}))
'''
r=rpc(s,'slim-motor-mounts-native-build',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/slim-motor-mounts-native-build.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
for row in record['parts']:fetch(row['path'],Path(row['path']).name)
