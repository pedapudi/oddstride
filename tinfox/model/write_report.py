"""Generate the review and inventory from the current CAD and analysis."""
import csv,json
from collections import Counter
from kinematics import ROOT,P,POSES,contacts
r=json.loads((ROOT/'output/engineering.json').read_text())
m=json.loads((ROOT/'output/model.json').read_text())
assert r['model_sha256']==json.loads((ROOT/'output/manifest.json').read_text())['model_sha256']
mass=r['mass']['base_kg'];motion=r['motion'];s=r['structure']
with (ROOT/'output/parts.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['part','quantity','material','each_mass_kg','status'])
 for name,count in sorted(Counter(p['mesh'] for p in m['parts']).items()):
  p=next(p for p in m['parts'] if p['mesh']==name)
  w.writerow([name,count,p['material'],p['mass_kg'],p['note'] or 'Geometry prototype; manufacturing qualification outstanding.'])
def fmt(v):return '; '.join(f'{a}° to {b}°' for a,b in v) or 'None'
lines=['# Tinfox 170: flange-driven hip and structural leg','',
'Tinfox uses twelve RS-02 actuators and one rigid pushrod per knee. Its cargo target is 1 kg beyond batteries, computer and sensors. The exported assembly is a design prototype. Loaded stairs, self-righting and running remain unproven.','',
'## The studio image uses the CAD geometry','',
'- [Individual CAD parts](http://127.0.0.1:8765/review/parts.html) and [all STEP parts in one archive](output/tinfox-individual-cad.zip).',
'- [Before-and-after exterior review](http://127.0.0.1:8765/review/body.html) and [measured changes](output/torso-comparison.json).',
'- [CAD studio render](../design/09-cad-studio.png) and [render provenance](output/studio-provenance.json).',
'- [Interactive assembly](http://127.0.0.1:8765/review/): orbit, open a leg, move the independent roll axis and inspect interference.',
'- [Named STEP assembly](output/tinfox-assembly.step), [GLB](output/tinfox.glb), [individual STEP parts](output/step-parts/) and [oriented print prototypes](output/print-stl/).',
'- [Part inventory](output/parts.csv), [torque cases](output/torques.csv) and [engineering results](output/engineering.json).','',
'The studio image is a Blender Cycles render of the exported CAD meshes. Lighting, camera and floor are presentation elements. The image retains the modeled flexible seals, whose deformation is unvalidated. The earlier generated studio image remains a styling reference.','',
'The precision-instrument exterior has an ivory torso and thighs, dark articulated shoulders and curved shins, recessed cap markings and restrained orange controls. The battery packs sit side by side within a shallow underside cassette. STEP preserves separate solids for Fusion 360, but does not transfer a native feature timeline.','',
'The torso is 464 mm long, with a central crown 47.5 mm above the hip axes. Continuous rounded flanks replace the local side patches, and the 263 mm center panel moves its seams toward the shoulders. A narrower rigid sensor face clears the hip actuators. The 1.6 mm body skin has two internal roof ribs; body-cover stiffness and payload-mount details remain unqualified. The thigh outlines narrow through the web, and their outer surfaces curve inward by up to 2.5 mm while retaining material around the joint seats. Flush metal shoulder caps sit in recessed seats. The shins bow gently between their bearing and foot centers, with larger corner radii at the foot end. These surfaces are in the STEP geometry. The status window follows the roof curvature, and the battery skid has rounded plan corners. The front apertures are visualization envelopes; selected camera modules and cable bends must be checked inside the shortened nose.','',
'## Individual parts are available as CAD solids','',
'Custom structural parts and modeled transmission components have separate STEP files. The browser parts catalog identifies its role, mating interfaces, material, installed quantity and handedness. It includes the fixed roll cartridge, roll-to-hip motor carrier, hip-output hub, knee-stator plate and knee-output adapter. Unique rear mounts have separate exports. Motor envelopes and provisional flexible seals are excluded from the individual manufacturing set.','',
'Click a component in the assembly to open its isolated view or download its STEP. The [CAD-only archive](output/tinfox-individual-cad.zip) includes the catalog and all individual solids. Coordinates remain local to the assembly; the viewer centers each part only for inspection. STEP imports into Fusion 360 without a native feature timeline. Nominal holes do not specify threads or tolerance fits.','',
'## The roll actuator drives a bearing-supported motor carrier','',
'Each body-fixed roll actuator points fore/aft. Its output bolts directly into a machined elbow carrier that includes a 50 mm bearing journal. A perpendicular flange on that carrier locates the hip-pitch stator. A separate hinge pin or clevis is not used.','',
'The crossed-roller bearing envelope is 50 × 66 × 8 mm. Its fixed outer housing transfers leg loads into the chassis; its inner ring supports the rotating carrier. The hip output hub carries a coaxial knee actuator inside the structural thigh root. Three metal ties and compression sleeves connect the hip output flange to the knee stator plate. The printed cradle and inner thigh are one continuous part.','',
'The motor interfaces use nine M3 stator positions on a 73 mm pitch circle and six M4 output positions on a 24 mm pitch circle. The roll coupling has through-access holes for its six output screws. The hip-output screw heads are recessed into the coupling flange. Low-head knee-output screws sit below the input-crank face to clear the rod. Delivered motor datums, screw length and engagement, bearing preload and retention still need manufacturing verification.','',
'The fore/aft offset keeps perpendicular motor bodies apart. The hip motor cups move with hip roll; the integrated knee-motor cradle and thigh move with hip pitch. Flexible neutral-position gaiters close the remaining exterior gaps; the viewer hides them during larger roll movements. They are provisional covers, not structural shoulders.','',
'## The recessed motor and rear pushrod make the leg narrower','',
f"The thigh pivot spacing is {P['thigh']} mm. Two {P['crank_radius']} mm cranks and a {P['rod_length']} mm steel rod form a 1:1 parallelogram. The crank phase is {P['crank_phase_deg']}°. The knee motor stays at the thigh root, although its mass still contributes to hip-pitch inertia.",'',
'The knee actuator is recessed 12 mm into the thigh root. A 4 mm shorter output coupling brings the complete limb 16 mm inward per side. Neutral foot-center track is 270 mm, down from 302 mm. Width across the recessed shoulder caps is 313.6 mm; the surrounding shoulder shells span about 314 mm. The earlier raised caps spanned 322 mm. The structural inner cheek wraps around the actuator; the outer cheek is removable for access.', '',
'The shin sits between the thigh cheeks. A fixed 12 × 8 mm tubular shaft ties those cheeks together. Two 6001-size bearings in metal shin carriers rotate around the shaft. The output crank bolts to the inner shin carrier. A central spacer separates the bearing inner races.','',
'The thigh has 3 mm outer skins, ribs and two upper through-bolt compression sleeves. The fixed knee axle connects the lower cheeks; cross-bolts are omitted from the shin folding path. Its lower fork opens around the folded shin path. The shin has two curved structural cheeks, an open upper channel for the pushrod, and a closed lower section. Both halves are required for operation.','',
'The output rocker extends above the knee in the shin frame, placing the rod behind the flexion opening. Both cranks use a −78° phase. Their 22 mm radius reduces worst-case rod force at 17 N·m to about 1.31 kN, compared with 1.61 kN for the earlier 18 mm cranks. The minimum moment arm is 12.93 mm across −156° to −48°, with a 36° margin to dead center. The equal crank radii preserve the 1:1 torque ratio.', '',
'The pushrod has a 6 mm square central section and pinned eyes. Final shoulder pins, washers and retention are not fully detailed. Equal cranks do not increase motor torque. The force rises as the crank approaches alignment with the rod.','',
'| Dimension | Value |','| --- | ---: |',
f"| Nominal torso station dimensions | {P['body_length']} × {P['body_width']} × {P['body_height']} mm |",
f"| Neutral width across shoulder caps | {2*(P['roll_y']+P['cap_y'])} mm |",
f"| Structural thigh depth at joint seats / central web | {P['thigh_depth']} / 41.5 mm |",
f"| Thigh / shank to foot center | {P['thigh']} / {P['shank_to_foot_center']} mm |",
f"| Lowest skid below hip | {P['skid_below_hip_mm']} mm |",
f"| Estimated base mass | {mass:.2f} kg |",'',
'The [interactive knee study](review/linkage.html) compares both routings. The [mounting audit](output/mounting-audit.json) checks the rod against modeled fasteners and measures shin sections. The [exact-solid fit report](output/mounting-fit.json) checks the actuator and mounting plate inside the structural cradle.', '',
'## Motion is checked at sampled poses','',
'The target limits follow the [official Go2 URDF](https://github.com/unitreerobotics/unitree_ros/blob/master/robots/go2_description/urdf/go2_description.urdf): roll ±60°, front pitch −90° to 200°, rear pitch −30° to 260°, knee −156° to −48°. Joint limits alone do not establish equivalent mobility.','',
'| Leg | Roll with other joints neutral | Hip with knee −130° | Knee with other joints neutral |','| --- | --- | --- | --- |']
for leg,d in motion['joint_sweeps'].items():lines.append(f"| {leg} | {fmt(d['roll']['clear_intervals_deg'])} | {fmt(motion['folded_hip_sweeps'][leg]['clear_intervals_deg'])} | {fmt(d['knee']['clear_intervals_deg'])} |")
lines+=['','| Preset | Intersections | Minimum checked separation |','| --- | --- | ---: |']
for name,v in motion['presets'].items():lines.append(f"| {name.replace('_',' ')} | {'Present' if v['collision'] else 'None'} | {v['minimum_distance_mm']:.2f} mm |")
count=sum(v['samples'] for d in motion['joint_sweeps'].values() for v in d.values())+sum(v['samples'] for v in motion['transitions'].values())+motion['coordinated_roll']['samples']+sum(v['samples'] for v in motion['folded_hip_sweeps'].values())
fail=sum(v['collision_samples'] for v in motion['transitions'].values())
lines += ['',f"The motion report includes {count:,} sweep and transition samples, plus preset distance checks. Neutral-to-preset transitions contain {fail} intersecting samples.",'',
f"Coordinated roll clears {fmt(motion['coordinated_roll']['clear_intervals_deg'])}, using front hip −35°, rear hip 35° and knee −70°. This is a free-space check, not a self-righting demonstration.",'',
'Checks omit intended bearing and motor-output interfaces, rigidly attached pairs and small hardware. Wires, tolerances, hard stops, ground contact, flexible seals and load deflection are not modeled. Some simultaneous joint combinations collide. Sampled checks do not prove continuous trajectory clearance.','',
'## The battery cassette improves belly clearance','',
'Two assumed 125 × 85 × 65 mm packs sit side by side under the electronics shelf. Each compact 5 Ah pack and adapter is allocated 0.70 kg. Exact commercial packs, contacts, latches and electrical protection remain unselected.','',
f"The battery audit found {len(r['battery_fit']['intersections'])} intersections against checked rigid parts, including fixed chassis parts. The skid is 48 mm higher than the preceding 119 mm-deep arrangement.",'',
'| Pose | Ground to skid |','| --- | ---: |']
for name in ['stand','raised','crouch']:
 foot,*_=contacts('FL',POSES[name]['FL']);c=-foot[2]-P['skid_below_hip_mm'];lines.append(f'| {name} | {c:.0f} mm / {c/25.4:.1f} in |')
lines+=['','The 12-inch belly-clearance target remains unmet. Maximum stair height also depends on foot placement, body pitch and stair-nosing contact. It cannot be inferred from link length alone.','',
'## Weight reduction toward 10 kg','',
f"The preceding cartridge assembly was {r['weight_comparison']['baseline_base_kg']:.2f} kg. The current estimate is {mass:.2f} kg, a reduction of {r['weight_comparison']['total_reduction_kg']:.2f} kg. It remains {mass-10:.2f} kg above the 10 kg target before cargo.",'',
f"Geometry and catalogued component changes save {r['weight_comparison']['geometry_and_component_reduction_kg']:.2f} kg. Smaller battery allowances save 0.80 kg, and the compact electronics allocation saves 0.60 kg. These allocations require a weighed bill of materials.",'',
'The structural changes include integrated motor cradles, pocketed output hubs, notched chassis rails, a thin skid, hollow curved shins and tubular knee shafts. The roll bearing changes from 270 g to 80 g per leg. Printed masses use actual CAD solid volumes at PETG density; no arbitrary infill discount is applied.','',
'Both 5 Ah packs are assumed to be installed. Larger 8–12 Ah packs and a heavier onboard computer increase mass. A 36 V nominal series pair also requires actuator speed and power verification at that supply voltage.','',
'## Torque is recalculated from the revised assembly','',
f"The estimated base mass is {mass:.2f} kg. This includes 1.4 kg of assumed compact packs, 0.8 kg for computer, sensors and wiring, and 0.4 kg for unmodeled hardware. The cargo case adds 1 kg.",'',
'The calculation combines prescribed foot-force moments with gravity moments of the modeled moving parts. Knee efficiency is assumed to be 90%. Joint accelerations, torque-speed limits, thermal response and dynamically balanced gaits are not simulated.','',
'The stair case places 60% of weight on one foot. Braking adds a backward force equal to 25% of that vertical force. The splayed case adds an outward force equal to 20% of vertical load. Pulse cases place half of 2.5 or 3 times robot weight on each stance foot.','',
'| Case | Cargo | Roll | Hip pitch | Knee motor |','| --- | ---: | ---: | ---: | ---: |']
for row in r['torque_cases']:
 if row['payload_kg']==1 or 'unloaded' in row['case']:
  a,b,c=row['motor_Nm'];lines.append(f"| {row['case'].replace('2p5g','2.5g').replace('_',' ')} | {row['payload_kg']} kg | {a:.2f} N·m | {b:.2f} N·m | {c:.2f} N·m |")
lines+=['',
'The reference is 6 N·m rated and 17 N·m peak from the [RS-02 manual](https://github.com/RobStride/Product_Information/blob/main/Product%20Literature/CAN2.0/RS02/RS02User%20Manual260713.pdf). Its rated test uses a 260 × 280 mm heat sink. That value is not a demonstrated holding limit for an enclosed printed pod.','',
'The all-RS-02 design remains torque-constrained. Some support cases exceed the rated reference. The revised pulse cases are below the peak reference, with limited reserve for unmodeled acceleration and impacts. Loaded stairs, running and jumping require a lower finished mass, constrained contact loads and measured actuator performance before acceptance.','',
'## Structural and manufacturing checks remain preliminary','',
f"The shin screen uses the smallest sagittal section modulus measured from 0.2 mm CAD slices at 5 mm intervals. Applying the maximum case joint moment uniformly gives a bending stress of {s['gross_bending_stress_MPa']:.1f} MPa; a factor of two requires {s['coupon_strength_needed_for_factor_2_MPa']:.1f} MPa coupon strength before local effects.",'',
'This sampled bending screen does not establish torsional strength or capture every local section minimum. Printed layer bonding, creep, fatigue, holes, bearing seats, fastener slip and impacts require separate tests. A required coupon result is not an assigned PETG allowable.','',
f"At 17 N·m and the worst linkage angle, rod force is {s['rod_force_at_17Nm_and_worst_transmission_angle_N']:.0f} N. Ideal pinned buckling capacity for a 6 mm round steel core is {s['rod_ideal_pinned_euler_N']:.0f} N. Joint clearance and imperfections reduce this idealized result.",'',
f"A 6 mm pin with a 4 mm single-shear overhang has {s['pin_6mm_nominal_vm_MPa']:.0f} MPa nominal equivalent stress. The 12 × 8 mm tubular axle screen gives {s['shaft_12x8mm_conservative_bending_MPa']:.0f} MPa bending stress under a central rod-force assumption over 36 mm.",'',
'The roll cartridge and motor carrier are machining candidates. Printed versions are fit-check prototypes only. Bearing shoulders, retainers, fits, fastener grades, hard stops, cable exits, cooling paths and chassis connections need detailed manufacturing drawings. The specialty roll bearing also leaves the sub-$100 replacement-leg target unverified.','',
('All printed-part bounding boxes fit the H2D envelope with the modeled margin.' if r['printability']['all_fit'] else 'Some printed-part bounding boxes exceed the H2D envelope.')+' The supplied STL orientations require slicer review and load qualification. The integrated motor cradle needs supports beneath its offset limb surfaces; keep the long limb axis in the bed plane and verify support removal before printing a full set.','',
'Assembly order:','',
'1. Attach the fixed roll cartridge and actuator to the chassis.',
'2. Install the bearing and elbow carrier, then attach the hip-pitch stator.',
'3. Bolt the hip output flange onto the actuator before enclosing it; then fit the integrated thigh cradle, knee actuator, stator plate and axial ties.',
'4. With the outer cheek removed, attach the motor output adapter and crank; assemble the fixed shaft, shin bearings and carriers.',
'5. Connect both cranks and the single pushrod; check passive travel.',
'6. Close the structural halves, fit the foot and add the battery cassette.','',
'## Research informs the arrangement','',
'- [PADWQ leg design, section 2.2](https://www.mdpi.com/2076-3417/11/9/3762): proximal coaxial motors and a parallelogram transmission. Longer cranks reduce force in printed parts. The rearward routing and dimensions used here come from Tinfox geometry checks.',
'- [Benjamin Katz, MIT thesis, chapter 3](https://dspace.mit.edu/bitstream/handle/1721.1/118671/1057343368-MIT.pdf): short abduction-to-hip carrier and coaxial proximal actuators. Tinfox retains the requested rigid pushrod instead of that design’s belt transmission.',
'- [MIT Cheetah actuation paper](https://fab.cba.mit.edu/classes/865.18/motion/papers/mit-cheetah-actuator.pdf): proximal actuator concentration and transmission design. This supports the layout principle, not Tinfox performance claims.',
'- [THK crossed-roller catalog](https://www.ws-thk.com/wp-content/uploads/Cross-Roller-Ring.pdf): RA5008 envelope 50 × 66 × 8 mm and 0.08 kg. Fits, preload and moment capacity must be selected for this application.',
'- [NSK 6001 bearing](https://www.nsk.com/engineering/products/bearings/ball-bearings/deep-groove-ball-bearings/single-row-deep-groove-ball-bearings/6001-apn.html): 12 × 28 × 8 mm knee bearing envelope.',
'- [RobStride manufacturer information](https://github.com/RobStride/Product_Information): motor manual and CAD reference. Motor internals and connectors are simplified in this assembly.','',
'## Reproduce the artifacts','',
'```bash','tinfox/.venv/bin/python tinfox/model/build.py','tinfox/.venv/bin/python tinfox/model/export_parts.py','tinfox/.venv/bin/python tinfox/model/audit_mounting.py','tinfox/.venv/bin/python tinfox/model/engineering.py','tinfox/.venv/bin/python tinfox/model/test_model.py','tinfox/.venv/bin/python tinfox/model/write_report.py','tinfox/.venv/bin/python tinfox/model/compare_torso.py','tinfox/.venv/bin/python tinfox/model/serve.py','```','',
'Install model dependencies from `requirements.txt` in a Python 3.12 environment. Render the studio with `render_studio.py` in a separate Python 3.11 environment containing `bpy==5.0.1` and NumPy.','',
f"CAD fingerprint: `{r['model_sha256']}`.",'']
budget=['| Mass category | Estimate |','| --- | ---: |']
labels={'motors':'Twelve RS-02 actuators','petg':'Printed PETG solids','aluminum':'Aluminum parts','steel':'Steel parts and bearings','rubber':'Feet','fabric':'Provisional protective seals','batteries':'Two compact packs and adapters','compute_sensors_wiring_allowance':'Computer, sensors, wiring and converters','unmodeled_mounts_cables_fasteners_allowance':'Unmodeled hardware allowance'}
for key,value in r['mass']['categories_kg'].items():
 if value>0:budget.append(f"| {labels.get(key,key)} | {value:.2f} kg |")
budget.extend([f'| Base total | {mass:.2f} kg |',f'| With 1 kg cargo | {mass+1:.2f} kg |',''])
insert=lines.index('## Torque is recalculated from the revised assembly');lines[insert:insert]=budget
(ROOT/'README.md').write_text('\n'.join(lines))
print('Wrote review and inventory.')
