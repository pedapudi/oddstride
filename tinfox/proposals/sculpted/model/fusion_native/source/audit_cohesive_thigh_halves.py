"""Check the complete native thigh shells against their frozen current STEP files."""
from pathlib import Path
import cadquery as cq
from audit_part import audit,cylinders
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1];allow=cylinders(cq.importers.importStep(str(ROOT/'snapshots/cohesive-limb/intent/thigh-continuous-rod-tool.step')).val())
for radius,z in [(45,0),(19,-170)]:allow.extend(cylinders(cq.Solid.makeCylinder(radius,45,cq.Vector(0,51,z),cq.Vector(0,1,0))))
for side in ['inner','outer','inner_right','outer_right']:
 ref={'id':'cohesive_thigh_'+side,'source_step':f'snapshots/cohesive-limb/step/thigh_{side}.step','volume_method':'gauss_kronrod_spans','volume_method_reason':'Converged span-aware integration supplements unstable source ordinary Gauss integration.','area_method':'boundary_mesh_convergence','area_method_reason':'Three-resolution boundary integration with explicit convergence allowance; ordinary source area quadrature is unstable.','functional_clearance_cylinders':allow,'functional_clearance_proof':'audits/cohesive-thigh-clearance-equivalence.json'}
 label='cohesive-thigh-'+side.replace('_','-')+'-final';audit('cohesive_thigh_'+side,label,ref);sections('cohesive_thigh_'+side,label,ref)
