> Historical generator documentation. Use [the current Tinfox workflow](../../../README.md) for review and print files. These sources remain migration references; their older browser exports are archived.

# Compact shoulder proposal

This proposal brings each hip-roll axis 5 mm inward and repackages the frame inside a 212 mm torso. It retains twelve RS-02 actuators, 170 mm links, a proximal knee actuator and one 22 mm-crank pushrod per knee. The cargo target is 1 kg beyond batteries and peripherals. It is an engineering prototype, not a qualified walking robot.

## Review and CAD files

- [Shared proposal comparison](http://127.0.0.1:8769/proposals/).
- [Interactive assembly](http://127.0.0.1:8767/review/) and [individual parts](http://127.0.0.1:8767/review/parts.html).
- [Front-detail CAD render](../design/15-body-detail.png) and [body measurements](output/body-revision-comparison.json).
- [Studio-view CAD render](../design/12-studio-view.png), [original-camera CAD render](../design/09-cad-studio.png), and [original studio reference](../design/studio-reference.png).
- [STEP assembly](output/tinfox-assembly.step), [individual STEP archive](output/tinfox-individual-cad.zip), and [oriented print prototypes](output/print-stl/).

## Geometry and visible construction

The precision-instrument exterior uses a broad shallow roof, controlled chamfered shoulder panels, a dark lower skirt and a recessed nose panel. The camera lenses sit inside annular wells. A surface-following body marking, seated cap gasket, diagonal cap engraving, restrained orange cassette release and modeled fasteners make the assembly interfaces legible. The thigh tapers into a clean circular knee termination. The shin has one shallow sweep, a continuous taper and recessed longitudinal channels. The foot combines a spherical contact surface with a tapered upper boot.

The body spans x = −236 to 243 mm while the motor stations remain fixed. A 7 mm front-only extension allows the wider rounded nose to clear the extreme shoulder sweep. The 178 mm front station joins the 212 mm center bay through local smooth transitions. The central body and shoulder cover boundaries use a 0.4 mm split. Flexible shoulder gaiters remain provisional neutral-position envelopes; the viewer hides them during large roll movements. They do not provide a rigid bridge across the hip-roll axis. Open-back protective motor sleeves use 1.5 mm walls and 0.75 mm radial motor clearance. Their short rear overhang clears the opposite shoulder through roll; the machined carrier carries the joint load.

| Dimension | Current proposal |
| --- | ---: |
| Nominal torso length / width / maximum height | 479 / 212 / 106 mm |
| Shoulder cap span | 303.6 mm |
| Neutral foot-center track | 260 mm |
| Thigh / effective shank | 170 / 170 mm |
| Estimated base mass | 12.03 kg |
| Individual STEP files | 99 |

The 212 mm torso preserves the 130 × 135 × 32 mm computer volume and two 125 × 85 × 65 mm tool-battery envelopes. Actual commercial packs, adapters, contacts, latches and electronics are unselected. The chassis rails follow the inward hip shift; the center of each rail is relieved above the battery cassette. Cooling, cabling and strain relief remain unresolved.

The body revision changes the base mass estimate from 12.021 to 12.030 kg. Every limb mesh is unchanged. The main roof has a minimum sampled normal wall thickness of 1.53 mm; front and rear cap samples are 1.53 and 1.60 mm. The display-pocket floor is intentionally 1.00 mm, and the service-panel counterbore floors are 1.05 mm. These are sampled geometry checks, not global wall or strength guarantees.

## Iterative comparison

The whole limb now uses a slimmer thigh web, a simpler knee termination and a near-straight tapered shin. One shallow 3.5 mm arc replaces the previous compound curve and lower flare. Both structural halves, the internal cavity, bolt bosses and recessed channel follow this profile. The [CAD silhouette comparison](../design/14-limb-profile.svg) shows the change, while the [measured comparison](output/limb-profile-comparison.json) records mass, inertia, section and clearance differences. Motor seats, knee bearings, transmission geometry and spherical foot contact remain fixed.

The exported groove skin has a minimum sampled transverse thickness of 3.73 mm. The minimum sampled sagittal section modulus of both shin halves is 963 mm³. These are nominal geometry screens; local stress, print anisotropy and fatigue still require qualification.

Compared with the preceding compound-curve limb, moving mass falls by 10.3 g per leg. The estimated hip-pitch inertia falls by 3.6% in the nominal standing pose; complete distal assembly inertia about knee pitch falls by 9.9%. The prescribed folded thigh-to-shin gap increases from 1.60 to 1.86 mm.

The minimum sampled thigh section modulus decreases by 19.9%, while the shin section modulus increases by 9.2%. Under the prescribed sagittal joint moments, nominal bending stress M/W is 9.42 MPa for the thigh and 14.12 MPa for the shin. This screen divides joint moment by geometric section modulus; it does not establish printed strength. Frontal loading, torsion, load transfer between halves, local stress, creep and fatigue remain unqualified.

The [iteration record](../design/iterations/visual-iteration.json) links the actual CAD renders and records observed mismatches, geometry corrections and remaining differences. The first two passes use the nominal standing pose [0°, 30°, −60°]. The final studio comparison uses [0°, 45°, −75°] for each leg, with the same camera as the other proposal and the comparison baseline. This pose is separately checked and can be selected in the browser. The original-camera render retains the nominal standing pose.

## Motion and package checks

| Pose | Intersections | Minimum checked gap |
| --- | ---: | ---: |
| stand | 0 | 1.521 mm |
| studio comparison | 0 | 1.512 mm |
| raised | 0 | 1.505 mm |
| crouch | 0 | 1.504 mm |
| reach | 0 | 1.502 mm |
| fold | 0 | 1.543 mm |
| splay | 0 | 1.518 mm |
| side reach | 0 | 1.518 mm |

The sampled transitions contain 0 intersecting samples. The fixed-package audit found 0 intersections; the battery audit found 0. Exported print bounding boxes fit the reserved H2D build volume in every case.

These checks cover sampled nominal rigid geometry. Bearing and motor-output interfaces, some fastening hardware, wires, tolerance stacks, flexible seals, load deflection and ground interaction are not qualified. Certain joint combinations can still collide. Sampled clearances do not prove continuous free motion.

## Recalculated torque screen

The calculation combines prescribed foot forces with gravity moments of the modeled moving parts. It assumes 90% knee-transmission efficiency. Joint acceleration, torque-speed behavior, thermal response and a dynamically balanced gait are not simulated.

| Load case | Cargo | Hip roll | Hip pitch | Knee motor |
| --- | ---: | ---: | ---: | ---: |
| four foot stand | 1 kg | 1.78 N·m | 0.06 N·m | 2.69 N·m |
| two foot stand | 1 kg | 3.92 N·m | 0.32 N·m | 5.42 N·m |
| three foot crouch | 1 kg | 2.49 N·m | 0.27 N·m | 6.53 N·m |
| stair reach 60 percent | 1 kg | 6.59 N·m | 13.74 N·m | 12.86 N·m |
| reach with braking | 1 kg | 6.59 N·m | 9.97 N·m | 12.24 N·m |
| splayed two foot | 1 kg | 13.45 N·m | 0.28 N·m | 5.11 N·m |
| unloaded 2p5g pulse | 0 kg | 9.52 N·m | 0.99 N·m | 12.57 N·m |
| unloaded 3g landing screen | 0 kg | 11.50 N·m | 1.22 N·m | 15.10 N·m |

Some support cases exceed the 6 N·m rated reference. Loaded stairs, self-righting, running and jumping remain unproven. The estimated mass includes 1.4 kg of battery allowances, 0.8 kg of electronics and wiring, and 0.4 kg of unmodeled hardware. It is not a weighed bill of materials.

## Manufacturing and assembly status

The integrated inner thigh cradles the knee motor. Metal stator plates and compression sleeves distribute mounting loads. The removable outer thigh uses a narrower web and a continuous circular knee termination around the retained axle seat. Both structural halves are required. The 0.4 mm cap gasket and surface markings are finish components. The 1.6 mm nose panel is a cosmetic prototype. Four metal tabs connect it to the continuous body rim; exact-solid checks verify contact without overlap. Counterbores and straight tool access clear the provisional head envelopes. Final screw selection, retention and impact resistance need validation.

Every custom mount has an individual STEP solid, including handed front/rear roll cartridges and motor carriers. The parts viewer lists function, interface geometry, quantity and handedness. STEP imports into Fusion 360 as solids without a native feature timeline. Select bearing fits, motor datums, screw lengths, retention and materials before producing loaded parts. The printed parts need coupon, creep, fatigue and assembled load tests.

## Reproduce from the repository root

```bash
/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/build.py
/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/orient_body_parts.py
/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/export_parts.py
/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/audit_mounting.py
/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/audit_body.py
/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/engineering.py
/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/test_model.py
/home/sunil/git/oddstride/tinfox/model/.cache/render-venv/bin/python tinfox/proposals/compact/model/render_studio.py
/home/sunil/git/oddstride/tinfox/model/.cache/render-venv/bin/python tinfox/proposals/compact/model/render_reference.py
/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/compare_limb.py
/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/compare_body.py
/home/sunil/git/oddstride/tinfox/model/.cache/render-venv/bin/python tinfox/proposals/compact/model/render_body_detail.py
/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/write_report.py
/home/sunil/git/oddstride/tinfox/.venv/bin/python tinfox/proposals/compact/model/serve.py
```

CAD fingerprint: `26dc3e75cbdbc009a4c43802ad7746045052365b9068d46fa1c1d88d5b37584a`.
