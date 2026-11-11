"""Audit the native paired current cranks and repaired foot link."""
from pathlib import Path
import cadquery as cq
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1]
right=ROOT/'snapshots/cohesive-limb/step/input_crank_right.step'
if not right.exists():cq.exporters.export(cq.importers.importStep(str(ROOT/'snapshots/cohesive-limb/step/input_crank.step')).val().mirror('XZ'),str(right))
for key,label,ref in [('cohesive_input_crank','cohesive-input-crank',{'id':'cohesive_input_crank','source_step':'snapshots/cohesive-limb/step/input_crank.step'}),('cohesive_input_crank_right','cohesive-input-crank-right',{'id':'cohesive_input_crank_right','source_step':'snapshots/cohesive-limb/step/input_crank_right.step'}),('foot_right','foot-right-repaired',None)]:
 audit(key,label,ref);sections(key,label,ref)
