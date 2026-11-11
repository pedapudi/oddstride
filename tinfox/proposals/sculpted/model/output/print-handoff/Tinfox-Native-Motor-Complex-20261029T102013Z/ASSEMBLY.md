# Assemble one unpowered RS02 motor complex

This guide covers one detached hip/thigh complex with three RS02 actuators,
paired 6810 bearings and thirteen custom parts. The shin, knee axle, pushrod
and their hardware belong to the later complete-limb stage.

The current parts are native Fusion geometry saved in Leg version 24. Direct
exports were captured at version 23; the final saved/reopened checkpoint preserves
that geometry and its placements. The hardware, reference seating and print
transforms are recorded in each package's manifests.

The Mac packages are available through:

- `~/Downloads/Tinfox/Current-Motor-Fit/` for the initial five-object fit plate.
- `~/Downloads/Tinfox/Current-Motor-Complex/` for the complete corrected complex.

The full nominal screen accounts for 121 physical bodies and all 7,260 possible
pairings. 473 candidate pairs received exact solid checks. The only positive
contacts are 45 verified motor-thread envelopes and 12 connected cable envelopes.
An Open CASCADE solid-intersection failure at the touching thigh split is
retained and resolved by independent checks on the saved native Fusion solids. See the
[static review](../analysis/dfma/knee-stator-seats/static-screen-review.md).
These results qualify supported, unpowered fit assembly. They do not establish
printer calibration, preload, creep, fatigue, operating strength or loaded motion.

## Check the motor interfaces first

Open `00-RS02-motor-fit.3mf` in Bambu Studio. Its two short case gauges retain
their recorded generated source. The three reusable mounting interfaces derive
from the current canonical native Fusion parts. Earlier socket-head knee plates
and unrecessed hip closures are superseded.

Use the actual H2D single-nozzle, nozzle and filament profile. The files are
unsliced; inspect orientation, supports and layers before printing. Let parts
cool before measuring. Align every hole while each interface sits flat against
the motor; do not use screw tension to force a misaligned fit.

The thigh gauge has an 80.5 mm bore and the hip gauge an 81.5 mm bore. They check
case openings only. They do not reproduce the hub's shallow case relief,
connectors, bearing fits or complete installation path.

## Obtain hardware for one complex

Quantities exclude spares. Use metric coarse threads and the specified head
standards. There are 18 M3 × 8 countersunk screws across the two stator interfaces.

| Connection | Specification | Quantity |
| --- | --- | ---: |
| Actuators | RobStride RS02 | 3 |
| Roll bearing pair | 6810-2RS, 50 × 65 × 7 mm | 2 |
| Long motor ties | M3 × 60 ISO 4762 socket-head cap screw | 3 |
| Hip output to hub | M4 × 8 ISO 4762 socket-head cap screw | 6 |
| Knee output to crank | M4 × 12 ISO 4762 socket-head cap screw | 6 |
| Knee stator to plate | M3 × 8 DIN 7991 countersunk screw | 9 |
| Hip stator to closure | M3 × 8 DIN 7991 countersunk screw | 9 |
| Roll output coupling | M4 × 25 countersunk screw | 6 |
| Roll stator/housing | M3 × 30 ISO 7380-1 button-head screw | 9 |
| Roll outer-race retainer | M3 × 25 button-head screw | 3 |
| Recessed cup closure | M4 × 16 ISO 7380-1 button-head screw | 3 |
| Thigh shell clamps | M4 × 25 button-head screw | 2 |
| Tie and retainer nuts | Ordinary M3 hex nut, 5.5 mm across flats | 6 |
| Closure and shell-clamp nuts | Ordinary M4 hex nut, 7 mm across flats | 5 |
| Shell-clamp washers | 4.3 mm ID × 12 mm OD × 1 mm nominal | 4 |
| Long pod tubes | 5 mm OD, 3.4 mm ID, 41 mm long | 3 |
| Short pod tubes | 5 mm OD, 3.4 mm ID, 6 mm long | 3 |
| Thigh-clamp tubes | 8 mm OD, 4.3 mm ID, 18 mm long | 2 |

The cup closure uses no separate washers. Its recessed seats spread the head
load through reinforced lugs. Do not add a washer inside those recesses.
Amazon.com is the preferred source for ordinary fasteners when dimensions,
head standard and grade match. Precision stock can come from McMaster-Carr,
Fastenal or a manufacturer with US ordering. Seller stock and delivery have
not been verified for this kit.

The manufacturer drawing specifies nine M3 stator holes on a 73 mm pitch circle
with 8 mm depth, and six M4 output holes on a 24 mm pitch circle marked 7 mm minimum
depth. The prototype choices target at most 6 mm motor penetration. Check the
actual motor revision, head seating and usable depth before tightening.
[Manufacturer manual](https://www.robstride.com/assets/product_manual_robStride02-e7f9f7c4.pdf).

Nominal penetrations are 4.3 mm at the hip output, 5.4 mm at the knee output,
4.9 mm at the knee stator, 5.1 mm at the seated hip stator and 4.2 mm at the seated
roll-output screws. Closing an actual mounting-face gap changes engagement;
verify the physical stack. M3 × 65 ties and M3 × 35 roll-stator screws are not
substitutes for the specified lengths.

## Preserve the prepared print orientations

The hip-stator closure prints with its broad front face on the bed. Printing
on its three projecting rear lugs would suspend the central ring. Its shallow
counterbore roofs span 1.7 mm radially outside the pilots; inspect their layers
and seating quality. Curved thigh exteriors and the horizontal carrier journal
also require support review.

The prepared plates use the H2D single-nozzle 325 × 320 × 325 mm envelope. Dual-nozzle
mode is narrower; rearrange objects if using it. Individual prepared STL/3MF
files are provided for separate prints. Raw native 3MF files retain CAD coordinates.
The optional printed sleeves are dimensional surrogates for finger-tight fit
checks. Use measured metal tubes for later clamp-load or powered tests.

## Assemble the roll support and hip carrier

Keep motors disconnected and support their weight throughout assembly. Use
ordinary metric hex keys and 5.5 mm/7 mm wrenches. No tightening torque is prescribed
for the printed fit parts.

1. Leave the roll motor and rear stator plate off while preparing the bearing
 cartridge. Insert the inner backplate from the motor side.
2. Fit both bearings and their separate inner- and outer-ring spacers. Start
 the front retainer screws while the rear nut pockets are accessible. Keep
 the nuts at their forward pocket floors; fit the rear plate/motor afterward.
3. Attach the roll stator/housing stack with nine M3 × 30 screws. The retainer
 controls the outer-ring stack separately; tightening it does not establish
 a qualified bearing preload.
4. Insert the carrier journal into the bearing pair. Align the inner backplate
 and install six M4 × 25 output screws through the empty motor cavity.
5. Insert the hip motor. Attach its closure with nine M3 × 8 countersunk screws.
 Seat the three registered rear lugs in the cup's matching reliefs. Secure
 the closure with M4 × 16 buttons and ordinary nuts, without washers.
6. Seat each button directly on its counterbore floor. The checked geometry
 preserves 1.8 mm web beneath the head and 1 mm nominal separation from the pod
 ties through continuous hip rotation. Hold nuts through the radial cup slots.
7. Attach the hip output hub with six M4 × 8 sockets before the knee motor blocks
 their driver routes.

The revised cup and closure preserve the motor-seat plane. Their thicker rear
lugs, relocated registers and open recesses are required together. Do not mix
an older cup with the reinforced closure.

## Close the thigh around the knee motor

Install the knee stator and crank screws while the outer shell is absent.
Their straight driver routes are blocked by the installed front roof; service
requires removing the outer shell.

1. Fit the inner thigh, long metal tubes and knee motor to the hub assembly.
 The relieved hub preserves all tube-bearing lands and nominally clears the
 case by 0.25 mm. Confirm actual case clearance and connector orientation.
2. Attach the seated knee stator plate with nine M3 × 8 DIN 7991 screws. Its
 countersinks keep the heads clear of the rotating crank. Align its three
 outer tie holes and integral pads with the long tubes.
3. Attach the input crank with six M4 × 12 sockets through its open head channels.
4. Install the short tubes and slide the outer shell over the preassembled
 module through its stator-plate passage.
5. Insert three M3 × 60 ties through the outer channels. Seat each head on its
 short tube and start the ordinary nut at the hub. Nominal nut engagement is
 2.4 mm with 1.6 mm thread projection.
6. Fit the two shell-clamp tubes, four large washers, M4 × 25 buttons and nuts.
 Check mating faces and connector access before gentle closure.

Check actual screw projection, seating and free hand motion. Keep the assembly
supported. Do not power it or lift a payload through printed fit surrogates.

## Match every part to the corrected source

The revised knee uses flush countersinks. The hip closure uses reinforced,
recessed lugs; its matching cup has moved locating bosses. The hub has a shallow
case-clearance relief. The manifest identifies native versions, file hashes,
part mappings, reference seating and print transforms. Earlier complete-limb
or Leg 20 packages are historical references and must not supply these revised
interfaces. Fusion material defaults do not constitute a qualified mass or
strength model; the viewer leaves native mass unestimated.
