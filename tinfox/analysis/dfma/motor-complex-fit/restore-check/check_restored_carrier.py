"""Read-only comparison of pre-edit and post-restore native carrier solids."""
from pathlib import Path
import hashlib,json,shutil,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]/'proposals/sculpted/model'
NATIVE=ROOT/'fusion_native'
sys.path.insert(0,str(NATIVE/'source'))
import audit_part
import audit_sections

PART='motor_carrier_1'
PRE=HERE/'input-pre'/f'{PART}.step'
POST=NATIVE/'exports/motor-complex-post-restore-motor_carrier_1.step'
PRE_SHA='b4d3fa0141de0d3b877e1bfaaff0440a3edf00a92207b44899f0f57a88b3c721'
POST_SHA='494774b9043435aa75deceb844b74b353eb592ec83329f15620c1771bea1f9a6'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(PRE)==PRE_SHA
assert sha(POST)==POST_SHA
(HERE/'exports').mkdir(exist_ok=True);(HERE/'audits').mkdir(exist_ok=True)
label='post-restore-motor_carrier_1'
frozen_post=HERE/'exports'/f'{label}.step';shutil.copy2(POST,frozen_post)
# Redirect existing read-only check functions' output roots into this audit's
# workspace. Neither the shared checker sources nor native export files change.
audit_part.NATIVE=HERE
audit_sections.ROOT=HERE
reference=dict(id=PART,source_step=str(PRE.resolve()),skip_legacy_probes=True,
 volume_method='gauss_kronrod_spans',
 volume_method_reason='Independent converged integration of native physical-property restoration drift; all geometric thresholds remain unchanged.',
 source_reference_note='Frozen saved Leg19 native carrier versus owner-identified nonempty post-restore carrier export. No generated geometry substituted.')
geometry=audit_part.audit(PART,label,reference)
sections=audit_sections.audit(PART,label,reference)
volume_delta=abs(geometry['source_volume_mm3']-geometry['native_volume_mm3'])
bounds_delta=geometry['conservative_brep_bounds_error_max_mm']
native_bounds_pass=bounds_delta<.00001
independent_volume_pass=volume_delta<.002
owner_diag=NATIVE/'audits/motor-complex-post-restore-solid.json'
if owner_diag.exists():shutil.copy2(owner_diag,HERE/'owner-post-restore-solid.json')
result=dict(part=PART,
 scope='Independent numerical and exported-surface restoration audit only. No geometry changes, tolerance changes, MCP access, release preparation or authority change.',
 before=dict(path=str(PRE),sha256=sha(PRE)),after=dict(path=str(frozen_post),source_path=str(POST),sha256=sha(frozen_post)),
 preserved_native_diagnostics=[
  dict(path=str(HERE/'input-pre/motor-complex-family-low-accuracy-diagnostic.json'),sha256=sha(HERE/'input-pre/motor-complex-family-low-accuracy-diagnostic.json'),accuracy='default',maximum_native_volume_delta_mm3=.04282450409664307,bounds_delta_mm=0,absolute_volume_threshold_mm3=.002,passed=False),
  dict(path=str(HERE/'input-pre/motor-complex-family-very-high-diagnostic.json'),sha256=sha(HERE/'input-pre/motor-complex-family-very-high-diagnostic.json'),accuracy='VeryHigh',maximum_native_volume_delta_mm3=.007148320277337916,bounds_delta_mm=0,absolute_volume_threshold_mm3=.002,passed=False)],
 excluded_empty_export=json.loads((HERE/'excluded-empty-export.json').read_text()),
 exact_solid_validity_passed=geometry['source_solid_count']==geometry['native_solid_count']==1,
 native_restore_bounds_gate=dict(maximum_error_mm=bounds_delta,threshold_mm=.00001,passed=native_bounds_pass),
 independent_span_volume_restore_gate=dict(before_mm3=geometry['source_volume_mm3'],after_mm3=geometry['native_volume_mm3'],absolute_difference_mm3=volume_delta,threshold_mm3=.002,passed=independent_volume_pass,integration=geometry['volume_integration']),
 existing_translation_gates=dict(geometry_passed=geometry['geometric_gate_passed'],sections_passed=sections['section_gate_passed'],geometry_tolerances=geometry['tolerances'],section_tolerances=sections['tolerances']),
 independent_restored_geometry_passed=bool(native_bounds_pass and independent_volume_pass and geometry['geometric_gate_passed'] and sections['section_gate_passed']),
 geometry_report=dict(path=str(HERE/'audits'/f'{label}-geometry.json'),sha256=sha(HERE/'audits'/f'{label}-geometry.json')),
 sections_report=dict(path=str(HERE/'audits'/f'{label}-sections.json'),sha256=sha(HERE/'audits'/f'{label}-sections.json')),
 limitations=['Both original native physical-property assertions remain recorded as failures. The independent method does not rewrite them.',
 'The owner reports this final post-restore body matches the native fingerprints after both span and M4-clearance restore checkpoints. The comparison directly certifies only the two retained STEP inputs.',
 'Surface and section samples are finite. This audit does not certify physical strength, manufacturing fits, or other components.'])
assert sha(PRE)==PRE_SHA and sha(POST)==POST_SHA
(HERE/'restoration-validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(passed=result['independent_restored_geometry_passed'],span_volume_delta_mm3=volume_delta,bounds_delta_mm=bounds_delta,
 surface_max_mm=max(r['max_mm'] for r in geometry['surface_deviation'].values()),section_max_mm=max(r['symmetric_sampled_error_max_mm'] for r in sections['sections'])),indent=2))
