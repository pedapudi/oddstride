"""Write a self-contained review of the compact shoulder proposal."""
import json,hashlib
from kinematics import ROOT,P
audit=json.loads((ROOT/'output/mounting-audit.json').read_text())
body=json.loads((ROOT/'output/body-revision-comparison.json').read_text())
comparison=json.loads((ROOT/'output/limb-profile-comparison.json').read_text());delta=comparison['comparison_summary'];bend=comparison['nominal_sagittal_bending_screen']
r=json.loads((ROOT/'output/engineering.json').read_text());m=json.loads((ROOT/'output/model.json').read_text());c=json.loads((ROOT/'output/parts-catalog.json').read_text())
assert r['model_sha256']==c['model_sha256']==hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest()
lines=['# Compact shoulder proposal','',
'This proposal brings each hip-roll axis5 mm inward and repackages the frame inside a212 mm torso. It retains twelve RS-02 actuators,170 mm links, a proximal knee actuator and one22 mm-crank pushrod per knee. The cargo target is1 kg beyond batteries and peripherals. It is an engineering prototype, not a qualified walking robot.','',
'## Review and CAD files','',
'- [Shared proposal comparison](http://127.0.0.1:8769/proposals/).',
'- [Interactive assembly](http://127.0.0.1:8767/review/) and [individual parts](http://127.0.0.1:8767/review/parts.html).',
'- [Front-detail CAD render](../design/15-body-detail.png) and [body measurements](output/body-revision-comparison.json).',
'- [Studio-view CAD render](../design/12-studio-view.png), [original-camera CAD render](../design/09-cad-studio.png), and [original studio reference](../design/studio-reference.png).',
'- [STEP assembly](output/tinfox-assembly.step), [individual STEP archive](output/tinfox-individual-cad.zip), and [oriented print prototypes](output/print-stl/).','',
'## Geometry and visible construction','',
'The precision-instrument exterior uses a broad shallow roof, controlled chamfered shoulder panels, a dark lower skirt and a recessed nose panel. The camera lenses sit inside annular wells. A surface-following body marking, seated cap gasket, diagonal cap engraving, restrained orange cassette release and modeled fasteners make the assembly interfaces legible. The thigh tapers into a clean circular knee termination. The shin has one shallow sweep, a continuous taper and recessed longitudinal channels. The foot combines a spherical contact surface with a tapered upper boot.','',
'The body spans x = −236 to 243 mm while the motor stations remain fixed. A 7 mm front-only extension allows the wider rounded nose to clear the extreme shoulder sweep. The 178 mm front station joins the 212 mm center bay through local smooth transitions. The central body and shoulder cover boundaries use a 0.4 mm split. Flexible shoulder gaiters remain provisional neutral-position envelopes; the viewer hides them during large roll movements. They do not provide a rigid bridge across the hip-roll axis. Open-back protective motor sleeves use 1.5 mm walls and 0.75 mm radial motor clearance. Their short rear overhang clears the opposite shoulder through roll; the machined carrier carries the joint load.','',
f'| Dimension | Current proposal |\n| --- | ---: |\n| Nominal torso length / width / maximum height | {P["body_length"]} / {P["body_width"]} / {P["body_height"]} mm |\n| Shoulder cap span | {2*(P["roll_y"]+P["cap_y"]):.1f} mm |\n| Neutral foot-center track | {2*(P["roll_y"]+P["shin_y"]):.0f} mm |\n| Thigh / effective shank | 170 / 170 mm |\n| Estimated base mass | {r["mass"]["base_kg"]:.2f} kg |\n| Individual STEP files | {len(c["parts"])} |','',
'The212 mm torso preserves the130 × 135 × 32 mm computer volume and two125 × 85 × 65 mm tool-battery envelopes. Actual commercial packs, adapters, contacts, latches and electronics are unselected. The chassis rails follow the inward hip shift; the center of each rail is relieved above the battery cassette. Cooling, cabling and strain relief remain unresolved.','',
f'The body revision changes the base mass estimate from {body["before"]["base_mass_kg"]:.3f} to {body["after"]["base_mass_kg"]:.3f} kg. Every limb mesh is unchanged. The main roof has a minimum sampled normal wall thickness of {body["wall_thickness_regions"]["roof"]["minimum_normal_ray_thickness_mm"]:.2f} mm; front and rear cap samples are {body["wall_thickness_regions"]["front_rim"]["minimum_normal_ray_thickness_mm"]:.2f} and {body["wall_thickness_regions"]["rear_cap"]["minimum_normal_ray_thickness_mm"]:.2f} mm. The display-pocket floor is intentionally 1.00 mm, and the service-panel counterbore floors are 1.05 mm. These are sampled geometry checks, not global wall or strength guarantees.','',
'## Iterative comparison','',
'The whole limb now uses a slimmer thigh web, a simpler knee termination and a near-straight tapered shin. One shallow 3.5 mm arc replaces the previous compound curve and lower flare. Both structural halves, the internal cavity, bolt bosses and recessed channel follow this profile. The [CAD silhouette comparison](../design/14-limb-profile.svg) shows the change, while the [measured comparison](output/limb-profile-comparison.json) records mass, inertia, section and clearance differences. Motor seats, knee bearings, transmission geometry and spherical foot contact remain fixed.','',
f'The exported groove skin has a minimum sampled transverse thickness of {audit["shin_skin_audit"]["minimum_sampled_skin_mm"]:.2f} mm. The minimum sampled sagittal section modulus of both shin halves is {audit["minimum_shin_section_modulus_y_mm3"]:.0f} mm³. These are nominal geometry screens; local stress, print anisotropy and fatigue still require qualification.','',
f'Compared with the preceding compound-curve limb, moving mass falls by {abs(delta["moving_leg_mass_delta_g"]):.1f} g per leg. The estimated hip-pitch inertia falls by {abs(delta["hip_pitch_inertia_change_percent"]):.1f}% in the nominal standing pose; complete distal assembly inertia about knee pitch falls by {abs(delta["knee_pitch_inertia_change_percent"]):.1f}%. The prescribed folded thigh-to-shin gap increases from {delta["fold_min_thigh_shin_gap_mm_before"]:.2f} to {delta["fold_min_thigh_shin_gap_mm_after"]:.2f} mm.','',
f'The minimum sampled thigh section modulus decreases by {abs(delta["thigh_section_modulus_change_percent"]):.1f}%, while the shin section modulus increases by {delta["shin_section_modulus_change_percent"]:.1f}%. Under the prescribed sagittal joint moments, nominal bending stress M/W is {bend["thigh"]["nominal_M_over_W_MPa"]:.2f} MPa for the thigh and {bend["shin"]["nominal_M_over_W_MPa"]:.2f} MPa for the shin. This screen divides joint moment by geometric section modulus; it does not establish printed strength. Frontal loading, torsion, load transfer between halves, local stress, creep and fatigue remain unqualified.','',
'The [iteration record](../design/iterations/visual-iteration.json) links the actual CAD renders and records observed mismatches, geometry corrections and remaining differences. The first two passes use the nominal standing pose [0°, 30°, −60°]. The final studio comparison uses [0°, 45°, −75°] for each leg, with the same camera as the other proposal and the comparison baseline. This pose is separately checked and can be selected in the browser. The original-camera render retains the nominal standing pose.','',
'## Motion and package checks','',
'| Pose | Intersections | Minimum checked gap |','| --- | ---: | ---: |']
for k,v in r['motion']['presets'].items():lines.append(f'| {k.replace("_"," ")} | {len(v["pairs"])} | {v["minimum_distance_mm"]:.3f} mm |')
lines+=['',f'The sampled transitions contain {sum(v["collision_samples"] for v in r["motion"]["transitions"].values())} intersecting samples. The fixed-package audit found {len(r["fixed_packaging"]["intersections"])} intersections; the battery audit found {len(r["battery_fit"]["intersections"])}. Exported print bounding boxes fit the reserved H2D build volume in every case.','',
'These checks cover sampled nominal rigid geometry. Bearing and motor-output interfaces, some fastening hardware, wires, tolerance stacks, flexible seals, load deflection and ground interaction are not qualified. Certain joint combinations can still collide. Sampled clearances do not prove continuous free motion.','',
'## Recalculated torque screen','',
'The calculation combines prescribed foot forces with gravity moments of the modeled moving parts. It assumes90% knee-transmission efficiency. Joint acceleration, torque-speed behavior, thermal response and a dynamically balanced gait are not simulated.','',
'| Load case | Cargo | Hip roll | Hip pitch | Knee motor |','| --- | ---: | ---: | ---: | ---: |']
for v in r['torque_cases']:
 if v['payload_kg']==1 or 'unloaded' in v['case']:lines.append('| '+v['case'].replace('_',' ')+' | '+str(v['payload_kg'])+' kg | '+' | '.join(f'{x:.2f} N·m' for x in v['motor_Nm'])+' |')
lines+=['','Some support cases exceed the6 N·m rated reference. Loaded stairs, self-righting, running and jumping remain unproven. The estimated mass includes1.4 kg of battery allowances,0.8 kg of electronics and wiring, and0.4 kg of unmodeled hardware. It is not a weighed bill of materials.','',
'## Manufacturing and assembly status','',
'The integrated inner thigh cradles the knee motor. Metal stator plates and compression sleeves distribute mounting loads. The removable outer thigh uses a narrower web and a continuous circular knee termination around the retained axle seat. Both structural halves are required. The 0.4 mm cap gasket and surface markings are finish components. The 1.6 mm nose panel is a cosmetic prototype. Four metal tabs connect it to the continuous body rim; exact-solid checks verify contact without overlap. Counterbores and straight tool access clear the provisional head envelopes. Final screw selection, retention and impact resistance need validation.','',
'Every custom mount has an individual STEP solid, including handed front/rear roll cartridges and motor carriers. The parts viewer lists function, interface geometry, quantity and handedness. STEP imports into Fusion360 as solids without a native feature timeline. Select bearing fits, motor datums, screw lengths, retention and materials before producing loaded parts. The printed parts need coupon, creep, fatigue and assembled load tests.','',
'## Reproduce from the repository root','',
'```bash',
'/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/build.py',
'/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/orient_body_parts.py',
'/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/export_parts.py',
'/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/audit_mounting.py',
'/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/audit_body.py',
'/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/engineering.py',
'/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/test_model.py',
'/home/sunil/git/oddstride/tinfox/model/.cache/render-venv/bin/python tinfox/proposals/compact/model/render_studio.py',
'/home/sunil/git/oddstride/tinfox/model/.cache/render-venv/bin/python tinfox/proposals/compact/model/render_reference.py',
'/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/compare_limb.py',
'/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/compare_body.py',
'/home/sunil/git/oddstride/tinfox/model/.cache/render-venv/bin/python tinfox/proposals/compact/model/render_body_detail.py',
'/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/write_report.py',
'/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/serve.py',
'```','',f'CAD fingerprint: `{r["model_sha256"]}`.','']
import re
for i,line in enumerate(lines):
    if line.startswith(('/home','- [','CAD fingerprint','|')):continue
    line=re.sub(r'(?<=[A-Za-z])(?=\d)', ' ',line)
    line=re.sub(r'(?<=\d)(?=[A-Za-z])',' ',line)
    line=re.sub(r',(?=\d)',', ',line).replace('H 2 D','H2D').replace('pose[','pose [')
    lines[i]=line
(ROOT/'README.md').write_text('\n'.join(lines))
print('Wrote compact proposal review.')
