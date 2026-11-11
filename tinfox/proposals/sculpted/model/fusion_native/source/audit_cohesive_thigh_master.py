"""Audit the native master against the current shared thigh and its motion tools."""
import hashlib,json,math,sys
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent));import cohesive_limb as cl
from audit_part import audit,cylinders,volume
from audit_sections import audit as sections
assert hashlib.sha256((ROOT.parent/'cohesive_limb.py').read_bytes()).hexdigest()==hashlib.sha256((ROOT/'snapshots/cohesive-limb/source/cohesive_limb.py').read_bytes()).hexdigest()
master,blank=cl.thigh_master();path=ROOT/'snapshots/cohesive-limb/intent/thigh-master.step';cq.exporters.export(master,str(path));rows=[]
for sign in [-1,1]:
 for label,tool in [('connector',cl.sd.connector_parts(54.4,sign)[3]),('cable',cl.sd.cable_space(54.4,sign))]:rows.append({'feature':label,'side':sign,'intersection_mm3':max(0,volume(master.intersect(tool))[0]),'omitted_as_noop':max(0,volume(master.intersect(tool))[0])<1e-6})
upper=math.radians(126);lower=math.radians(234);a=np.array([28*math.cos(upper),28*math.sin(upper)]);b=np.array([28*math.cos(lower),-170+28*math.sin(lower)]);arcs=[]
def arc(c,r,lo,hi):
 def point(t):return cq.Vector(c[0]+r*math.cos(math.radians(t)),65.5,c[1]+r*math.sin(math.radians(t)))
 return cq.Edge.makeThreePointArc(point(lo),point((lo+hi)/2),point(hi))
arcs=[arc(a,9,0,126),arc((0,0),37,126,180),arc((0,-170),37,180,234),arc(b,9,234,360)];edges=[]
for i,e in enumerate(arcs):
 edges.append(e);nextedge=arcs[(i+1)%4]
 if e.endPoint().sub(nextedge.startPoint()).Length>1e-6:edges.append(cq.Edge.makeLine(e.endPoint(),nextedge.startPoint()))
wire=cq.Wire.assembleEdges(edges);tool=cq.Solid.extrudeLinear(wire,[],cq.Vector(0,9,0));cq.exporters.export(tool,str(ROOT/'snapshots/cohesive-limb/intent/thigh-continuous-rod-tool.step'))
points=[]
for knee in range(-156,-47,2):
 a=math.radians(knee-78)
 for dz in [0,-170]:
  x=28*math.cos(a);z=-28*math.sin(a)+dz
  for u in range(0,360,30):points.append((x+9*math.cos(math.radians(u)),z+9*math.sin(math.radians(u))))
points=np.array(points);poly=points[ConvexHull(points).vertices].tolist();plane=cq.Plane(origin=(0,65.5,0),xDir=(1,0,0),normal=(0,-1,0));old=cq.Workplane(plane).polyline(poly).close().extrude(-9).val();proof={'source_outside_native_tool_mm3':max(0,volume(old.cut(tool))[0]),'extra_continuous_tool_mm3':max(0,volume(tool.cut(old))[0]),'unchanged_physical_body_tolerance_mm':.05,'omitted_noop_features':rows};proof['passed']=proof['source_outside_native_tool_mm3']<.001 and all(r['omitted_as_noop'] for r in rows);(ROOT/'audits/cohesive-thigh-clearance-equivalence.json').write_text(json.dumps(proof,indent=2));assert proof['passed'],proof
allow=cylinders(tool)
for radius,z in [(45,0),(19,-170)]:allow.extend(cylinders(cl.cyl(radius,45,(0,51,z))))
ref={'id':'cohesive_thigh_master','source_step':str(path.relative_to(ROOT)),'volume_method':'gauss_kronrod_spans','volume_method_reason':'Explicit B-spline spans avoid source Gauss integration instability; unchanged geometry thresholds.','area_method':'boundary_mesh_convergence','area_method_reason':'Original source area changes by 252.9 mm2 with requested tolerance; see cohesive-thigh-master-area-diagnostic.json. Surface/section and area tolerance unchanged.','functional_clearance_cylinders':allow,'functional_clearance_proof':'audits/cohesive-thigh-clearance-equivalence.json'}
audit('cohesive_thigh_master','cohesive-thigh-master',ref);sections('cohesive_thigh_master','cohesive-thigh-master',ref)
