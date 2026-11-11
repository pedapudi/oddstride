"""Verify a three-station construction for the retained end-envelope regions."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
script=(ROOT/'source/intent_geometry.py').read_text()+(ROOT/'source/nose_intent.py').read_text()+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent
 results=[]
 for inset,label,stations in [('0 mm','Compact outer',[236,242]),('nose_wall','Compact inner',[226,236])]:
  occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Temporary '+label;g=IntentGeometry(d,c);n=NoseIntent(g);prefix=label.lower().replace(' ','_')+'_'
  try:
   body=n.hull(inset,label,stations);path=os.path.join(tempfile.gettempdir(),'tinfox-native',label.lower().replace(' ','-')+'-intent.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));results.append({'label':label,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'path':path})
  finally:
   assert occ.deleteMe()
   for p in list(d.userParameters):
    if p.name.startswith(prefix):assert p.deleteMe()
 print(json.dumps({'proofs':results,'temporary_components_removed':True}))
'''
r=rpc(script,'compact-hull-proof',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/compact-hull-proof.json').write_text(json.dumps(record,indent=2))
for row in record['proofs']:fetch(row['path'],Path(row['path']).name)
print(json.dumps(record))
