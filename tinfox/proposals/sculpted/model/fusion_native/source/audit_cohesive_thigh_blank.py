"""Audit the shared native thigh exterior before adding internal interfaces."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent));import cohesive_limb as cl
import cadquery as cq
from audit_part import audit
from audit_sections import audit as sections
blank=cl.thigh_outline(9).extrude(-91).val();blank=cq.Workplane(obj=blank).faces('>Y').edges().fillet(7).val();blank=blank.cut(cl.box(220,94,300,(0,0,-90))).clean();blank=cq.Workplane(obj=blank).faces('<Y').edges().fillet(4).val();path=ROOT/'snapshots/cohesive-limb/intent/thigh-blank.step';cq.exporters.export(blank,str(path));ref={'id':'cohesive_thigh_blank','source_step':str(path.relative_to(ROOT)),'volume_method':'gauss_kronrod_spans','volume_method_reason':'Source adaptive Gauss volume changes by 1862 mm3 with requested tolerance; explicit B-spline spans converge. See cohesive-thigh-blank-volume-diagnostic.json and cohesive-thigh-blank-gk-diagnostic.json.'}
audit('cohesive_thigh_blank',export_label='cohesive-thigh-blank',reference_override=ref);sections('cohesive_thigh_blank',export_label='cohesive-thigh-blank',reference_override=ref)
