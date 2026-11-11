"""Build two internal frame candidates without replacing the saved baseline."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
header='\n'.join((ROOT/'source'/name).read_text() for name in ['native_documents.py','intent_geometry.py','compact_cover_intent.py','frame_deck_intent.py'])
s=header+'''
def run(_context: str):
 import json
 app=core.Application.get();doc=authoring_document(app,'chassis');assert doc.dataFile.versionNumber==12;assert not any(c.partNumber.startswith('CANDIDATE_') for c in fusion.Design.cast(doc.products.itemByProductType('DesignProductType')).allComponents)
 if doc!=app.activeDocument:assert doc.activate()
 print(json.dumps({'active':doc.name,'version':doc.dataFile.versionNumber}))
'''
r=rpc(s,'activate-chassis-frame-family',timeout=30);assert r[0]['success'],r
s=header+'''
def run(_context: str):
 import json,time,os,tempfile
 app=core.Application.get();doc=authoring_document(app,'chassis');assert doc==app.activeDocument;d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();tick=time.monotonic();rows=[]
 for key,method,title in [('chassis_lower_brace','brace','Shared-datum frame diaphragm'),('electronics_shelf','deck','Shared-datum electronics deck')]:
  assert not any(c.partNumber=='CANDIDATE_'+key for c in d.allComponents);occ=d.rootComponent.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name=title;c.partNumber='CANDIDATE_'+key;g=IntentGeometry(d,c);body=getattr(FrameDeckIntent(g),method)();assert c.bRepBodies.count==1;issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues;old=next(c0 for c0 in d.allComponents if c0.partNumber==key and c0.bRepBodies.count);body.material=old.bRepBodies.item(0).material;body.appearance=old.bRepBodies.item(0).appearance
  for item in list(c.sketches)+list(c.constructionPlanes):item.isLightBulbOn=False
  path=os.path.join(tempfile.gettempdir(),'tinfox-native','frame-intent-'+key+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));occ.isLightBulbOn=False;rows.append({'key':key,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'volume_mm3':body.volume*1000,'path':path,'previous_features':old.features.count,'previous_sketches':old.sketches.count})
 print(json.dumps({'saved':False,'source_of_truth':False,'parts':rows,'elapsed_seconds':time.monotonic()-tick}))
'''
r=rpc(s,'frame-deck-native-intent-build',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/frame-deck-native-intent-build.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
for row in record['parts']:fetch(row['path'],Path(row['path']).name)
