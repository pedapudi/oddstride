"""Bound the continuous shoulder profile's difference from the sampled source."""
import math,json
from pathlib import Path
import numpy as np,cadquery as cq
from scipy.spatial import ConvexHull
ROOT=Path(__file__).resolve().parents[1]
pts=[]
for angle in np.deg2rad(np.arange(-61,62)):
 for y,z in [(-51,-55),(-51,55),(111,-55),(111,55)]:pts.append([y*np.cos(angle)-z*np.sin(angle),y*np.sin(angle)+z*np.cos(angle)])
pts=np.array(pts);outline=pts[ConvexHull(pts).vertices].tolist();source=cq.Workplane('YZ').polyline(outline).close().wires().toPending().offset2D(2,kind='arc').extrude(1).val()
R=math.hypot(111,55);r=math.hypot(51,55);A=math.radians(61)+math.atan2(55,111);T=A+math.acos(r/R)
def p(radius,angle,center=(0,0)):return (center[0]+radius*math.cos(angle),center[1]+radius*math.sin(angle))
top=p(R,A);bottom=p(R,-A)
w=cq.Workplane('YZ').moveTo(*p(R+2,-A)).threePointArc(p(R+2,0),p(R+2,A)).threePointArc(p(2,(A+T)/2,top),p(2,T,top)).lineTo(*p(r+2,T)).threePointArc(p(r+2,math.pi),p(r+2,2*math.pi-T)).lineTo(*p(2,2*math.pi-T,bottom)).threePointArc(p(2,2*math.pi-(T+A)/2,bottom),p(2,2*math.pi-A,bottom)).close()
analytic=w.extrude(1).val();rows={}
for name,a,b in [('analytic_to_source',analytic,source),('source_to_analytic',source,analytic)]:
 errors=[]
 for e in a.Edges():
  if e.BoundingBox().xlen>1e-6:continue
  for u in np.linspace(0,1,41):errors.append(b.distance(cq.Vertex.makeVertex(*e.positionAt(float(u)).toTuple())))
 rows[name]=max(errors)
missing=source.cut(analytic).Volume();added=analytic.cut(source).Volume();record={'deviation_mm':rows,'source_not_covered_volume_mm3':missing,'added_clearance_area_mm2':added,'source_clearance_mm':2,'continuous_corner_radii_mm':[R+2,r+2],'passed':missing<1e-5 and max(rows.values())<.005,'scope':'One-millimeter extrusion of the complete YZ clearance profile. The continuous profile conservatively contains the frozen one-degree polygon plus its 2 mm offset.'}
(ROOT/'audits/shoulder-envelope-equivalence.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
