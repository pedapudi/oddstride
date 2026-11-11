"""Include only a source construction datum in the native family derive link."""
import json,sys
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];role=sys.argv[1];assert role in ['leg','head'];header=(ROOT/'source/native_documents.py').read_text()+'\nimport adsk.core as core,adsk.fusion as fusion,json\n'
s=header+'''
def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,ROLE)
 if doc!=app.activeDocument:assert doc.activate()
 print(json.dumps({'active':doc.name}))
'''.replace('ROLE',repr(role))
r=rpc(s,'activate-'+role+'-datum-anchor',timeout=30);assert r[0]['success'],r
s=header+'''
def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,ROLE);assert doc==app.activeDocument;d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();assert d.rootComponent.features.deriveFeatures.count==1;feature=d.rootComponent.features.deriveFeatures.item(0);source=feature.sourceDesign;plane=source.rootComponent.constructionPlanes.itemByName('Front hip family datum');assert plane;assert not feature.sourceEntities;before=sum(c.bRepBodies.count for c in d.allComponents);assert feature.setSourceEntities([plane],[]);assert d.computeAll();assert before==sum(c.bRepBodies.count for c in d.allComponents);assert feature.bodies.count==0;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for c in d.allComponents for f in c.features);print(json.dumps({'passed':True,'role':ROLE,'source_entities':[e.objectType for e in feature.sourceEntities],'source_version':feature.documentReference.version,'derived_parameters':[{'name':p.name,'value':p.value} for p in d.derivedParameters],'body_count_unchanged':True,'saved':False}))
'''.replace('ROLE',repr(role))
r=rpc(s,role+'-shared-datum-plane-anchor',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits'/f'{role}-shared-datum-plane-anchor.json').write_text(json.dumps(record,indent=2));print(record)
