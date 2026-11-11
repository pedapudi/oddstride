"""Compare native wall offset against the exact cohesive thigh cavity."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent));import cohesive_limb as cl
import cadquery as cq
from audit_part import audit,cylinders
from audit_sections import audit as sections
blank=cl.thigh_outline(9).extrude(-91).val();blank=cq.Workplane(obj=blank).faces('>Y').edges().fillet(7).val();underside=cl.box(220,94,300,(0,0,-90));blank=blank.cut(underside).clean();blank=cq.Workplane(obj=blank).faces('<Y').edges().fillet(4).val();wire=cl.thigh_outline(13).wires().val().offset2D(-4)[0].toNURBS();cavity=cq.Solid.extrudeLinear(wire,[],cq.Vector(0,83,0)).cut(underside.translate((0,4,0)));source=blank.cut(cavity);path=ROOT/'snapshots/cohesive-limb/intent/thigh-hollow.step';cq.exporters.export(source,str(path));allow=[]
for radius,z in [(45,0),(19,-170)]:allow.extend(cylinders(cl.cyl(radius,45,(0,51,z))))
ref={'id':'cohesive_thigh_hollow','source_step':str(path.relative_to(ROOT)),'volume_method':'gauss_kronrod_spans','volume_method_reason':'Explicit B-spline spans avoid source Gauss integration instability; unchanged geometry thresholds.','functional_clearance_cylinders':allow,'functional_clearance_proof':'Wall offset derives radii49-4 and23-4 from native analytic crown arcs; source converted these arcs to NURBS before cavity extrusion. They are structural envelope surfaces, not altered hardware interfaces.'}
audit('cohesive_thigh_hollow','cohesive-thigh-hollow',ref);sections('cohesive_thigh_hollow','cohesive-thigh-hollow',ref)
