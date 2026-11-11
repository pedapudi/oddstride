# Reduce separate mounting stages in the leg

The integrated leg uses **52 threaded screws or functional pins**, compared with
61 in the separate-adapter design. It retains all factory motor screws. A shared
bearing cap, rear-loaded hip cup and two structural thigh halves replace
separate closure and motor-interface stages.

The ten-part proximal fit assembly is saved in native Fusion Leg37. Its ordinary
M3/M4 screws all use ISO 4762 socket heads. The
[fit and assembly guide](integrated-motor-complex-fit.md) gives the current
hardware, print orientations and assembly sequence. Four-leg adoption remains
separate from this supported, unpowered fit release.

The **37-fastener reduced-pattern option remains unqualified research**. It would
require independent qualification of fewer motor mounting screws. Its counts
must not be substituted for the full-pattern fit package.

## Count physical pieces separately from CAD components

The frozen whole-leg inventory contains 95 purchased hardware pieces per leg,
excluding three motors and twenty-four connector references. Its 26 fabricated
CAD entries represent 29 physical pieces: each of three pod-sleeve entries
contains both a long and a short tube.

| Per leg | Current | Integrated architecture, full motor patterns | First reduced-pattern proposal |
|---|---:|---:|---:|
| Motor mounting screws | 45 | 45 | 30 |
| Other screws and shoulder pins | 16 | 7 | 7 |
| Nuts | 16 | 7 | 7 |
| Washers | 10 | 14 | 13 |
| Pushrod bushings | 4 | 4 | 4 |
| Bearings | 4 | 4 | 4 |
| Purchased hardware total | 95 | 81 | 65 |
| Fabricated physical pieces | 29 | 24 | 23 |
| Fabricated CAD entries | 26 | 24 | 23 |
| Hardware plus fabricated pieces | 124 | 105 | 88 |

The first motor-pattern goal removes 24 threaded fasteners and 36 physical
pieces per leg. For four legs, that is 96 fewer threaded fasteners and 144
fewer pieces. These totals exclude motors and connector references in every
column. They retain both structural halves of each thigh and shin.

Exact names, baseline hashes and the count arithmetic are retained in
[counts-and-load-screens.json](../analysis/dfma/fastener-reduction/counts-and-load-screens.json).
The source is the current frozen whole-leg target, with the corrected native
motor complex. Later native pose-history repairs do not establish new strength.

## Share the roll-bearing cap with the motor stator screws

Use the existing stator screws to clamp a stepped removable front cap, the
through-bore cartridge and the removable rear stator plate. Delete the three
separate retainer screws and their three nuts. Keep both 6810 bearings, their
14 mm center spacing, both race spacers and the removable rear plate.

The cap needs two controlled contact levels. Metal housing lands carry bolt
preload; the bearing-retaining lip has its own specified axial clearance. Bolt
tightening must not determine bearing preload through printed material.
The native candidate uses a continuous 3 mm cap and ordinary M3 × 35 screws.
The new head seat at X−47.5 gives 5 mm nominal motor penetration. A rear relief
leaves 0.15 mm nominal race-stop clearance while the housing hard stop remains
at X−50.5. The older assembly's M3 × 30 choice belongs to its different stack.

This is one redesigned cap replacing one existing retainer, not another layer.
With the cap and rear plate removed, the cartridge must retain its full bore
for outer-race drivers and extraction from either end. Axial steps are reached
from the open end; no internal circlip groove or reverse-facing cutter is needed.
The present bearing seats must be supported across the relocated cap joint.

**Count change:** six purchased pieces removed; fabricated piece count unchanged.
The motor screws now serve bearing retention as well as stator mounting, so
their combined loads require analysis before reducing their number.
Removing this cap also releases the stator clamp; service the module supported
on the bench.

## Rear-load the hip motor into an integral front mounting face

Make the hip stator face part of the motor carrier and open the rear motor
mouth. Delete the separate closure, three M4 closure screws and three nuts.
The existing nine M3 stator holes remain available in the integral face.

The detached-module assembly sequence is:

1. Assemble the roll support and motor.
2. Install the empty carrier journal and its six roll-output screws. Preserve
   the existing straight driver window.
3. Insert the hip motor from the rear, with plugs disconnected. Its two fixed
   socket references remain on the motor.
4. Install the hip stator screws from the front, then attach the thigh assembly.

A read-only packaging screen of this proposal passes 177 exact checks,
including eleven rearward insertion positions and all six coupling-driver
paths. It includes the current roll support, seated coupling screws, motor and
fixed sockets. The chassis is absent. Motor service should therefore remove
the complete module from the chassis before withdrawing the hip motor.
[Packaging evidence](../analysis/dfma/knee-stator-seats/rear-loaded-cup-packaging-proposal.json).

Removing the rear diaphragm takes away approximately 11,911 mm³ of material.
Eight direct journal/web sections remain unchanged, but the diaphragm also
restrains cup ovalization. Preserve a broad continuous front mounting ring and
add integral fan-shaped gussets between that ring and the journal. Keep them
outside the motor insertion cylinder and driver paths. Do not transfer the
load through the former small closure-lug roots.
[Section evidence](../analysis/dfma/knee-stator-seats/rear-loaded-cup-structure-screen.json).

Machine the motor pocket from its open rear and the mounting face from the
front. Journal and driver features have their documented perpendicular setups.
Print orientation and the perpendicular neck's layer strength need separate
checks; one-piece construction does not itself establish printed strength.

**Count change:** six purchased pieces and one fabricated closure removed.

## Make the structural thigh carry both motor interfaces

Replace the separate hip-output hub, knee-stator plate and three long tie
stacks with a coordinated two-piece structural thigh. The primary carrier
contains the full hip-output flange, the motor cradle and the knee support.
The second structural shell closes the section and completes the knee-stator
mounting face. Preserve the two existing thigh clamp stacks, including their
metal compression tubes and large washers.

The side-opening primary cradle carries five knee-stator screws; four long
stator screws pass through the secondary structural shell. The open stator
sector passes the motor's protruding output pilot during insertion. Both motor
interfaces connect to broad structural walls without a separate mounting tab.

Install the primary carrier's hip-output screws before inserting the knee
motor sideways. Install the five short stator screws and rotating crank before
closing the shell and installing the four long stator screws. Preserve positive
locating surfaces between the halves so the two closure screws do not act as
alignment dowels. Their
compression lands and spreaders remain in the count.

The primary carrier can include the stationary knee clevis while retaining the
existing plain axle, spacer and service sequence. Do not count a stepped-axle
merge until its insertion and bearing removal paths are demonstrated. The
current shin split is fore/aft on X=0; its Y-axis pivot cannot replace a shin
closure screw. Both shin clamp stacks remain.

Each new thigh piece must present open pockets to its machining setup. Motor
face holes remain accessible from their axial directions. Focused native motor
insertion, connector, driver, shell-closure and crank checks cover the front-left
fit assembly. The socket-head revision adds 78 native interface checks,
including full washer support and a 0.6 mm nominal knee screw/crank gap. These
checks do not establish physical fits, strength or continuous loaded motion.

**Count change:** three long screws, three nuts, six tubes and two separate
motor-interface parts removed. The two structural thigh pieces remain. The
new secondary uses four long factory stator screws in the full pattern, with
four counted compression tubes and washers. The reduced pattern has three
active long positions. These additions are included in the table; the earlier
20-piece idealized fabricated budget does not describe this printed variant.

An all-printed fit prototype can represent these integrated pieces. Powered
variants need a qualified motor-preload path. If two separate metal face
spreaders prove necessary, count them: the reduced-pattern fabricated total
becomes 25 rather than 23. A metal structural carrier is another material variant, not an
unreported insert. Broad ribs and continuous walls must replace the tie stack's
load path; thin printed bosses are insufficient evidence.

## Qualify reduced motor patterns independently

The manufacturer drawing provides nine M3 holes on a 73 mm pitch circle and
six M4 holes on a 24 mm pitch circle. The reviewed manual warns against excessive
penetration but does not establish a minimum number of mounting screws.
No reduced-pattern approval was found.
[RS02 manual](../proposals/sculpted/model/references/rs02-manual.pdf).

Retain every factory hole in the native design. Investigate six stator screws
per actuator and three roll/knee output screws as a distinct qualification step.
Keep all six hip-output screws because that joint also carries off-axis body
loads. A
threefold-symmetric six-hole stator subset uses pairs at 0°/40°, 120°/160° and
240°/280°, shifted by the interface's clock angle. The output subset uses
0°, 120° and 240°. This makes 30 motor screws, plus seven other screws or pins.
Reducing the hip output to three screws is the more aggressive 34-fastener,
62-hardware-piece option. It needs separate tension, prying and thread-pullout
qualification. Three stator screws would reduce the total further to 25, but
is a research option rather than the recommended first reduction.

For one explicit screen, assume 16 kg all-up mass, 3g vertical acceleration,
single-leg support and zero hip roll. A native-model foot offset of 67 mm along
Y gives 470.88 N × 0.067 m = 31.55 N·m of hip-output bending. The rigid-group
upper bound is 1,753 N incremental tension with three M4 screws versus 876 N
with six. These values exclude preload, prying and direct forces. The assumed
pose does not bound falls or other roll angles and is not a capacity proof.

Torque alone is insufficient to select either pattern:

| Interface | Screws | Torque-only shear per screw at 17 N·m | Tension increment from an illustrative 20 N·m bending moment |
|---|---:|---:|---:|
| Stator, radius 36.5 mm | 9 | 51.8 N | 121.8 N |
| Stator, radius 36.5 mm | 6 | 77.6 N | 182.6 N |
| Stator, radius 36.5 mm | 3 | 155.3 N | 365.3 N |
| Output, radius 12 mm | 6 | 236.1 N | 555.6 N |
| Output, radius 12 mm | 3 | 472.2 N | 1,111.1 N |

The torque-only screen uses T/(nr). The rigid symmetric group bending screen
uses 2M/(nr), where n is screw count, r is circle radius, T is applied torque
and M is external bending moment. It omits prying, direct force, flange
compliance and joint separation. A 50 N·m sensitivity case raises the three-bolt
output tension increment to 2,778 N. These example moments do not bound a fall.

The existing 28 mm crank also produces approximately 1.03 kN rod force at
17 N·m in the least favorable screened pose. The integrated faces must carry
that force as well as torque. Check case-thread pullout, real screw grade,
slip, preload retention and printed or metal bearing stress. NASA's fastener
manual treats eccentric fastener groups and combined tension/shear explicitly;
its method does not replace an actual joint model.
[NASA Fastener Design Manual](https://ntrs.nasa.gov/api/citations/19900009424/downloads/19900009424.pdf).

## Use tapped receiving bosses for the later metal variant

For machined metal structural halves, the four thigh/shin closure locations can
use integral metal compression lands and tapped receiving bosses. Keep a broad
ordinary washer under each screw head. This removes four nuts, four opposite
washers and four separate tube limiters without adding parts. Integral metal
long-screw columns can replace the three additional tubes. Keeping their three
head-spreader washers gives 37 threaded fasteners, 57 purchased hardware pieces
and 16 fabricated pieces per leg with the first reduced motor pattern.

Do not apply that count to printed halves with four replacement inserts.
Those inserts are four physical pieces and printed compression still needs a
load path. Preserve open tool access and avoid captive roofed nut pockets,
blind extraction grooves or special low-profile screws.
