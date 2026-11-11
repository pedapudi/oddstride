"""Check compact analytic hull-profile construction and dimensional dependency."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
script=(ROOT/'source/intent_geometry.py').read_text()+'''
def run(_context: str):
 import json
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct)
 occ=d.rootComponent.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Temporary hull profile proof';g=IntentGeometry(d,c);names=[]
 try:
  for name,value in {'proof_hull_width':202,'proof_hull_roof':45.5,'proof_hull_floor':-44,'proof_hull_top_bevel':10.8,'proof_hull_bottom_bevel':10.8,'proof_hull_radius':18}.items():g.parameter(name,value);names.append(name)
  plane=g.plane(c.yZConstructionPlane,'240 mm','Hull profile datum')
  sk=g.rounded_octagon(plane,'proof_hull_width / 2','proof_hull_roof','proof_hull_floor','proof_hull_top_bevel','proof_hull_bottom_bevel','proof_hull_radius','Hull profile')
  g.extrude(sk,'5 mm','Profile proof stock')
  def vol():return c.bRepBodies.item(0).volume*1000
  before=vol();p=d.userParameters.itemByName('proof_hull_width');p.expression='208 mm';d.computeAll();changed=vol();p.expression='202 mm';d.computeAll();restored=vol();assert abs(changed-before)>1 and abs(restored-before)<.001
  print(json.dumps({'profiles':sk.profiles.count,'entities':sk.sketchCurves.count,'dimensions':sk.sketchDimensions.count,'before':before,'changed':changed,'restored':restored,'passed':True}))
 finally:
  assert occ.deleteMe()
  for name in reversed(names):assert d.userParameters.itemByName(name).deleteMe()
'''
r=rpc(script,'octagon-intent-proof',timeout=120);print(json.dumps(r))
