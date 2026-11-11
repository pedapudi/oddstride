# Paired-bearing motor assembly: manufacturing and assembly review

The paired-bearing prototype has a demonstrated motor installation route,
ordinary-wrench access and outer-race extraction access. Independent targeted
checks pass on the frozen geometry under the assembly conditions below.
These results support an unpowered fit print; they do not qualify loaded operation.

This review uses generated model SHA-256
`b968fea927022ba467e05eb52ab602a680e14fd7295c263eefcb95a58a90cdc6`.
It covers exported front and rear left-side motor carriers, housings, retainers,
spacers and reference hardware. Independent checks use preserved STEP files in
[`analysis/dfma/paired-service-input/`](../analysis/dfma/paired-service-input/).
The earlier [whole-robot manufacturing review](dfma-review.md) remains relevant
to unchanged body, battery, equipment and limb interfaces.

This is an unpowered fit prototype. The modeled bearing clearances, material
allocation and nominal contacts do not qualify a loaded printed robot or CNC
production assembly. Native Fusion publication is a separate migration process.

## Bearing and fastening contacts establish a nominal load path

The earlier paired-bearing model tested 46 axial contact interfaces across the
front and rear assemblies, all with positive nominal contact. The current check
also verifies the new rear plate's contacts and the retained front/inner abutments.
The probes move a reference part 0.02 mm toward its receiving face and divide
the intersecting volume by that travel to estimate the contact footprint.

| Interface | Footprint per interface | Interpretation |
| --- | --- | --- |
| Rear outer bearing to housing shoulder | 201.062 mm² | Rear outer-ring axial abutment exists. |
| Front outer bearing to removable retainer | 201.062 mm² | Front outer-ring axial abutment exists. |
| Rear inner bearing to motor-side backplate | 201.258 mm² | Rear inner-ring axial abutment exists. |
| Front inner bearing to carrier shoulder | 201.258 mm² | Front inner-ring abutment uses the smaller shoulder rather than the old broad flange. |
| Outer spacer to either bearing | 190.860 mm² | A separate outer-ring spacing path exists. |
| Inner spacer to either bearing | 193.396 mm² | A separate inner-ring spacing path exists. |
| M3 retainer head to retainer | 15.551 mm² | The screw head bears on a real land. |
| M3 retainer nut to housing | 17.118 mm² | The rear nut bears on its pocket floor. |
| M4 closure washer to closure | 48.412 mm² | The washer distributes clamp load into the removable flange. |
| M4 closure head to washer | 30.843 mm² | The head overlaps its washer. |
| M4 closure nut to cup | 27.230 mm² | The nut bears on the main cup lug. |

Bearing references are simple annuli. These contact results do not validate
the selected commercial bearing's separate race faces, recessed seals or internal
clearance. Check those details against the purchased product before machining
the shoulders. Pressure, deflection, preload and fastener strength were not modeled.

The outer-ring path runs from the removable rear shoulder through both outer rings and
their spacer to the front retainer. The inner-ring path runs from the motor-side
backplate through both inner rings and their spacer to the carrier shoulder.
Output screws also clamp the carrier journal against the backplate, so screw
torque alone does not establish bearing preload.

Two actual bearing widths can differ from their nominal 7 mm values. Measured
spacer lengths and a specified endplay or preload procedure remain necessary.
The nominal 65.15 mm housing seat and 49.90 mm journal are fit-print allowances,
not finished CNC fits. A coupon checks dimensional fit; it does not verify
bearing support stiffness or printed structural strength.

## Motor insertion and closure removal now have straight paths

The cup and removable stator closure form separate structural parts. The bare
motor proxy clears the open cup at eight sampled axial positions from its seated
position to 65 mm withdrawal. The closure clears the cup at six sampled positions
from seated to 20 mm withdrawal. Both front and rear assemblies pass.

Rear retainer nuts also clear their housing pockets at the sampled axial positions.
The open nut pockets therefore provide a nominal installation path. Actual nut
dimensions, print compensation and removal grip still need physical checks.

The rear inner backplate must enter before the bearing pack closes the route.
Its 52.5 mm outside diameter cannot pass through installed 50 mm bearing bores.
Assemble the roll motor and bearing cartridge on a bench, preserving the plate's
clock while the carrier and output screws are installed.

Install the perpendicular motor only after tightening the roll-output screws
through the empty cup. Then attach its stator closure, secure the closure lugs,
connect the cables and install the output hub and thigh. This sequence remains
subject to the corrected wrench route and actual purchased motor hardware.

## Wrench access uses the through-wall slot and a short final approach

The slots extend inward to a 37 mm radius, across the full cup wall. Their
22 mm tangential width and 5.5 mm axial height provide an open wrench route
while preserving the nut-bearing floor. A generic 7 mm wrench with a 16 mm
head and 3.8 mm thickness clears the actual exported geometry.

The lower lug beside the fixed bearing support also needs an angled handle.
Use the ordinary 15° jaw-to-handle relationship with the handle pointing farther
downward, away from that support. For the front 215° lug this is a +15° handle
offset; for the rear 325° lug it is −15° in the local X/Z convention.

A long radial approach from 15–25 mm away intersects the fixed housing or
retainer. A shorter route avoids that obstruction:

1. Hold the wrench 8 mm radially outside the nut.
2. Enter axially from behind the cup into the side-slot plane.
3. Slide 7 mm radially inward, leaving the wrench head 1 mm outward from center.
4. Hold the nut stationary and turn the accessible bolt from the front.

The nut flats remain fully within the jaw at that 1 mm offset. Fully centering
the circular proxy head causes a small corner intersection with the preserved
web; pushing the tool against the web is unnecessary for holding the nut.

The current audit tests the axial entry and short seating motion against the
cup, motor, housing, rear plate, retainer, closure and all modeled roll-module
steel hardware. Every tested pairing clears. The handle is 100 mm long and
the wrench's front face remains 0.3 mm from the nut-bearing floor.
Whole-robot hand space was not checked; use bench assembly for the motor cartridge.

These are generic tool envelopes. A larger 17.5 mm circular-head proxy slightly
enters the motor reference, so the design should not promise access for every
7 mm wrench. Verify an ordinary purchased tool's actual jaw outline and thickness;
do not require a custom-ground wrench.

## CNC setups are plausible but not fully qualified

The following setup directions use the front-left local axes. Reverse X for
mirrored rear bearing components. They are proposed machining plans, not verified
CAM toolpaths or a declaration that every feature is undercut-free.

| Part | Proposed straight-tool setups | Remaining manufacturing issue |
| --- | --- | --- |
| Fixed bearing housing | Through-bore and face operations along X; rear hex pockets from −X; chassis-ear holes along Y. | Check thin ligaments beside nut pockets, drill breakout, seat coaxiality and workholding. |
| Removable rear stator plate | Opposed X faces for motor aperture, raised collar and through holes. | Preserve the 1 mm radial stop collar and verify race-face contact before machining. |
| Outer retainer | Opposed X faces for profiling and through holes. | Support the 2 mm plate during cutting; retain broad screw lugs. |
| Main cup and orthogonal journal | Open motor cavity from +Y; journal and output-screw features along X through the open tool window; radial wrench slots from their open sides. | Verify full cutter/holder access to countersinks and the web; the corrected slot must retain its bearing lands. |
| Removable stator closure | Opposed Y faces for plate, countersinks, through holes and open registration pockets. | Preserve motor seating and countersink thickness. |
| Inner backplate | Opposed X faces and six through holes; flat stock can avoid heavy pocketing. | Control flatness and bearing-contact diameter. |
| Inner and outer spacers | Open axial ring features, accessible from either X face. | Thin walls need supported machining, deburring and measured lengths. |

The new housing's through bore and rear plate's exposed collar have conventional
axial access. The project prohibits undercuts. A CAD interference result does not establish
tool access. A complete setup sheet still needs cutter diameter, flute length,
holder envelope and fixture support for the internal carrier features.

For fit printing, a housing with its X bearing axis vertical is a reasonable
starting orientation. Print the rear plate flat with its collar upward.
The main cup/journal has perpendicular functional axes, so it needs a sliced
orientation study and accessible supports. A rear-face-down cup leaves the
journal horizontal; a vertical shaft coupon does not reproduce its support scars
or roundness. Match coupons to the actual orientation and profile.

A metal shape printed unchanged is not a qualified structural polymer carrier.

## The removable rear plate opens an outer-race extraction route

The stationary housing splits at X−74.5 into a through-bore body and a removable
rear stator plate. The existing nine M3 motor screws clamp both parts, so the
split adds no fasteners. The plate's 65 mm collar enters the 65.15 mm body bore
and preserves the complete rear outer-ring abutment.

With motor, carrier, backplate and end retainers released, a straight 64.8 mm
outside-diameter, 63 mm bore press sleeve clears the full housing. Eight sampled
push-pin directions also clear. Rear-plate withdrawal clears at every tested
position, and its seated register does not intersect the housing.

The rear plate has 901.255 mm² of nominal face contact with the main housing.
Its collar has a 1 mm radial wall and 3 mm projection, with 201.062 mm² of
nominal bearing contact. That is a functional bearing stop, not a qualified printed
structural wall. The press sleeve is a reference tool envelope; confirm it contacts
the purchased bearing's outer race rather than its seal before applying force.

The motor cartridge should be removed from the robot for this service operation.
No whole-body rear motor withdrawal path was certified by this review.

## Finish purchased hardware dimensions before final torque and engagement claims

The corrected knee hardware uses nominal 1.2 mm M5 large washers. The standard
US catalog drawing lists 1.1–1.4 mm thickness, so the clamp and projection stack
must retain that variation. [DIN 9021 dimensions](https://www.asmc.net/product_images/ASMC_reference_full/metdin9021.pdf).

The displayed flat-head output and stator screws need about 0.20 mm axial
drawdown to contact their conical seats. Exact probes find no contact at
0.19 mm and contact at 0.21 mm. This is a seated-position refinement rather
than a trapping defect; include it in thread engagement and tip-clearance calculations.

Select the actual countersunk screw standard and head interval. DIN 7991 and
ISO 10642 are not dimensionally identical at every size. Verify motor blind-hole
depth and the selected screw's seated position before prescribing tightening torque.
[Manufacturer ISO drawing](https://eshop.boellhoff.de/out/media/pdf/ISO_10642_Stahl_10.9___en.pdf).

The [current independent check](../analysis/dfma/paired-service-delta.json) records
2,886 passing targeted contact, access and service checks on the stated model hash.
The [earlier contact measurements](../analysis/dfma/paired-prototype-review.json)
and [countersink-seat check](../analysis/dfma/paired-countersink-seating.json) retain
their original model hash; they do not certify a different revision.
