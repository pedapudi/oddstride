> Historical generator documentation. Use [the current Tinfox workflow](../../../README.md) for review and print files. These sources remain migration references; their older browser exports are archived.

# Tinfox proposal B: sculpted panels and articulated shoulder collars

Tinfox uses twelve RS-02 actuators and one rigid pushrod per knee. Its cargo target is 1 kg beyond batteries, computer and sensors. The exported assembly is a design prototype. Loaded stairs, self-righting and running remain unproven.

## The review images render the CAD geometry

- [Individual CAD parts](http://127.0.0.1:8768/review/parts.html) and [all STEP parts in one archive](output/tinfox-individual-cad.zip).
- [Parallel proposal comparison](http://127.0.0.1:8769/proposals/).
- [Matched studio view](../design/12-studio-view.png), [neutral CAD render](../design/09-cad-studio.png) and [render provenance](output/studio-view-provenance.json).
- [Interactive assembly](http://127.0.0.1:8768/review/): orbit, open a leg, move the independent roll axis and inspect interference.
- [Named STEP assembly](output/tinfox-assembly.step), [GLB](output/tinfox.glb), [individual STEP parts](output/step-parts/) and [oriented print prototypes](output/print-stl/).
- [Assembly stages](review/assembly.html), [access report](output/assembly-audit.json) and [installation sequence](output/assembly-guide.txt).

- [Print plates and manufacturing guide](review/manufacturing.html), [fabrication kit](output/tinfox-manufacturing-kit.zip) and [STEP round-trip checks](output/step-roundtrip.json).
- [Flat electronics deck](http://127.0.0.1:8768/review/parts.html#electronics_shelf), [deck DXF](output/flat-patterns/electronics_shelf.dxf) and [deck/service checks](output/electronics-deck-audit.json).

- [Part inventory](output/parts.csv), [torque cases](output/torques.csv) and [engineering results](output/engineering.json).

The matched review image is a Blender Cycles render of the exported CAD meshes. Lighting, camera and floor are presentation elements. The image retains the modeled flexible seals, whose deformation is unvalidated. The earlier generated studio image remains a styling reference.

The precision-instrument exterior has ivory service panels and structural thighs, dark annular shoulder collars, curved shin channels with rounded ends, diagonal cap engravings and restrained orange controls. The battery packs sit side by side within an underside cassette and shaped removable service panels. STEP preserves separate solids for Fusion 360, but does not transfer a native feature timeline.

The main torso is 464 mm long. The convex face extends the overall rigid body length to approximately 494 mm. The central roof is 49.5 mm above the hip axes; local shoulder crowns rise to 55.5 mm. The planar center bay transitions through controlled curved shoulders into a rounded front wrap. The center roof and both side walls form one removable clamshell. The roof and side panels are 250.8 mm long; front and rear service seams sit close to the shoulder stations. The removable front face has independent 8 mm horizontal and 10 mm vertical crowns, with nominal 18 mm rounded front corners, a 0.6 mm perimeter seam and a recessed black sensor bezel. A ribbed return attaches the wrap to the independent metal frame through two screw positions; four posts support the removable face. Final screws, inserts and load qualification remain unselected. The 168 mm wide sensor opening is forward of the shoulder sweep. The 2.8 mm nominal body shell has internal ribs; body-cover stiffness and payload-mount details remain unqualified. The thigh outlines narrow through the web, and their outer surfaces curve inward by up to 1.5 mm while retaining material around the joint seats. The outer thigh includes the motor face and knee surround. The slimmer thigh web leads into a simple circular knee. The shin follows a single shallow parabolic bow, with a maximum 3.5 mm offset from the knee-to-foot chord. Its sagittal width tapers continuously from 34 to 22 mm. The paired shin halves enclose a ribbed cavity along the same arc. Both structural shin halves end 136 mm below the knee, leaving a distinct boot neck. These surfaces are in the STEP geometry. The status window follows the roof curvature, and the battery skid has rounded plan corners. Layered sensor barrels, aperture rings and curved recessed glass are provisional envelopes. Selected camera modules, glazing, seals and cable bends must be checked inside the nose. Battery access panels have rounded perimeter corners and edge blends.

## The revised front shares the body envelope

The [front detail](../design/15-body-detail.png) renders the actual rounded wrap, recessed optics and removable face. The [refinement checks](output/refinement-checks.json) distinguish the revised structural limb surfaces from the integrated mounts and linkage. The roof and side panels form one printed clamshell. The fascia and its recessed bezel share a shallow compound curve. The face uses a 2.1 mm axial skin offset; normal wall thickness is checked separately on the curved solid.

The shell and front-face mass changed by +227.1 g. The sensor opening remains 168 mm wide. The curved face extends overall rigid length to approximately 494 mm. A central ribbed return attaches the nose wrap to the metal frame; four posts carry the removable face. Nominal attachment fits have no solid overlap. Final hardware, retention and sealing remain unselected.

Exact CAD rays at 83 selected surface locations measure at least 2.781 mm on the nominal shell and 1.689 mm on the finished face. The return tongue has a minimum sampled section of 43.72 mm². The fascia retains four mounting posts; the ribbed nose module supports its perimeter.

These samples check geometric material paths, not every local minimum or printed strength. Individual joint-clear intervals, folded-hip sweeps and coordinated-roll intervals match the preceding body at the same sample spacing. The [manufacturing review](review/manufacturing.html) provides oriented STL parts, unsliced 3MF plates and individual support notes. Final sliced supports, sensor modules and seals remain to be checked.

## Individual parts are available as CAD solids

Custom structural parts and modeled transmission components have separate STEP files. The browser parts catalog identifies each part’s role, mating interfaces, material, installed quantity and handedness. It includes the fixed roll cartridge, roll-to-hip motor carrier, hip-output hub, knee-stator plate and integrated knee-input crank. Unique rear mounts have separate exports. Motor envelopes are excluded from the individual manufacturing set.

Click a component in the assembly to open its isolated view or download its STEP. The [CAD-only archive](output/tinfox-individual-cad.zip) includes the catalog and all individual solids. Coordinates remain local to the assembly; the viewer centers each part only for inspection. STEP imports into Fusion 360 without a native feature timeline. Nominal holes do not specify threads or tolerance fits.

## The roll actuator drives a bearing-supported motor carrier

Each body-fixed roll actuator points fore/aft. Its output bolts directly into a machined elbow carrier that includes a 50 mm bearing journal. A perpendicular flange on that carrier locates the hip-pitch stator. A separate hinge pin or clevis is not used.

The crossed-roller bearing envelope is 50 × 66 × 8 mm. Its fixed outer housing transfers leg loads into the chassis; its inner ring supports the rotating carrier. The hip output hub carries a coaxial knee actuator inside the structural thigh root. Three metal ties and compression sleeves connect the hip output flange to the knee stator plate. The cradle and inner thigh remain continuous, with the service ring integrated into the removable outer thigh.

The motor interfaces use nine M3 stator positions on a 73 mm pitch circle and six M4 output positions on a 24 mm pitch circle. The roll coupling has through-access holes for its six output screws. The hip-output screw heads are recessed into the coupling flange. Low-head knee-output screws sit below the input-crank face to clear the rod. Delivered motor datums, screw length and engagement, bearing preload and retention still need manufacturing verification.

The fore/aft offset keeps perpendicular motor bodies apart. The enlarged annular motor cowls move with hip roll; the integrated knee-motor cradle and thigh move with hip pitch. Rounded fixed shoulder openings remain visible throughout roll. No provisional skins appear or disappear with joint angle. The coordinated roll demonstration spans ±60 degrees; separate checks distinguish body clearance from inter-leg contact. The [body roll audit](output/roll-shell-audit.json) records restricted roll when the front leg is deeply tucked; ±60 degrees is not available at every hip/knee combination.

## The recessed motor and rear pushrod make the leg narrower

The thigh pivot spacing is 170 mm. Two 22 mm cranks and a 170 mm steel rod form a 1:1 parallelogram. The crank phase is -78°. The knee motor stays at the thigh root, although its mass still contributes to hip-pitch inertia.

The knee actuator is recessed 12 mm into the thigh root. A 4 mm shorter output coupling brings the complete limb 16 mm inward per side. Neutral foot-center track is 270 mm, down from 302 mm. Width across the recessed shoulder caps is 325.0 mm; the surrounding shoulder shells span about 314 mm. The earlier raised caps spanned 322 mm. The structural inner cheek wraps around the actuator; the outer cheek is removable for access.

The foot uses a 22 mm spherical lower sole with its center 148 mm from the knee, retaining 170 mm effective reach. A ruled upper boot connects the sole rim to a neck centered on the shin. The lower sole is oriented for the nominal stance, and contact height is checked for every reported torque case. Boot attachment cavities and retaining fasteners remain unresolved. The shin sits between the thigh cheeks. A removable 12 × 8.4 mm precision sleeve spans the thigh cheeks. Two 6001 bearings sit directly in the structural shin halves, which also form the pushrod rocker. The fore/aft split passes through the bearing axes, allowing radial removal when the halves open. Bearing centers are 20 mm apart, with a 12 mm inner-race spacer. Integral shoulders retain the outer races axially. A recessed M8 bolt and outboard flange nut retain the sleeve; clamp preload and bearing fits require verification.

The thigh has 3 mm outer skins, ribs and two upper through-bolt compression sleeves. The motor-cradle tie clearances are 5.6 mm in diameter, avoiding a tangent boundary at the adjacent cavity. The fixed knee axle connects the lower cheeks; cross-bolts are omitted from the shin folding path. Its lower fork opens around the folded shin path. The shin has two structural halves with broad mating lands and full-width fastening ribs. Two M4 screws and captive metal compression sleeves join the halves. Clamp preload, joint slip, torsion and layer adhesion require qualification.

The output rocker extends above the knee in the shin frame, placing the rod behind the flexion opening. Both cranks use a −78° phase. Their 22 mm radius reduces worst-case rod force at 17 N·m to about 1.31 kN, compared with 1.61 kN for the earlier 18 mm cranks. The minimum moment arm is 12.93 mm across −156° to −48°, with a 36° margin to dead center. The equal crank radii preserve the 1:1 torque ratio.

The pushrod has a 6 mm square central section and pinned eyes. Two opposed flanged bushes and a retained 6 mm shoulder pin support each eye in a double-shear fork. Pin material, thread locking and wear life remain unqualified. Equal cranks do not increase motor torque. The force rises as the crank approaches alignment with the rod.

| Dimension | Value |
| --- | ---: |
| Main torso length / overall nose-to-tail length | 464 / 493.8 mm |
| Rigid torso width / maximum height | 222.4 / 103.5 mm |
| Central roof / shoulder crown above hip | 49.5 / 55.5 mm |
| Neutral width across shoulder caps | 321.6 mm |
| Structural thigh depth at joint seats / central web | 48 / 41.5 mm |
| Thigh / shank to foot center | 170 / 148 mm |
| Lowest skid below hip | 71 mm |
| Estimated base mass | 13.19 kg |

The [interactive knee study](review/linkage.html) compares both routings. The [mounting audit](output/mounting-audit.json) checks the rod against modeled fasteners and measures shin sections. The [exact-solid fit report](output/mounting-fit.json) checks the actuator and mounting plate inside the structural cradle.

## Motion is checked at sampled poses

The target limits follow the [official Go2 URDF](https://github.com/unitreerobotics/unitree_ros/blob/master/robots/go2_description/urdf/go2_description.urdf): roll ±60°, front pitch −90° to 200°, rear pitch −30° to 260°, knee −156° to −48°. Joint limits alone do not establish equivalent mobility.

| Leg | Roll with other joints neutral | Hip with knee −130° | Knee with other joints neutral |
| --- | --- | --- | --- |
| FL | -60° to -60°; -51° to 60° | -90° to 200° | -156° to -48° |
| FR | -60° to -60°; -51° to 60° | -90° to 200° | -156° to -48° |
| RL | -60° to -60°; -51° to 60° | -30° to 260° | -156° to -48° |
| RR | -60° to -60°; -51° to 60° | -30° to 260° | -156° to -48° |

| Preset | Intersections | Minimum checked separation |
| --- | --- | ---: |
| stand | None | 1.50 mm |
| studio | None | 1.50 mm |
| raised | None | 1.50 mm |
| crouch | None | 1.50 mm |
| reach | None | 1.50 mm |
| fold | None | 1.50 mm |
| splay | None | 1.50 mm |
| side reach | None | 1.52 mm |

The motion report includes 4,177 sweep and transition samples, plus preset distance checks. Neutral-to-preset transitions, including the [0°, 45°, −75°] studio stance, contain 0 intersecting samples.

Coordinated roll clears -60° to 60°, using front hip −35°, rear hip 35° and knee −70°. This is a free-space check, not a self-righting demonstration.

Checks omit intended bearing and motor-output interfaces, rigidly attached pairs and small hardware. Wires, tolerances, hard stops, ground contact, flexible seals and load deflection are not modeled. Some simultaneous joint combinations collide. Sampled checks do not prove continuous trajectory clearance.

## The battery cassette improves belly clearance

Two assumed 125 × 85 × 65 mm packs sit side by side under the electronics shelf. Each compact 5 Ah pack and adapter is allocated 0.70 kg. Exact commercial packs, contacts, latches and electrical protection remain unselected.

The battery audit found 0 intersections against checked rigid parts, including fixed chassis parts. The skid is 48 mm higher than the preceding 119 mm-deep arrangement.

| Pose | Ground to skid |
| --- | ---: |
| stand | 226 mm / 8.9 in |
| raised | 242 mm / 9.5 in |
| crouch | 85 mm / 3.4 in |

The 12-inch belly-clearance target remains unmet. Maximum stair height also depends on foot placement, body pitch and stair-nosing contact. It cannot be inferred from link length alone.

## Weight reduction toward 10 kg

The preceding cartridge assembly was 16.99 kg. The current estimate is 13.19 kg, a reduction of 3.80 kg. It remains 3.19 kg above the 10 kg target before cargo.

Geometry and catalogued component changes save 2.40 kg. Smaller battery allowances save 0.80 kg, and the compact electronics allocation saves 0.60 kg. These allocations require a weighed bill of materials.

The structural changes include integrated motor cradles, pocketed output hubs, notched chassis rails, a thin skid, hollow curved shins and tubular knee shafts. The roll bearing changes from 270 g to 80 g per leg. Printed masses use actual CAD solid volumes at PETG density; no arbitrary infill discount is applied.

Both 5 Ah packs are assumed to be installed. Larger 8–12 Ah packs and a heavier onboard computer increase mass. A 36 V nominal series pair also requires actuator speed and power verification at that supply voltage.

| Mass category | Estimate |
| --- | ---: |
| Steel parts and bearings | 1.25 kg |
| Printed PETG solids | 2.31 kg |
| envelope | 0.01 kg |
| Two compact packs and adapters | 1.40 kg |
| Aluminum parts | 1.99 kg |
| Twelve RS-02 actuators | 4.86 kg |
| Feet | 0.17 kg |
| Computer, sensors, wiring and converters | 0.80 kg |
| Unmodeled hardware allowance | 0.40 kg |
| Base total | 13.19 kg |
| With 1 kg cargo | 14.19 kg |

## Torque is recalculated from the revised assembly

The estimated base mass is 13.19 kg. This includes 1.4 kg of assumed compact packs, 0.8 kg for computer, sensors and wiring, and 0.4 kg for unmodeled hardware. The cargo case adds 1 kg.

The calculation combines prescribed foot-force moments with gravity moments of the modeled moving parts. Knee efficiency is assumed to be 90%. Joint accelerations, torque-speed limits, thermal response and dynamically balanced gaits are not simulated.

The stair case places 60% of weight on one foot. Braking adds a backward force equal to 25% of that vertical force. The splayed case adds an outward force equal to 20% of vertical load. Pulse cases place half of 2.5 or 3 times robot weight on each stance foot.

| Case | Cargo | Roll | Hip pitch | Knee motor |
| --- | ---: | ---: | ---: | ---: |
| four foot stand | 1 kg | 1.89 N·m | 0.15 N·m | 2.80 N·m |
| two foot stand | 1 kg | 4.22 N·m | 0.53 N·m | 5.66 N·m |
| three foot crouch | 1 kg | 2.67 N·m | 0.49 N·m | 6.82 N·m |
| stair reach 60 percent | 1 kg | 7.12 N·m | 14.44 N·m | 13.44 N·m |
| reach with braking | 1 kg | 7.12 N·m | 10.22 N·m | 12.64 N·m |
| splayed two foot | 1 kg | 14.46 N·m | 0.48 N·m | 5.33 N·m |
| unloaded 2.5g pulse | 0 kg | 10.40 N·m | 1.54 N·m | 13.24 N·m |
| unloaded 3g landing screen | 0 kg | 12.56 N·m | 1.90 N·m | 15.90 N·m |

The reference is 6 N·m rated and 17 N·m peak from the [RS-02 manual](https://github.com/RobStride/Product_Information/blob/main/Product%20Literature/CAN2.0/RS02/RS02User%20Manual260713.pdf). Its rated test uses a 260 × 280 mm heat sink. That value is not a demonstrated holding limit for an enclosed printed pod.

The all-RS-02 design remains torque-constrained. Some support cases exceed the rated reference. Compare each prescribed pulse with the 17 N·m peak reference; these cases leave limited reserve for unmodeled acceleration and impacts. Loaded stairs, running and jumping require a lower finished mass, constrained contact loads and measured actuator performance before acceptance.

## The limb geometry has measured tradeoffs

The [whole-limb profile](../design/14-limb-profile.svg) compares the preceding and revised CAD in open and folded poses. Both retain the hip, knee and foot centers. The [comparison data](output/limb-revision-comparison.json) records the geometry fingerprints and calculation scope.

| Geometric metric | Preceding limb | Revised limb |
| --- | ---: | ---: |
| Moving mass about one hip | 1.0591 kg | 1.1735 kg |
| Hip-pitch inertia at neutral stance | 0.01165 kg·m² | 0.01350 kg·m² |
| Knee-axis inertia at neutral stance | 0.001389 kg·m² | 0.001461 kg·m² |
| Minimum sampled thigh section modulus | 1424 mm³ | 1420 mm³ |
| Minimum sampled shin section modulus | 1082 mm³ | 1007 mm³ |
| Folded thigh-to-shin gap | 1.87 mm | 1.60 mm |

The inertia estimates use one front-left limb at hip 30° and knee −60°. They combine mesh tensors scaled to nominal part masses and exclude reflected rotor and gearbox inertia. They do not establish dynamic control performance.

The shin has two open structural halves with direct bearing seats, an integral rocker and a lower cavity. Both halves contribute to the measured section. The lowest sampled outer-wall thickness is 3.85 mm.

The section comparison measures the preceding and current surfaces from complete solid geometry. Smoother external curves change the available bending section; the table records the tradeoff. Both require material, fastener, fatigue and load testing. The profile is a design candidate, not a globally optimal geometry or a mobility-equivalence claim.

Applying the largest prescribed hip-pitch moment uniformly to the thigh gives 10.2 MPa nominal sagittal bending stress. Applying the largest knee-output moment to the shin gives 14.2 MPa. Under an equal material allowable, the thigh has lower utilization in this limited screen.

These estimates divide moment by minimum sampled section modulus about the local pitch axis. They omit transmission point forces, distributed loading, holes, torsion and print anisotropy; they do not qualify either member.

## Structural and manufacturing checks remain preliminary

The shin screen uses the smallest sagittal section modulus measured from 0.2 mm CAD slices at 5 mm intervals. Applying the maximum case joint moment uniformly gives a bending stress of 14.4 MPa; a factor of two requires 28.7 MPa coupon strength before local effects.

The mounting audit measures the paired thigh sections, assembled shin sections and remaining outer wall at four stations. Section modulus relates bending moment to nominal bending stress. These geometry measurements do not establish stiffness or printed strength.

This sampled bending screen does not establish torsional strength or capture every local section minimum. Printed layer bonding, creep, fatigue, holes, bearing seats, fastener slip and impacts require separate tests. A required coupon result is not an assigned PETG allowable.

At 17 N·m and the worst linkage angle, rod force is 1315 N. Ideal pinned buckling capacity for a 6 mm round steel core is 4345 N. Joint clearance and imperfections reduce this idealized result.

A 6 mm pin with a 14.2 mm double-shear support span has 224 MPa nominal equivalent stress. The 12 × 8.4 mm tubular axle screen gives 112 MPa bending stress under a central rod-force assumption over 44 mm.

The roll cartridge and motor carrier are machining candidates. Printed versions are fit-check prototypes only. Bearing shoulders, retainers, fits, fastener grades, hard stops, cable exits, cooling paths and chassis connections need detailed manufacturing drawings. The specialty roll bearing also leaves the sub-$100 replacement-leg target unverified.

All printed-part bounding boxes fit the H2D envelope with the modeled margin. The supplied STL orientations require slicer review and load qualification. The integrated motor cradle needs supports beneath its offset limb surfaces; keep the long limb axis in the bed plane and verify support removal before printing a full set.

Assembly order:

1. Bench-assemble each leg cartridge, installing hidden motor-interface screws before closing adjacent flanges.
2. Join leg cartridges to the chassis rails, fit both transverse ties and the fixed lower brace, and attach the end modules.
3. Prepare the cassette, insert its four trapped nuts and support it beneath the frame.
4. Secure the cassette with its four side screws. Fit the flat electronics deck with four independent top-access screws.
5. Install and route the selected electronics while the sides are open.
6. Connect the roof harness and lower the top-and-side clamshell onto the frame. Secure its four side screws.

The [assembly guide](output/assembly-guide.txt) records the removal sequence, tested tool envelopes and unresolved retention details. The cassette remains attached during deck removal. Support it only when removing its independent side screws.

## Research informs the arrangement

- [PADWQ leg design, section 2.2](https://www.mdpi.com/2076-3417/11/9/3762): proximal coaxial motors and a parallelogram transmission. Longer cranks reduce force in printed parts. The rearward routing and dimensions used here come from Tinfox geometry checks.
- [Benjamin Katz, MIT thesis, chapter 3](https://dspace.mit.edu/bitstream/handle/1721.1/118671/1057343368-MIT.pdf): short abduction-to-hip carrier and coaxial proximal actuators. Tinfox retains the requested rigid pushrod instead of that design’s belt transmission.
- [MIT Cheetah actuation paper](https://fab.cba.mit.edu/classes/865.18/motion/papers/mit-cheetah-actuator.pdf): proximal actuator concentration and transmission design. This supports the layout principle, not Tinfox performance claims.
- [THK crossed-roller catalog](https://tech.thk.com/en/products/pdf_download.php?file=E_18_CrossRollerRing.pdf): RA5008 envelope 50 × 66 × 8 mm and 0.08 kg. Fits, preload and moment capacity must be selected for this application.
- [US NSK 6001 bearing listing](https://littlemachineshop.com/products/bearing-6001-2rs): 12 × 28 × 8 mm knee bearing envelope.
- [RobStride manufacturer information](https://github.com/RobStride/Product_Information): motor manual and CAD reference. Motor internals and connectors are simplified in this assembly.

## Hardware and limb assembly

[The hardware review](review/hardware.html) links supplier candidates, quantities and fit limitations. [The limb assembly guide](output/limb-hardware-guide.txt) defines the bench assembly sequence. The outer thigh incorporates the motor service ring; exact-solid checks cover outer-half removal and plate/motor insertion. The [print-strength review](review/strength.html) records layer directions, rod force and the limits of solid PETG. Knee axle clamp preload, roll bearing retainers, motor tie hardware and foot attachment remain unresolved.

The [dimensional coupon](output/print-fixtures/dimensional-coupon.step) checks carrier seats, sleeve holes and nut pockets before full-size printing. It does not qualify strength.

## Reproduce the artifacts

```bash
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/build.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/export_parts.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/audit_mounting.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/audit_body.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/audit_assembly.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/engineering.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/prepare_manufacturing.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/analyze_limb_revision.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/compare_body_revision.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/check_refinement.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/verify_manufacturing.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/audit_limb_assembly.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/audit_integration.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/make_fit_coupon.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/write_hardware_review.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/test_model.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/write_assembly_guide.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/write_report.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/write_summary.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/write_manufacturing_guide.py
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/serve.py
```

Run these commands from the repository root. Install model dependencies from `tinfox/proposals/sculpted/model/requirements.txt` in a Python 3.12 environment. Render the studio with `render_studio.py` in a separate Python 3.11 environment containing `bpy==5.0.1` and NumPy.

CAD fingerprint: `144a84e88daed50139f890480e9f1a1740cfb20c773e740ba6b4e9c1b9eede5e`.
