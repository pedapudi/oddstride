"""Verify a native spatial guide's dimensional coordinates and edit response."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
script=(ROOT/'source/intent_geometry.py').read_text()+'''
def run(_context: str):
 import json
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);occ=d.rootComponent.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Temporary spatial guide proof';g=IntentGeometry(d,c);g.parameter('proof_guide_shift',0)
 try:
  coordinates=[['nose_bridge_guide_x_'+str(i+1),'nose_bridge_guide_half_width_'+str(i+1)+' - 2 mm','nose_bridge_guide_roof_'+str(i+1)+' + proof_guide_shift'] for i in range(6)];spline=g.control_spline_3d(coordinates,'Spatial crown edge')
  def error():return max(p.geometry.distanceTo(core.Point3D.create(*[g.mm(e)*.1 for e in row]))*10 for p,row in zip(spline.controlPoints,coordinates))
  before=error();d.userParameters.itemByName('proof_guide_shift').expression='1 mm';d.computeAll();changed=error();d.userParameters.itemByName('proof_guide_shift').expression='0 mm';d.computeAll();restored=error();assert max(before,changed,restored)<1e-5
  print(json.dumps({'before_error_mm':before,'changed_error_mm':changed,'restored_error_mm':restored,'entities':c.sketches.item(0).sketchCurves.count,'passed':True}))
 finally:assert occ.deleteMe();assert d.userParameters.itemByName('proof_guide_shift').deleteMe()
'''
r=rpc(script,'spatial-guide-proof',timeout=120);print(json.dumps(r))
