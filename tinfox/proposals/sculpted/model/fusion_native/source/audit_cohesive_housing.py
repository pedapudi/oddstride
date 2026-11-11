"""Check the shared structural web and bearing geometry before linkage machining."""
import sys
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent));import cohesive_limb as cl;import integrated_candidate as ic
from audit_part import audit
from audit_sections import audit as sections
blank=cq.Solid.extrudeLinear(cl.shin_outline(51),[],cq.Vector(0,34,0));blank=cq.Workplane(obj=blank).faces('>Y or <Y').edges().fillet(1.2).val();plane=cq.Plane(origin=(0,55,0),xDir=(1,0,0),normal=(0,-1,0));pocket=cq.Workplane(plane).moveTo(-11,-25).lineTo(11,-25).lineTo(8,-128).lineTo(-6,-128).close().extrude(-26).val();pocket=cq.Workplane(obj=pocket).edges('|Y').fillet(4).val();s=blank.cut(pocket)
for z in [-30,-105]:s=s.fuse(ic.cyl(8.6,34,(2,51,z)).intersect(blank))
s=s.cut(ic.cyl(14,11,(0,50,0))).cut(ic.cyl(14,9,(0,77,0))).cut(ic.cyl(8.2,48,(0,44,0))).clean();path=ROOT/'snapshots/cohesive-limb/intent/shin-housing.step';cq.exporters.export(s,str(path));r={'id':'cohesive_shin_housing','source_step':str(path.relative_to(ROOT))};audit('cohesive_shin_housing','cohesive-shin-housing',r);sections('cohesive_shin_housing','cohesive-shin-housing',r)
