"""Cut an analytic continuous pushrod envelope instead of a polygonal replay."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text() for p in ['intent_geometry.py','cohesive_limb_intent.py','cohesive_thigh_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);c=next(o.component for o in d.rootComponent.occurrences if o.component.partNumber=='CANDIDATE_cohesive_thigh_master');assert c.features.count==22;g=IntentGeometry(d,c);n=CohesiveThighIntent(g);body=n.thigh_rod_space(c.bRepBodies.item(0));path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-thigh-rod-space.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));print(json.dumps({'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'paths':[path],'saved':False}))
'''
r=rpc(s,'cohesive-thigh-rod-space',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-thigh-rod-space.json').write_text(json.dumps(record,indent=2));print(record)
for path in record['paths']:fetch(path,Path(path).name)
