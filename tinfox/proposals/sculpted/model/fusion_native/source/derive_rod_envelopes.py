"""Replace sampled rod-clearance hulls with continuous arcs and tangent lines."""
import json,math,sys
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent));import cohesive_limb as cl;import integrated_candidate as ic
p=ic.PIN;lo,hi=map(math.radians,[-156,-48]);base=math.atan2(12,3);tip=math.atan2(158,3);midr=math.hypot(3,12);outer=math.hypot(3,158);small=7.5;alpha=math.acos(small/midr)
def point(r,a):return cq.Vector(p[0]+r*math.cos(a),66.5,p[1]+r*math.sin(a))
def arc(r,a,b):return cq.Edge.makeThreePointArc(point(r,a),point(r,(a+b)/2),point(r,b))
def line(r,a,s,b):return cq.Edge.makeLine(point(r,a),point(s,b))
# Four and six master curves; the one-millimetre round offset is explicit.
stem=[line(midr,base+lo,outer,tip+lo),arc(outer,tip+lo,math.pi-tip+hi),line(outer,math.pi-tip+hi,midr,math.pi-base+hi),line(midr,math.pi-base+hi,midr,base+lo)]
taper=[line(small,math.pi+hi,small,lo),arc(small,lo,base+lo-alpha),line(small,base+lo-alpha,midr,base+lo),arc(midr,base+lo,math.pi-base+hi),line(midr,math.pi-base+hi,small,math.pi-base+hi+alpha),arc(small,math.pi-base+hi+alpha,math.pi+hi)]
solids=[];counts=[]
for name,edges in [('stem',stem),('taper',taper)]:
 wire=cq.Wire.assembleEdges(edges);offset=wire.offset2D(1,kind='arc')[0];assert cq.Face.makeFromWires(offset).Area()>cq.Face.makeFromWires(wire).Area();solid=cq.Solid.extrudeLinear(offset,[],cq.Vector(0,7,0));solids.append(solid);counts.append({'name':name,'master_curves':len(edges),'offset_curves':len(offset.Edges())})
continuous=solids[0].fuse(solids[1],ic.cyl(8.5,7,(p[0],66.5,p[1])),ic.cyl(6.3,8.4,(p[0],65.8,p[1]))).clean();source=cl.shin_linkage_space();uncovered=source.cut(continuous).Volume();extra=continuous.cut(source).Volume()
path=ROOT/'snapshots/cohesive-limb/intent';cq.exporters.export(continuous,str(path/'continuous-rod-clearance.step'));cq.exporters.export(source,str(path/'sampled-rod-clearance.step'))
record={'construction':counts,'source_outside_continuous_mm3':uncovered,'additional_clearance_mm3':extra,'analytical_boundary_error_bound_mm':outer*(1-math.cos(math.radians(.5)))+1-math.cos(math.radians(15)),'purpose':'Continuous conservative motion envelope, replacing one-degree rotation samples and twelve-point offset circles. Bearing shoulders remain outside this axial channel.','passed':uncovered<1e-5 and outer*(1-math.cos(math.radians(.5)))+1-math.cos(math.radians(15))<.05};(ROOT/'audits/cohesive-rod-envelope-equivalence.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
