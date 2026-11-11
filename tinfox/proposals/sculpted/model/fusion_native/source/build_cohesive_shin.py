"""Start a compact shared shin master inside the existing Leg document."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1];fit=json.loads((ROOT/'snapshots/cohesive-limb/intent/shin-cubic-design-skeleton.json').read_text())
s=(ROOT/'source/intent_geometry.py').read_text()+'\n'+(ROOT/'source/cohesive_limb_intent.py').read_text()+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent
 assert not any(o.component.partNumber=='CANDIDATE_cohesive_shin_master' for o in root.occurrences)
 occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.partNumber='CANDIDATE_cohesive_shin_master';c.name='Cohesive shin - shared native master';g=IntentGeometry(d,c);n=CohesiveLimbIntent(g);body=n.blank(FIT)
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-shin-blank.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c))
 print(json.dumps({'component':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'paths':[path],'saved':False,'source_of_truth_changed':False}))
'''.replace('FIT',repr(fit))
r=rpc(s,'cohesive-shin-blank',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-shin-blank.json').write_text(json.dumps(record,indent=2))
for p in record['paths']:fetch(p,Path(p).name)
print(record)
