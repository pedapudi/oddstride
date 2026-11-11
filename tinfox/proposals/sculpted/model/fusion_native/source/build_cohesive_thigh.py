"""Start the thigh's shared native envelope in the existing Leg document."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1];fit=json.loads((ROOT/'snapshots/cohesive-limb/intent/thigh-cubic-design-skeleton.json').read_text())
s='\n'.join((ROOT/'source'/p).read_text() for p in ['intent_geometry.py','cohesive_limb_intent.py','cohesive_thigh_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert not any(o.component.partNumber=='CANDIDATE_cohesive_thigh_master' for o in root.occurrences)
 occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.partNumber='CANDIDATE_cohesive_thigh_master';c.name='Thigh shared design master';g=IntentGeometry(d,c);n=CohesiveThighIntent(g);body=n.thigh_blank(FIT)
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-thigh-blank.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));print(json.dumps({'part':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'paths':[path],'saved':False}))
'''.replace('FIT',repr(fit))
r=rpc(s,'cohesive-thigh-blank',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-thigh-blank.json').write_text(json.dumps(record,indent=2));print(record)
for path in record['paths']:fetch(path,Path(path).name)
