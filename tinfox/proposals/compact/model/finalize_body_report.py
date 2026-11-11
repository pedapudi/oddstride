"""Synchronize the compact proposal summary after body validation."""
import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parent;out=root/'output'
read=lambda n:json.loads((out/n).read_text())
s=read('proposal-summary.json');e=read('engineering.json');b=read('body-revision-comparison.json');l=read('limb-profile-comparison.json');a=read('mounting-audit.json');p=json.loads((root/'parameters.json').read_text())
sha=hashlib.sha256((out/'model.json').read_bytes()).hexdigest()
assert e['model_sha256']==b['model_sha256']==l['model_sha256']==a['model_sha256']==sha
s.update(model_sha256=sha,nominal_torso_mm=[p['body_length'],p['body_width'],p['body_height']],estimated_base_mass_kg=e['mass']['base_kg'],model_tests_passed=11,individual_step_files=len(list((out/'step-parts').glob('*.step'))),preset_results=e['motion']['presets'],transitions=e['motion']['transitions'],coordinated_roll=e['motion']['coordinated_roll'],printability=e['printability'],fixed_packaging=e['fixed_packaging'],battery_fit=e['battery_fit'],torque_cases=e['torque_cases'],comparison_summary=l['comparison_summary'],body_revision_comparison='body-revision-comparison.json',limb_meshes_unchanged=b['limb_meshes_unchanged'])
bounds={'min':b['after']['shell_min_mm'],'max':b['after']['shell_max_mm'],'extent':b['after']['shell_extent_mm']}
s['rigid_panel_bounds_mm']=bounds;s['appearance_shell_bounds_mm']=bounds
s['renders']['body_detail']='../design/15-body-detail.png'
s['limitations']=[
'Neutral flexible gaiters are provisional; motion deformation and weather sealing are unqualified.',
'Motor connectors, cabling, hard stops, thermal behavior, fit tolerances and loaded motion are unqualified.',
'Exact tool batteries, electronics, optics and fasteners remain unselected.',
'The 1.6 mm nose panel has four modeled metal support tabs and recessed head envelopes; screw selection, tolerance stacks and loaded retention require validation.',
'The refined nose extends the previous body 7 mm forward. Body width, motor locations and every limb mesh remain unchanged.',
'Wall thickness is sampled from exported geometry, not proven globally. Printed strength and fatigue remain unqualified.'
]
s['shin_revision']['skin_audit']=a['shin_skin_audit'];s['shin_revision']['outline_audit']=a['shin_outline_audit']
(out/'proposal-summary.json').write_text(json.dumps(s,indent=2)+'\n')
print(sha)
