# One-limb fit prototype

The prototype uses three RS02 actuators, two 6810-2RS hip bearings and two
6001-2RS knee bearings. Its custom parts can be printed for an unpowered bench
assembly. Operating bearing fits, fastener preload and printed strength are not
qualified. Stationary contacts with the robot chassis still need correction.

The limb uses M3, M4 and M5 threads. M3 serves the motor stators and small
retainers. M4 serves the motor outputs, cup closure and structural-shell clamps.
M5 serves the two shoulder-screw pivots and the knee retaining bolt. The knee
retains a 12 mm steel bearing journal; the M5 bolt does not replace that journal.

## Print small fit rings before the complete limb

Download the [prototype package](.)
or inspect the [current limb in the browser](http://127.0.0.1:8770/viewer/?design=v14&focus=FL).
The package manifest records its source model hash and part orientations.

Start with the individual 65.15 mm bearing-seat, 49.90 mm journal and 28.10 mm
knee-seat coupons. A coupon is a small test print reproducing a dimensional
interface. Print an adjacent size if the first size does not fit appropriately.
The optional nine-object coupon plate contains all sizes in one unsliced 3MF.

Use the same material, nozzle and print settings intended for the corresponding
full part. Record the actual bearing, selected coupon and measured result.
The journal coupons lie horizontally to match the cup's perpendicular journal.
Use the intended support profile and inspect the supported underside; a vertical
shaft coupon would not reproduce its support scars. Check the full printed
journal again because the small coupon does not reproduce its entire structure.
The modeled diameters include trial print allowances; they are not finished CNC
fit specifications. A loose printed journal is not acceptable evidence of loaded
bearing stiffness.

## Prepare the larger parts in the slicer

The package contains sixteen oriented part geometries, individual generic 3MF
files and matching STEP references. The 3MF files contain geometry in millimetres;
they contain no machine profile, supports or G-code.

| Parts | Starting orientation | Preparation needed |
| --- | --- | --- |
| Inner thigh and shin | Open mating cavity upward; limb length near the bed plane | Inspect bearing seats, washer floors and bridges. Keep support removable. |
| Outer thigh and shin | Open mating cavity upward; curved exterior toward the bed | Review exterior bed contact and add accessible exterior support where necessary. |
| Main motor cup | Motor rear face toward the bed; open motor cavity upward | Support the horizontal roll journal and inspect nut-access overhangs. Remove support through the open cup. |
| Removable motor flange | Broad mounting face parallel to the bed | Inspect the locating-pad recesses and countersinks. |
| Fixed bearing housing, removable rear plate and front retainer | Bearing axis vertical | Keep support and seam defects away from bearing seats and race-contact lands. |
| Backplate, spacers, hub, stator plate, crank and pushrod | Broad face toward the bed | These printed parts are fit surrogates for the intended metal parts; thin spacers require particular care. |

All oriented bounding boxes fit within a 305 × 300 × 305 mm working envelope,
leaving nominal margins inside the project's H2D single-nozzle volume. Bounding
box fit and closed meshes do not establish acceptable toolpaths. Inspect each
layer preview before printing.

Keep the assembly supported on the bench. Printed precision spacers, bearing
supports and drive components have not been qualified to carry the robot.

## Assemble the hip cartridge before attaching the thigh

1. Seat the three retainer nuts from the housing's open rear. Place the inner
   backplate through the motor-side opening. Align its six output holes before
   attaching the fixed housing to the roll motor.
2. Insert the rear bearing, separate inner and outer spacers, and front bearing
   through the open output side. Keep force on the ring being fitted.
3. Install the outer-race retainer. Inner and outer race stacks have separate
   locating faces. Measure the supplied bearing widths and spacer lengths;
   tightening screws does not establish a controlled bearing preload.
4. Insert the main cup's journal and install the six recessed roll-output screws.
   The perpendicular hip motor is absent during this operation so a driver can
   reach the screws through the open cup.
5. Slide the hip motor and its bare sockets axially into the open cup. Install
   the removable stator flange and its three locating pads, washers and M4 joints.
6. Fit the hip output hub and thigh module. Install the knee axle, bearings,
   pushrod bushings and shoulder screws before closing the structural halves.

The pushrod pivot nuts must be installed before their containing structures are
closed. The knee axle uses its metal sleeve and two large M5 washers to provide
defined bearing footprints at the thigh faces. Sleeve length, printed floor
spacing and washer tolerances still require measurement before setting preload.

The lower inboard flange nut has a side-entry wrench route. A generic 7 mm
open-ended wrench with a 16 mm-wide, 3.8 mm-thick head clears when its handle
points about 15° downward from the lug's radial direction. Position it about
8 mm outside the nut, enter axially through the side opening, then slide inward.
Keep about 1 mm before the jaw opening bottoms against the cup. The nut flats
remain within the jaws while the front screw is turned. This is a checked tool
envelope; larger wrench heads have not been qualified.

For bearing removal, detach the roll actuator and remove the rear stator plate
and front retainer. The housing then has a through bore exposing the outer-race
diameter. A ring driver can push the outer-race stack without using the inner
rings as a force path. Select its contact band for the actual bearing rather
than pressing on the seals.

## Obtain hardware for one limb

Counts below are installed quantities without spares. Multiply by four for the
complete quadruped. The ordinary fasteners use standard metric coarse threads.

| Hardware | One limb | Purchase status |
| --- | ---: | --- |
| 6001-2RS bearing, 12 × 28 × 8 mm | 2 | Dimensional family selected. |
| 6810-2RS bearing, 50 × 65 × 7 mm | 2 | Dimensional family selected; ratings depend on the actual manufacturer. |
| Igus GFM-0608-04 flanged bushing | 4 | Manufacturer dimensions match the model. |
| M4 × 25 button-head screw | 4 | Shell clamps; ordinary ISO 7380 geometry. |
| M4 hex nut | 7 | Four shell clamps and three removable-flange joints. |
| M4 large washer, 12 × 4.3 × 1 mm | 8 | Shell clamps; large-series washer specification. |
| M4 × 16 button-head screw | 3 | Removable flange; nominal assembly geometry checked. |
| M4 ordinary washer, 9 × 4.3 × 0.8 mm | 3 | Removable flange. |
| M5 × 55 button-head screw | 1 | Knee retention candidate; supplier grade and actual head need confirmation. |
| M5 hex nut, 8 mm across flats | 3 | Two pushrod pivots and one knee retainer. |
| M5 large washer, 15 × 5.3 × 1.2 mm | 2 | Knee retention; thickness is 1.2 mm nominal, not 1 mm. |
| M3 × 25 button-head screw and M3 hex nut | 3 each | Hip bearing retainer. |
| M3 × 30 button-head screw | 9 | Roll stator-to-housing stack; confirm actuator thread depth before ordering the final set. |
| M4 × 25 flat-head screw | 6 | Recessed roll-output coupling; length includes the head. Confirm actuator thread depth. |
| M3 × 8 flat-head screw | 9 | Hip stator closure candidate; confirm supplied head geometry and actuator thread depth. |
| Shoulder screw, 6 mm shoulder diameter × 20 mm shoulder length, M5 thread | 2 | Supplier drawing remains to be matched. Current geometry needs the threaded tail shortened to 7 mm. |

The knee-motor stator screws, hip-output screws, input-crank screws and three
long motor-pod ties still need final length specifications. A complete kit cannot
be ordered solely from this table. The long ties currently have a nominal 58 mm
under-head length; a standard-length solution must be checked before procurement.

The reference countersunk screws are displayed before final seating. The measured
reference profiles draw down approximately 0.2 mm into their seats, changing
thread engagement by the same amount. DIN 7991 and ISO 10642 heads differ;
freeze the supplied standard and dimensions before finalizing screw lengths.
[Manufacturer countersunk-screw drawing](https://eshop.boellhoff.de/out/media/pdf/ISO_10642_Stahl_10.9___en.pdf).

The [Igus US bushing listing](https://www.igus.com/iglide-ibh/flange-bearings/product-details/iglide-g-m?artnr=GFM-0608-04)
specifies a 6 mm bore, 8 mm outside diameter, 12 mm flange, 4 mm overall length
and 1 mm flange thickness. Ordinary screws and nuts can come from Amazon.com
when dimensions, standard and grade match. Use a US precision supplier for
ground shoulders and bearing-related stock.

[ASMC's large-washer drawing](https://www.asmc.net/product_images/ASMC_reference_full/metdin9021.pdf)
provides the catalog dimensions. M5 large-washer thickness spans 1.1–1.4 mm in the
ASMC drawing; the nominal knee model uses 1.2 mm. Catalog dimensions do not
establish stock or delivery. No checkout availability has been verified.

The following metal pieces also need a cut-stock or machining plan:

- Four shell compression sleeves: 8 mm OD × 4.3 mm ID × 18 mm nominal length.
- Six motor-pod tube segments: three 41 mm and three 6 mm lengths, 5 mm OD
  and 3.4 mm ID.
- One knee axle: 12 mm OD × 5.5 mm bore × 44.6 mm nominal length.
- One knee inner-race spacer: the current 16 mm-length reference.
- Two hip bearing spacers and one inner backplate, with ring-specific contact
  lands and measured axial stacks.
- The motor hubs/plates, input crank and 170 mm-center pushrod for an operating
  metal transmission.

## Interpret the checks before powered operation

The geometry reports distinguish bench assembly, rigid motion, knee retention,
foot folding and stationary body contacts. Recorded contacts between the new
fixed hip module and the chassis are unresolved. Whole-robot installation needs
those contacts corrected before release.

Loaded strength, seam slip, bearing endplay, polymer creep, motor temperature
and dynamic impacts require physical tests. The complete robot remains above
the approximately 10 kg target. Native Fusion conversion continues separately;
these generated STEP references are not editable native Fusion feature models.
