"""Build and export the original analytical hull as native design features."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
script=(ROOT/'source/intent_geometry.py').read_text()+(ROOT/'source/nose_intent.py').read_text()+'''
def run(_context: str):
 import os,tempfile,json
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent
 assert not any(o.component.partNumber=='CANDIDATE_body_nose_surround' for o in root.occurrences)
 occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Nose surround - native construction review';c.partNumber='CANDIDATE_body_nose_surround';g=IntentGeometry(d,c);n=NoseIntent(g)
 body=n.hull('0 mm','Nose outer');assert d.computeAll();issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues
 body.name='Outer hull construction';path=os.path.join(tempfile.gettempdir(),'tinfox-native','nose-outer-intent.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));occ.isLightBulbOn=False
 print(json.dumps({'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'path':path,'saved':False}))
'''
r=rpc(script,'nose-outer-intent',timeout=180);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/nose-outer-intent-build.json').write_text(json.dumps(record,indent=2));fetch(record['path'],Path(record['path']).name);print(json.dumps(record))
