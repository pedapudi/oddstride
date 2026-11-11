"""Bind the body revision, attachment checks and mobility comparison to final CAD."""
import json,hashlib
import numpy as np
from kinematics import ROOT
baseline=ROOT.parent/'design/iterations/refinement-baseline'
old={'model':json.loads((baseline/'model.json').read_text()),'engineering':json.loads((baseline/'engineering.json').read_text()),'model_sha256':hashlib.sha256((baseline/'model.json').read_bytes()).hexdigest()}
new=json.loads((ROOT/'output/model.json').read_text())
engineering=json.loads((ROOT/'output/engineering.json').read_text())
fit=json.loads((ROOT/'output/mounting-fit.json').read_text())
skin=json.loads((ROOT/'output/body-skin-audit.json').read_text())
hash_now=hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest()
assert engineering['model_sha256']==fit['model_sha256']==skin['model_sha256']==hash_now

def canonical(mesh):
    vertices=[tuple(round(x,8) for x in v) for v in mesh['vertices']]
    return sorted(tuple(sorted(vertices[i] for i in face)) for face in mesh['faces'])
previous_parts={p['name']:p for p in old['model']['parts']}
limb_changes=[]
for part in new['parts']:
    if not part['leg']:continue
    if part['name'] not in previous_parts:
        assert any(t in part['name'] for t in ['_axle_bolt','_axle_nut','_shin_clamp_','_output_pivot_nut','_shin_join_','_bearing_inner','_bearing_outer','_shin_shell','_knee_retaining_ring','_motor_service_ring','_knee_head','_input_pin','_output_pin','_rod_bush_','_shin_head_','_bearing_70','_bearing_90']);limb_changes.append(part['name']);continue
    before=previous_parts[part['name']]
    a=old['model']['meshes'][before['mesh']];b=new['meshes'][part['mesh']]
    if a!=b and canonical(a)!=canonical(b):limb_changes.append(part['name'])

def dimensions(model,report):
    names=['body_aft_','body_center_','body_front_','belly_aft_','belly_center_','belly_front_']
    selected=[p for p in model['parts'] if any(p['name'].startswith(prefix) for prefix in names) or p['name'] in ['body_nose_surround','front_fascia']]
    vertices=np.vstack([model['meshes'][p['mesh']]['vertices'] for p in selected])
    lower=vertices.min(axis=0);upper=vertices.max(axis=0)
    fascia=next(p for p in model['parts'] if p['name']=='front_fascia')
    return {'rigid_shell_dimensions_xyz_mm':(upper-lower).tolist(),'rigid_shell_bounds_mm':[lower.tolist(),upper.tolist()],
            'body_shell_and_fascia_mass_kg':sum(p['mass_kg'] for p in selected),
            'battery_side_panels_mass_kg':sum(p['mass_kg'] for p in model['parts'] if p['name'].startswith('battery_side_panel_')),
            'front_fascia_bounds_xyz_mm':fascia['bounds_mm'],'complete_base_mass_kg':report['mass']['base_kg']}

before=dimensions(old['model'],old['engineering']);after=dimensions(new,engineering)
changes=[]
for leg,before_leg in old['engineering']['motion']['joint_sweeps'].items():
    for joint,check in before_leg.items():
        previous=check['clear_intervals_deg'];current=engineering['motion']['joint_sweeps'][leg][joint]['clear_intervals_deg']
        if previous!=current:changes.append({'check':f'{leg} {joint} single-joint sweep','before_deg':previous,'after_deg':current})
for leg,check in old['engineering']['motion']['folded_hip_sweeps'].items():
    previous=check['clear_intervals_deg'];current=engineering['motion']['folded_hip_sweeps'][leg]['clear_intervals_deg']
    if previous!=current:changes.append({'check':f'{leg} hip sweep with folded knee','before_deg':previous,'after_deg':current})
previous=old['engineering']['motion']['coordinated_roll']['clear_intervals_deg'];current=engineering['motion']['coordinated_roll']['clear_intervals_deg']
if previous!=current:changes.append({'check':'coordinated roll','before_deg':previous,'after_deg':current})

report={'baseline_model_sha256':old['model_sha256'],'model_sha256':hash_now,
 'limb_meshes_unchanged':not limb_changes,'changed_limb_meshes':limb_changes,
 'before':before,'after':after,
 'body_mass_delta_kg':after['body_shell_and_fascia_mass_kg']-before['body_shell_and_fascia_mass_kg'],
 'front_opening_width_mm':{'before':168,'after':168},
 'front_face_nominal_crown_mm':8,'front_face_vertical_crown_mm':10,'fascia_corner_radius_mm':16,'nominal_front_corner_radius_mm':18,'central_roof_height_mm':49.5,'shoulder_crown_height_mm':55.5,
 'fit_checks':[check for check in fit['pairs'] if 'body_nose_surround' in check['parts']],
 'skin_checks':{'nominal_envelope_min_mm':skin['nominal_skin_min_mm'],'finished_fascia_min_mm':skin['finished_fascia_min_mm'],
                'return_tongue_min_sampled_section_mm2':skin['minimum_return_tongue_section_mm2'],
                'sample_count':len(skin['nominal_skin_samples'])+len(skin['finished_fascia_samples'])+len(skin['return_tongue_samples']),
                'scope':skin['scope']},
 'preset_minimum_gap_mm':{name:value['minimum_distance_mm'] for name,value in engineering['motion']['presets'].items()},
 'transition_intersections':sum(value['collision_samples'] for value in engineering['motion']['transitions'].values()),
 'joint_interval_changes':changes,
 'battery_fit':engineering['battery_fit'],'fixed_packaging':engineering['fixed_packaging'],'printability':engineering['printability'],
 'scope':'Actual CAD meshes, exact-solid interface checks and sampled CAD skin paths. Sweeps compare the same joint definitions and sample spacing. No loaded locomotion, deformation, sealing or final fastener qualification.'}
(ROOT/'output/body-revision-comparison.json').write_text(json.dumps(report,indent=2))
assert any(n.endswith('_shin_inner') for n in limb_changes)
print('Body mass change',report['body_mass_delta_kg'],'kg; declared limb surface changes; interval changes:',changes)
