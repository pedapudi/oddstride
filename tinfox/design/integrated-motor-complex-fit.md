# Integrated three-motor limb fit assembly

This guide covers one detached, supported, unpowered motor complex with three
RobStride RS02 actuators. Its two structural thigh halves also mount the hip
output and knee motor. The package tests motor insertion, connector routing,
fastener access and bearing service. Printed strength and powered operation
require physical qualification.

Use the package's `native-source-manifest.json` to identify its saved Fusion
revision. Use its `hardware.csv` for screw lengths, head styles, washers and
metal tube dimensions. Earlier packages with a separate hip output hub, knee
stator plate and hip closure describe a different assembly.

## Fabricated pieces

| Part | Quantity | Function |
|---|---:|---|
| Paired-bearing housing | 1 | Supports the two hip-roll bearings and attaches to the chassis |
| Rear stator backplate | 1 | Locates the roll motor and rear bearing stop |
| Shared front cap | 1 | Retains the front bearing with the roll stator screws |
| Rear-loaded hip motor cup | 1 | Connects the roll output to the hip motor |
| Primary structural thigh | 1 | Carries the hip-output flange, knee motor cradle and inner knee support |
| Secondary structural thigh | 1 | Closes the thigh and completes the knee motor mounting |
| Inner bearing backplate | 1 | Retains the existing inner bearing interface |
| Inner and outer race spacers | 2 | Control the separation of the two roll bearings |
| Knee input crank | 1 | Drives the knee pushrod |

These are ten custom pieces. Six additional metal compression tubes support
the four long knee-stator screws and the two thigh clamps. Printed tube or race
spacer surrogates are for finger-tight fit checks. The assembly needs metal
parts in those locations for powered testing.

## Motor-complex hardware

All screws in this table use ordinary ISO 4762 socket heads. M3 threads use
0.5 mm pitch; M4 threads use 0.7 mm pitch. Lengths are measured from beneath
the head. Use the package's hardware list to verify the saved geometry before
ordering or assembly.

| Connection | Screw | Quantity |
|---|---|---:|
| Shared roll cap and stator | M3 × 35 | 9 |
| Hip stator | M3 × 8 | 9 |
| Primary knee-stator face | M3 × 6 | 5 |
| Secondary knee-stator columns | M3 × 45 | 4 |
| Roll output coupling | M4 × 25 | 6 |
| Hip output to primary thigh | M4 × 8 | 6 |
| Knee output to crank | M4 × 12 | 6 |
| Thigh shell clamps | M4 × 40 | 2 |

One motor complex uses 47 screws, two ordinary M4 hex nuts, eight flat washers
and two sealed 6810 bearings, excluding the three motors and their connectors.
The washers are 12 mm outside diameter, 4.3 mm inside diameter and 1 mm thick.
The bearings are 50 × 65 × 7 mm. Four washers sit beneath the long M3 screws;
each thigh clamp uses one washer at each end.

The five short knee-stator screws sit directly on their flat seats. The modeled
M3 × 6 stack leaves 4.2 mm of motor-thread penetration, a 1.8 mm mounting web
and 0.6 mm nominal axial clearance beneath the crank. Adding washers at these
five positions would consume that clearance. Inspect actual head height,
printed seating faces and crank clearance during the unpowered fit check.

The four motor tubes are 6 mm outside diameter, 4 mm inside diameter and 39 mm
long. The two thigh clamp tubes are 8 mm outside diameter, 4.3 mm inside diameter
and 29 mm long. Tube ends must be square and their lengths must match the
actual printed seating faces. An overlong tube can lift a washer clear of the
shell; a short tube transfers preload into the plastic. Nominal CAD dimensions
do not establish an acceptable physical fit.

## Print orientation and supports

Open the unsliced files in `plates/` in Bambu Studio. Select the actual H2D,
nozzle and filament. Check every plate's support preview before printing.
The layouts use the single-nozzle build envelope, 325 × 320 × 325 mm.

Both thigh halves should lie with their lengths along the bed and their outer
faces downward. Their local CAD orientation uses a −90° rotation about X,
followed by translation onto the bed. Both halves fit side by side on one
plate. Their curved faces and offset structures require localized supports.

The primary half needs support under the proximal stator face and offset knee
and bridge regions. Placing only the hip flange on the bed leaves the lower
limb suspended above it. The secondary half needs support around its curved
exterior contact regions and knee cheek, with its main cavity facing upward.
Keep supports away from bearing, motor-pilot, washer and screw seating faces
where the slicer permits. Inspect those faces after support removal.

Print the rear-loaded hip cup with its rear motor opening downward, using
a +90° rotation about local X. Its flat rear contact ring is about 865 mm²;
use a brim. Support the integral front stator face from inside the 81.5 mm
opening and support the projecting roll journal and fan locally. The opening
provides access to remove the internal supports. Keep supports clear of the
motor bore, screw seats and bearing journal where practical. The cup fits within
120.5 × 88 × 77.4 mm in this orientation.

Laying the limb length along the bed improves the orientation of filament
paths for limb bending. It does not establish strength under axial motor loads,
bearing press fits, impacts or sustained bolt preload. The fit prototype is
not a payload or locomotion qualification.

## Assembly order

1. Compare the physical motors, bearings and connectors with their printed
   interfaces. Check the bolt lengths against actual blind thread depth before
   tightening. A screw must clamp its intended stack before its tip bottoms.
2. Assemble the roll motor, rear stator backplate, bearing housing, both 6810
   bearings, race spacers and shared cap in the order shown by the CAD section.
   Preserve the independent bearing-retention clearance. Do not use screw
   tightening to set bearing preload through printed plastic.
3. Install the shared cap and roll stator screws before fitting the rotating
   hip cup. The cup obstructs their driver paths after installation.
4. Fit the empty hip cup and install its roll-output screws through the open
   driver approach. Insert the hip motor through the rear opening with plugs
   disconnected, then install its stator screws.
5. Attach the primary thigh to the hip output using all six output screws.
   Install these screws before the knee motor blocks their drivers.
6. Insert the knee motor sideways into the primary cradle at its modeled
   connector clock. Pass its output pilot through the open stator face. Install
   the short stator screws and the knee input crank before closing the thigh.
7. Stage the four motor compression tubes, two clamp tubes and connector plugs.
   Route the cables through their modeled openings. Flexible cable bend and
   pinch clearance need physical inspection during closure and movement.
8. Slide the secondary half into place. Install the long knee-stator screws,
   washers and two shell clamps according to `hardware.csv`. Hold the inner
   clamp nuts with a socket no larger than the modeled 10 mm outside diameter.
   Confirm sufficient socket depth for each projecting screw tip.
9. Inspect the assembly with the actuators unpowered. Check the pushrod route,
   driver access and the ability to reopen the shell before proceeding to
   bearing fits or a complete limb assembly.

## Bearing service

The paired roll-bearing housing has a through bore and removable end parts.
Bearing removal requires disassembling the hip cup and releasing the shared
stator clamp while supporting the module on the bench. Use a driver that acts
on the bearing race being fitted or extracted. Do not force a bearing into a
printed seat whose measured fit is incorrect.

The distal knee interfaces retain their existing bearing supports and removal
access. A fit package does not establish polymer interference tolerances; inspect
the actual print and bearing before pressing them together.
