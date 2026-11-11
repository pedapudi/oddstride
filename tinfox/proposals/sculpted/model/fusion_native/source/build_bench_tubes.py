"""Build simple native cut stock in the existing Leg document."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py','bench_tube_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile,time
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;tick=time.monotonic();made=[]
 # Correct a source-construction label: 40 mm is the original pocket's
 # reference radius, not a verified vendor motor-case dimension.
 p=d.userParameters.itemByName('st_case_radius_nominal')
 if p:p.name='st_case_reference_radius';p.comment='Source pocket construction reference, not a measured vendor envelope. Fit qualification is separate.'
 for key in ['knee_axle','sleeve_0','sleeve_1','pod_sleeve_90','pod_sleeve_210','pod_sleeve_330']:
  assert not any(c.partNumber=='CANDIDATE_bt_'+key for c in d.allComponents);o=root.occurrences.addNewComponent(core.Matrix3D.create());c=o.component;c.name=key.replace('_',' ').title();c.partNumber='CANDIDATE_bt_'+key;BenchTubeIntent(IntentGeometry(d,c)).build(key);made.append((key,o));o.isLightBulbOn=False
 for key,o in list(made):
  no=root.occurrences.addNewComponent(core.Matrix3D.create());c=no.component;c.name='Right '+o.component.name.lower();c.partNumber='CANDIDATE_bt_'+key+'_right';objects=core.ObjectCollection.create()
  for b in o.component.bRepBodies:objects.add(b)
  copy=c.features.copyPasteBodies.add(objects);copy.name='Linked cut-stock family';originals=list(copy.bodies);objects=core.ObjectCollection.create()
  for b in originals:objects.add(b)
  inp=c.features.mirrorFeatures.createInput(objects,c.xZConstructionPlane);inp.isCombine=False;f=c.features.mirrorFeatures.add(inp);f.name='Right-hand stack placement'
  for b in originals:c.features.removeFeatures.add(b).name='Keep the reflected cut-stock length'
  no.isLightBulbOn=False;made.append((key+'_right',no))
 rows=[];paths=[]
 for key,o in made:
  c=o.component;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);o.isLightBulbOn=True
  for b in c.bRepBodies:b.isLightBulbOn=True
  path=os.path.join(tempfile.gettempdir(),'tinfox-native','bench-native-'+key+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>5000;paths.append(path);o.isLightBulbOn=False;rows.append({'part':key,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count})
 print(json.dumps({'saved':False,'parts':rows,'paths':paths,'elapsed_seconds':time.monotonic()-tick,'scope':'Native cut-stock geometry and shared stack expressions; installed assembly, tolerance and strength checks remain separate.'}))
'''
r=rpc(s,'bench-native-cut-stock',timeout=600);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/bench-native-cut-stock.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
for path in record['paths']:fetch(path,Path(path).name)
