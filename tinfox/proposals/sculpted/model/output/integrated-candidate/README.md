# Continuous thigh shells and a deeper structural neck

The review assembly has a rounded body cover, continuous two-piece thigh shells,
conventional shoulder screws and a deeper camera neck mounted across the chassis
rails. Open <http://127.0.0.1:8770/viewer/?design=v2> to inspect the robot, motion
and individual parts. STEP and STL files are available for changed parts.
`updated-robot.step` and `updated-robot.glb` contain 424 physical components.

The lower thigh gradually widens into rounded axle cheeks. A curved articulation
opening leaves room for the shin to fold; the pushrod channel extends into that
opening. The motor interfaces and integral bearing backup stops are retained.
Both thigh halves remain individual connected solids, with no separate knee
head or added external brace.

The camera neck has a deeper central support with a cable channel. Its lower
half connects the front chassis saddle to the camera surround. The upper hood
and face lift off together. In the middle of the lower support, the material
section increases from about 13 mm² to 342 mm². This is a geometry measurement,
not a load-capacity result. The four rail-joint locations and metal crossmember
carry the camera housing attachment.

## Conventional pivots fit the revised fork geometry

Both knee cranks retain a 28 mm radius and the rod retains its 170 mm center
distance. Conventional 6 × 20 mm shoulder screws face inward; M5 nuts sit in
integral outboard pockets. The head is 4.5 mm high and the threaded end is
9.75 mm long. The longer thread fits inside the revised thigh pocket.

Assemble the input crank, pushrod and captured nut before mounting the crank to
the motor. The inward-facing screw head has restricted driver access afterward.
Four input-crank nuts are added. See the [hardware specification](../../COMPACT-HARDWARE.md)
for dimensions, supplier references and the unresolved inventory check.

## Local knee motion and nominal service fits pass

The assembled left-front knee mechanism has no reported mesh intersections at
109 angles from −156° through −48°, sampled in one-degree steps. This includes
the thigh, shin, rod, pins, bearings and fasteners. The four-leg assembly also
has 35 sampled pose checks and linkage-closure checks for each leg.

All 69 nominal solid-fit and sampled bearing-service checks pass. They cover
complete bearing-seat walls, outward extraction after splitting the shin,
extraction-pin access, clamp and pivot fits, and the camera cradle's frame fit.
The full STEP export reopens with 424 components and a relative volume difference
below 0.000001%.

The front-limb audit includes modeled knee hardware against the fixed chassis.
It reports no knee-hardware intersections in its sampled poses or sweeps.
Deep folding still brings the front inner thighs into the body shells. Existing
motor-flange tie tips also contact the carriers in several poses. Combined roll
and hip angles can collide. The viewer sliders are exploration limits, not an
approved operating envelope.

## Mass, printing and strength remain qualification work

Estimated base mass is 13.41 kg, including assumed batteries, electronics and
allowances. With 1 kg additional payload, prescribed four-foot standing requires
about 2.85 N·m at the knee motor; two-foot standing requires about 5.76 N·m.
The case assigning 60% of supported weight to one foot during stair reach requires
about 14.68 N·m at hip pitch and 13.66 N·m at the knee motor.

Those values are prescribed-force estimates. They do not establish gait loads,
thermal endurance or impact capacity. The conventional fastener dimensions have
been checked against a supplier listing; sufficient on-hand stock remains unverified.

The limb halves retain open cavities for manufacturing and bearing service.
Place the limb length in the print bed plane and inspect support requirements
at the motor pocket, flared knee cheeks and curved neck underside. Actual slicer
orientation, layer loading, creep, fatigue and tool access need prototype checks.
Rounded contours alone do not establish printed strength.

The generated CAD remains authoritative for this proposal. Native Fusion work
continues against the separate migration reference; this revision has not passed
that migration gate. Each geometry audit records the model hash, and the viewer
shows the full-assembly download only when its export report matches the model.
