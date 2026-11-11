"""Add functional housing and bearing geometry to the shared native shin master."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/intent_geometry.py').read_text()+'\n'+(ROOT/'source/cohesive_limb_intent.py').read_text()+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);c=next(o.component for o in d.rootComponent.occurrences if o.component.partNumber=='CANDIDATE_cohesive_shin_master');assert c.features.count==2
 g=IntentGeometry(d,c);n=CohesiveLimbIntent(g);body=n.housing(c.bRepBodies.item(0));assert c.bRepBodies.count==1
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-shin-housing.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c))
 print(json.dumps({'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'paths':[path],'saved':False}))
'''
r=rpc(s,'cohesive-shin-housing',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-shin-housing.json').write_text(json.dumps(record,indent=2))
for p in record['paths']:fetch(p,Path(p).name)
print(record)
