"""Replace the empty reference study with a saved native datum-plane link."""
import json,sys
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];role=sys.argv[1];assert role in ['leg','head'];record=json.loads((ROOT/'audits'/f'{role}-shared-robot-datum-link.json').read_text());bindings=record['bindings'];header=(ROOT/'source/native_documents.py').read_text()+'\nimport adsk.core as core,adsk.fusion as fusion,json\n'
s=header+'''
def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,ROLE)
 if doc!=app.activeDocument:assert doc.activate()
 print(json.dumps({'active':doc.name}))
'''.replace('ROLE',repr(role))
r=rpc(s,'activate-'+role+'-replace-datum-link',timeout=30);assert r[0]['success'],r
s=header+'''
def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,ROLE);assert doc==app.activeDocument;d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;assert root.features.deriveFeatures.count==1;old=root.features.deriveFeatures.item(0);assert old.bodies.count==0 and not old.sourceEntities;before={c.partNumber:(c.features.count,c.sketches.count,c.bRepBodies.count) for c in d.allComponents if c!=root}
 for row in BINDINGS:d.userParameters.itemByName(row['parameter']).expression=row['before']
 assert old.deleteMe();assert not list(d.derivedParameters);source_doc=authoring_document(app,'chassis');assert source_doc.dataFile.isComplete and not source_doc.isModified;source=fusion.Design.cast(source_doc.products.itemByProductType('DesignProductType'));plane=source.rootComponent.constructionPlanes.itemByName('Front hip family datum');assert plane;inp=root.features.deriveFeatures.createInput(source);inp.sourceEntities=[plane];inp.isIncludeFavoriteParameters=True;inp.isIncludeComponentParameters=False;feature=root.features.deriveFeatures.add(inp);assert feature and feature.bodies.count==0;assert len(feature.sourceEntities)==1;assert len(list(d.derivedParameters))==8
 for row in BINDINGS:d.userParameters.itemByName(row['parameter']).expression=row['expression']
 assert d.computeAll();after={c.partNumber:(c.features.count,c.sketches.count,c.bRepBodies.count) for c in d.allComponents if c!=root};assert before==after
 for c in d.allComponents:
  assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),c.name
  for pl in c.constructionPlanes:pl.isLightBulbOn=False
 print(json.dumps({'passed':True,'saved':False,'role':ROLE,'source_version':source_doc.dataFile.versionNumber,'source_entities':[e.objectType for e in feature.sourceEntities],'native_histories_preserved':True,'geometry_bodies_added':feature.bodies.count,'parameters':[p.name for p in d.derivedParameters]}))
'''.replace('ROLE',repr(role)).replace('BINDINGS',repr(bindings))
r=rpc(s,role+'-native-plane-datum-link',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits'/f'{role}-native-plane-datum-link.json').write_text(json.dumps(record,indent=2));print(record)
