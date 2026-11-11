"""Compare the refined body with the preserved pre-body revision."""
import json,hashlib
import numpy as np
import fcl
from kinematics import ROOT,POSES
from collision import Checker
OUT=ROOT/'output';raw=(OUT/'model.json').read_bytes();sha=hashlib.sha256(raw).hexdigest();model=json.loads(raw)
before=json.loads((ROOT.parent/'analysis/09-body-baseline.json').read_text());engineering=json.loads((OUT/'engineering.json').read_text());fit=json.loads((OUT/'body-fit.json').read_text())
assert engineering['model_sha256']==fit['model_sha256']==sha

def dimensions(data):
    covers=[p for p in data['parts'] if p['name'].startswith(('body_','belly_')) and p['material']=='petg']
    vertices=np.vstack([data['meshes'][p['mesh']]['vertices'] for p in covers]);low=vertices.min(0);high=vertices.max(0)
    end=vertices[vertices[:,0]>high[0]-.03]
    panel=next(p for p in data['parts'] if p['name']=='nose_panel');glass=next(p for p in data['parts'] if p['name']=='sensor_window')
    return {'shell_min_mm':low.tolist(),'shell_max_mm':high.tolist(),'shell_extent_mm':(high-low).tolist(),'front_plane_y_span_mm':float(np.ptp(end[:,1])),
            'nose_panel_bounds_mm':panel['bounds_mm'],'sensor_window_bounds_mm':glass['bounds_mm'],
            'rigid_cover_and_face_mass_kg':sum(p['mass_kg'] for p in covers)+panel['mass_kg'],
            'printed_body_parts_mass_kg':sum(p['mass_kg'] for p in data['parts'] if not p['leg'] and p['material']=='petg')}

changed=[]
for key,digest in before['limb_mesh_sha256'].items():
    current=hashlib.sha256(json.dumps(model['meshes'][key],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if current!=digest:changed.append(key)
assert not changed,changed
old=dimensions(before);new=dimensions(model)
old['base_mass_kg']=before['engineering']['mass']['base_kg'];new['base_mass_kg']=engineering['mass']['base_kg']
old['minimum_preset_gap_mm']=min(v['minimum_distance_mm'] for v in before['engineering']['motion']['presets'].values())
new['minimum_preset_gap_mm']=min(v['minimum_distance_mm'] for v in engineering['motion']['presets'].values())
old['front_station_nominal_width_mm']=134;new['front_station_nominal_width_mm']=178
checker=Checker();front=[n for n in checker.parts if n.startswith(('body_front','belly_front')) or n=='nose_panel'];moving=[n for n,p in checker.parts.items() if p['leg'] and p['group']!='mount'];gaps={}
for name,pose in POSES.items():
    checker.check(pose);best=(float('inf'),None)
    for a in front:
        for b in moving:
            distance=float(fcl.distance(checker.manager._objs[a]['obj'],checker.manager._objs[b]['obj']))
            if distance<best[0]:best=(distance,[a,b])
    gaps[name]={'minimum_gap_mm':best[0],'parts':best[1]}
result={'model_sha256':sha,'baseline_model_sha256':before['model_sha256'],'limb_meshes_unchanged':not changed,'changed_limb_meshes':changed,
        'before':old,'after':new,'front_body_to_moving_parts':gaps,'wall_thickness_regions':fit['shell_regions'],
        'nose_panel_nominal_mm':fit['nose_panel_nominal_mm'],'panel_counterbore_floor_mm':fit['minimum_sampled_panel_counterbore_floor_mm'],
        'support_tabs':fit['support_tabs'],'head_cover_intersections':fit['head_cover_intersections'],'tool_access_intersections':fit['tool_access_intersections'],
        'fixed_packaging':engineering['fixed_packaging'],'battery_fit':engineering['battery_fit'],'all_print_envelopes_fit':engineering['printability']['all_fit'],
        'scope':'Actual CAD meshes and exact STEP support contacts. The nose station is a design dimension; front-plane span is smaller because of the leading-edge blend. The front-only extension preserves motor locations and every limb mesh. Wall samples do not prove a global minimum; flexible gaiters, final optics, screws, tolerance stacks and loaded performance remain unqualified.'}
interval_changes=[]
for leg,axes in before['engineering']['motion']['joint_sweeps'].items():
    for axis,row in axes.items():
        old_intervals=row['clear_intervals_deg'];new_intervals=engineering['motion']['joint_sweeps'][leg][axis]['clear_intervals_deg']
        if old_intervals!=new_intervals:interval_changes.append({'leg':leg,'axis':axis,'before':old_intervals,'after':new_intervals})
folded_changes=[]
for leg,row in before['engineering']['motion']['folded_hip_sweeps'].items():
    old_intervals=row['clear_intervals_deg'];new_intervals=engineering['motion']['folded_hip_sweeps'][leg]['clear_intervals_deg']
    if old_intervals!=new_intervals:folded_changes.append({'leg':leg,'before':old_intervals,'after':new_intervals})
result['individual_joint_clear_interval_changes']=interval_changes
result['folded_hip_clear_interval_changes']=folded_changes
result['coordinated_roll_before']=before['engineering']['motion']['coordinated_roll']
result['coordinated_roll_after']=engineering['motion']['coordinated_roll']
result['transition_intersections']=sum(v['collision_samples'] for v in engineering['motion']['transitions'].values())
(OUT/'body-revision-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'before':old,'after':new,'front_gaps':gaps},indent=2))
