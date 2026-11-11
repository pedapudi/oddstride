"""Replace only the generated nose work with source-qualified short hull lofts."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
for label in ['compact-outer-intent','compact-inner-intent']:
 assert json.loads((ROOT/f'audits/{label}-geometry.json').read_text())['passed']
script=(ROOT/'source/intent_geometry.py').read_text()+(ROOT/'source/nose_intent.py').read_text()+'''
def run(_context: str):
 import json
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent
 old=next(o for o in root.occurrences if o.component.partNumber=='CANDIDATE_body_nose_surround');assert old.component.features.count==24 and old.component.bRepBodies.count==1;before={'features':old.component.features.count,'sketches':old.component.sketches.count};assert old.deleteMe()
 removed=[]
 for p in list(d.userParameters):
  if p.name.startswith(('nose_outer_','nose_inner_')):name=p.name;assert p.deleteMe();removed.append(name)
 occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Nose surround - native construction review';c.partNumber='CANDIDATE_body_nose_surround';g=IntentGeometry(d,c);n=NoseIntent(g)
 outer=n.hull('0 mm','Nose outer',[236,242]);outer.name='Outer hull construction';inner=n.hull('nose_wall','Nose inner',[226,236]);inner.name='Inner hull construction';occ.isLightBulbOn=False
 print(json.dumps({'removed_work':before,'removed_obsolete_station_parameters':len(removed),'rebuilt_hull_features':c.features.count,'rebuilt_hull_sketches':c.sketches.count,'saved':False}))
'''
r=rpc(script,'nose-compact-rebuild',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/nose-compact-rebuild.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
