"""Prove a short native construction for the unchanged lower enclosure."""
import json,gzip,sys
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
import build as b,service_design as sd
from audit_part import volume
model=json.loads(gzip.decompress((ROOT/'snapshots/cohesive-limb/model.json.gz').read_bytes()));b.P.update(model['parameters'])
def box(*args):return b.box(*args)
outer=cq.Solid.extrudeLinear(b.body_section(-125.4),[],cq.Vector(250.8,0,0));inner=cq.Solid.extrudeLinear(b.body_section(-126.4,2.8),[],cq.Vector(252.8,0,0));s=outer.cut(inner).intersect(box(270,250,38,(0,0,-29.3)))
for front in [-1,1]:
 for side in [-1,1]:
  for r,length,start in [(41.25,49.4,70.3),(42,7,111.7),(38,20,113.5)]:s=s.cut(b.cyl(r,length,(front*start,side*68,0),(front,0,0)))
omitted=[]
for front in [-1,1]:
 for side in [-1,1]:
  for z in [-12,24]:omitted.append({'tool':'ear','front':front,'side':side,'z':z,'overlap_mm3':s.intersect(box(14,16,14,(front*125.5,side*94.5,z))).Volume()})
for y in [-102,102]:omitted.append({'tool':'rail','y':y,'overlap_mm3':s.intersect(box(268,3,55,(0,y,8),.8)).Volume()})
# The aperture's top/bottom blends lie outside the retained wall material.
tool=cq.Workplane('XY',origin=(0,0,-100)).rect(148,202).extrude(80).edges('|Z').fillet(8).val();s=s.cut(tool)
for front in [-1,1]:
 for side in [-1,1]:
  for sign in [-1,1]:
   tool=sd.connector_parts(0,sign)[3].rotate((0,0,0),(0,0,1),-90).translate((-67.3,0,0))
   if front<0:tool=tool.mirror('YZ')
   if side<0:tool=tool.mirror('XZ')
   tool=tool.translate((front*185,side*68,0))
   if sign<0:s=s.cut(tool)
   else:omitted.append({'tool':'upper connector','front':front,'side':side,'overlap_mm3':s.intersect(tool).Volume()})
s=s.clean();target=next(p for p in json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low']['custom_parts'] if p['key']=='belly_center_0');reference=cq.importers.importStep(str(ROOT/target['files']['step']['path'])).val();sv,nv=volume(reference)[0],volume(s)[0];errors=[]
for a,z in [(reference,s),(s,reference)]:
 points,_=a.tessellate(.025,.05);boundary=cq.Compound.makeCompound(z.Faces());errors.extend(boundary.distance(cq.Vertex.makeVertex(*v.toTuple())) for v in points[::max(1,len(points)//800)])
report={'valid':s.isValid(),'solids':len(s.Solids()),'source_volume_mm3':sv,'volume_mm3':nv,'relative_volume_error':abs(nv-sv)/sv,'maximum_boundary_error_mm':max(errors),'omitted_tool_intersections':omitted,'passed':s.isValid() and len(s.Solids())==1 and abs(nv-sv)/sv<.0001 and max(errors)<.005 and max(row['overlap_mm3'] for row in omitted)<.001};(ROOT/'audits/compact-lower-shell-local-replay.json').write_text(json.dumps(report,indent=2));cq.exporters.export(s,str(ROOT/'snapshots/current-targets/compact-lower-shell.step'));print(report)
