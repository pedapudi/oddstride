"""Evaluate candidate washer footprints on the frozen, unmodified shells."""
from pathlib import Path
import sys,json,math
import cadquery as cq
ROOT=Path(__file__).resolve().parents[2]/'proposals/sculpted/model';sys.path.insert(0,str(ROOT));import build as b
base=Path(__file__).resolve().parent/'input-step';rows=[]
for family,tag,x,z in [('thigh',0,-36,-66),('thigh',1,5,-70),('shin',37,2,-30),('shin',105,2,-105)]:
 for side in ['inner','outer']:
  s=cq.importers.importStep(str(base/(family+'_'+side+'.step'))).val()
  y=58 if side=='inner' else 75.9
  record={'family':family,'clamp':tag,'half':side,'center_xz_mm':[x,z]}
  for label,outer in [('nominal',6),('minimum_washer_OD',11.57/2)]:
   ring=b.ring(outer,4.1,.1,y,z,x);area=sum(t.Volume() for t in s.intersect(ring).Solids())/.1
   record[label+'_bearing_area_mm2']=area;record[label+'_full_annulus_mm2']=math.pi*(outer**2-4.1**2)
  # Surface continuity around the proposed enlarged access bore; these are
  # nominal point samples, not proof of a minimum manufactured ligament.
  angles=[]
  for angle in range(0,360,5):
   a=math.radians(angle);p=cq.Vector(x+6.3*math.cos(a),57.5 if side=='inner' else 77.5,z+6.3*math.sin(a))
   if not s.isInside(p):angles.append(angle)
  record['missing_material_angles_at_access_radius6_3mm']=angles
  rows.append(record)
report={'checks':rows,'scope':'Read-only footprint screen on frozen shells before the proposed larger access cuts. Existing CAD material only; compression, print fit, washer bending and post-redesign strength remain unqualified.'}
(Path(__file__).resolve().parent/'washer-land-screen.json').write_text(json.dumps(report,indent=2));print(json.dumps(rows,indent=2))
