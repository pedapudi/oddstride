# Manufacturing and assembly review

## Detached motor complex passes nominal static review

The corrected native motor-complex assembly has no unresolved nominal material
interference at its exported bench pose. It contains thirteen custom parts,
eight cut-stock bodies and one hundred purchased references. The saved native
checkpoint is Leg24. Its scope is supported, unpowered fit and assembly.

The independent screen covers all 7,260 possible pairs: 6,787 disjoint bounding
boxes and 473 exact-check candidates. Forty-five measured motor-thread reference
crossings and twelve connected protective-boot envelopes are explicitly accepted.
A failed external Boolean at the touching thigh split remains recorded and is
resolved by targeted native solid interference and bidirectional differences.
[Static review and exact evidence](../analysis/dfma/knee-stator-seats/static-screen-review.md).

Recessed ordinary closure screws eliminate the rotating tie/head contact.
A shallow native hub relief eliminates the knee motor's rear-case contact while
preserving every compression-tube bearing footprint. Physical fits, tolerances,
preload, printed strength, CNC toolpaths and loaded motion remain unqualified.
[Native closure comparison](../analysis/dfma/knee-stator-seats/native-closure-review.md),
[native hub measurements](../analysis/dfma/knee-stator-seats/native-hub-relief-validation.json).

## Earlier whole-robot snapshot retains qualification work

The detailed findings below describe the earlier hashed whole-robot snapshot.
They preserve its measured defects and outstanding qualification tasks; they do
not override the corrected detached motor-complex evidence above.

The [paired-bearing assembly follow-up](paired-bearing-prototype-dfma.md) covers
the newer motor carrier, removable stator closure and bearing retention.
It demonstrates motor insertion, nominal axial contacts, an ordinary-wrench
approach and outer-race extraction through a removable rear stator plate.

The quadruped is suitable for further fit prototypes, but the reviewed model is
not ready for loaded operation or a complete CNC order. The original shell-clamp
stack had a verified bearing-contact defect. A corrected washer-seat candidate
establishes nominal contact, with clamp tolerances and loaded behavior still
unqualified. CNC cutter access also remains unresolved at several internal features.
The motor carrier in that earlier snapshot lacked a demonstrated insertion
route; the later split cup and removable closure resolve that fit-assembly issue.

The design uses twelve RS02 actuators and a 1 kg additional payload target.
Its estimated robot mass is about 13.3 kg before that payload, above the 10 kg
target. Batteries and equipment still use assumed envelopes and masses.

This review covers the closed-thigh candidate in
`proposals/sculpted/model/output/closed-thigh-work/model.json`, with SHA-256
`beeac749ee36ea254189f884d8be080e354d245108a6cbd2c7506d8f2f7c3dc8`.
It retains 170 mm thighs, 28 mm cranks and the existing boot and joint locations.
The native Fusion assembly is a separate migration baseline; its earlier audit
results do not qualify this candidate.

The intended reader is the builder or machinist preparing parts and assembly
instructions. DFMA means design for manufacture and assembly. Findings below
separate measured geometry, missing design information and qualification work.
No physical prints, CAM toolpaths, load tests or inventory checks were performed.

The two-piece limb segments, independent equipment services and complete knee
bearing seats are useful manufacturing decisions. The closed thigh also clears
the modeled boot: exact-solid samples give a 2.453 mm minimum gap, with a
1.705 mm conservative bound between samples over the stated knee range.
That result applies to the modeled rigid boot, before manufacturing variation
or loaded deflection. [Foot-clearance evidence](../proposals/sculpted/model/output/closed-thigh-work/foot-clearance.json).

## Correct the structural shell clamps before applying load

**Blocker for printed and metal structural halves; verified geometry defect.**
Each leg has two thigh clamps and two shin clamps. The modeled screw heads are
7.6 mm in diameter. The metal compression sleeves are 8 mm in diameter and sit
in 8.2 mm bores. The M4 nuts have 7 mm flats and an 8.083 mm maximum corner
diameter. Both the head and the nut fit inside the receiving bore.

Exact-solid probes moved each head 0.1 mm inward against its receiving half and
each nut 0.1 mm inward against the other half. All eight probes across the four
clamps intersected zero receiving plastic volume. Tightening this nominal stack
therefore clamps the metal sleeve without establishing axial retention of the
structural shells. Clear interference checks do not demonstrate a usable clamp.

Use an accessible metal bearing footprint that overlaps the receiving shell,
with a controlled sleeve-to-host length relationship. A standard large M4 washer
is a practical candidate. Preserve a complete supporting land underneath it.
Do not substitute more tightening torque or an insert without resolving the
load path. SPIROL requires the head or washer footprint to extend beyond the
compression limiter and contact the host. Its guidance also addresses limiter
length and host compression; those values still need calibration for these
printed parts. [Compression-limiter guidance](https://www.spirol.com/assets/files/cmpl-compression-limiter-design-guide-us.pdf).

The proposed 12 mm outside-diameter, 4.3 mm bore, 1 mm thick M4 washer is a
conventional size. ASMC lists 11.57–12.00 mm outside diameter and 0.90–1.10 mm
thickness. Albany County Fasteners lists the same nominal A2 washer. These are
verified catalog dimensions. Inventory and delivery remain unverified.
[ASMC drawing](https://www.asmc.net/product_images/ASMC_reference_full/metdin9021.pdf),
[US supplier dimensions](https://www.albanycountyfasteners.com/fender-washers-a2-ss-m4-x-12m-43-id-x-120-od-x-10-thick-5670012/).

A 12 mm washer has 60.29 mm² of nominal bearing area outside an 8.2 mm bore.
At the minimum catalog outside diameter, that annulus is 52.33 mm². The rear
thigh location at X−36/Z−66 has slightly truncated lands: 59.46 and 52.17 mm².
Its enlarged access bore would also break out through the nearby outline.
The other thigh clamp and both shin locations have complete sampled material
around a 6.3 mm access radius.

Move the rear clamp or broaden its supporting outline before enlarging that
counterbore. An inward X move can enter the pushrod corridor, so the move must
be checked against the rod throughout its travel. The source boss is clipped
by the thigh envelope; its nominal 8.8 mm radius does not guarantee a complete
2.6 mm wall around a 6.2 mm counterbore.

The corrected washer-seat candidate has SHA-256
`5fbedd560af0f5710b651ee88808d09b24277987ceccc2c12e9ccd7b6825e873`.
Independent exact-solid probes establish contact on every canonical receiving
half: 60.287 mm² beneath each thigh washer and 61.567 mm² beneath each shin
washer. Screw heads contact 30.843 mm² of washer face; nuts contact 27.913 mm².
The shin's receiving bore is effectively 8.1 mm, compared with the thigh's 8.2 mm.

The widened rear thigh also retains complete sampled material at radii 6.3,
7.5 and 8.7 mm around the 6.2 mm access bore. The shin retains the complete
7.5 mm ring, but the 8.7 mm ring crosses the exterior. The shin's access rim
is therefore thinner; do not describe all counterbores as having 2.6 mm walls.

These wall samples use 5° increments at local inner Y56.5 and outer Y77.5.
They establish sampled geometry, not a minimum wall throughout the entire depth.
The corrected stack still needs physical sleeve-length, washer-thickness and
host-compression control. Preload, creep, joint slip, tool reach and loaded
strength remain unqualified. [Corrected contact evidence](../analysis/dfma/corrected-clamp-contact.json).

## Open the motor cup before installing the hip motor

**Assembly release blocker; verified straight-path interference.**

The default metal motor carrier combines its rear cup wall and front stator
flange in one solid. The motor body is 78.5 mm in diameter; the front aperture
is only 54 mm and the rear center opening is 24 mm. The motor fits in the
closed cavity but has no demonstrated route into it.

Independent checks used both current canonical carrier STEPs from the corrected
washer-seat candidate. Both are valid single solids. With all surrounding parts
and fasteners absent, all six straight withdrawal directions encounter material.
Forward axial motion intersects the front flange by 0.25 mm travel; rearward
motion intersects the rear wall by 1.1 mm. Lateral directions also encounter
material within 1–2.5 mm.

This checks straight paths and does not exhaust every tilted trajectory. With
only 2.25 mm nominal radial body clearance inside the cup, a complex tilted
installation should not be assumed feasible. A clear assembled interference
result does not establish an assembly sequence.

The existing optional printed split leaves both closures in its flange/cup part.
Reconstructing that split from its source also blocks axial and lateral motor
withdrawal. Its separate trunnion helps print orientation but does not resolve
this installation problem.

Separate the main cup/elbow from a removable front stator flange. Insert the
motor axially into the open cup, attach the flange to the motor, then secure
the flange to a broad registered cup interface. Use ordinary accessible screws
and preserve a straight tool path to every recess and retaining feature.

Place screw bosses outside the cylindrical motor envelope or entirely ahead
of its case end. A nominal boss centered just outside the case can still
intersect it when its full wall thickness is included. Verify screw insertion,
motor removal, connector routing and flange load transfer on the proposed split.
[Frozen carrier and service-path evidence](../analysis/dfma/hip-motor-service.json).

## Resolve CNC access with actual cutter and fixture setups

**CNC release blocker; standard-cutter reach remains unverified.**

The current stator clearance is a lobed recess at local Y50.3–53.7, behind smaller
case and crank openings. A finite 3 mm straight-cylinder probe from selected
lobe voids found no clear approach in eight tested directions for the outer
thigh's 90° and 330° lobes. The 210° lobe had a clear −Y corridor. These samples
do not test every possible angle or establish feasible flute and holder reach.

Document a standard end-mill setup for the complete recess, including its
remaining ledges. If no setup works, move the pocket boundary to an exposed
structural split or revise the plate support. Removing a support ledge solely
to obtain tool access requires a new load-path review.

The battery cassette also needs a setup study. Its internal guide windows lie
inside the closed outer walls and beneath upper gussets. Open top-loading nut
pockets do not prove access to these separate windows. Check both the printed
support-removal route and the CNC tool/holder route before ordering it.

The knee bearing shoulders have a plausible conventional route. Machine the
inner seat from its outer Y51 side toward +Y and the outer seat from Y85 toward
−Y. Machine the open structural cavities from the split faces. Opposite-face
setups can preserve the full backup annuli without a trapped cutter path.
These directions still require a fixture and holder check.

Project rules prohibit undercuts, including in the printed prototype. Special
undercut cutters do not satisfy that rule. Rounded cavities and valid solids
alone do not establish machining access. Protolabs identifies inaccessible
internal features, undercuts and deep galleries as machining constraints.
[Machining guidance](https://www.protolabs.com/resources/design-for-machining-toolkit/).

## Keep fit parameters separate from manufacturing compensation

**Major issue for both processes; nominal geometry exists but manufactured fits
remain unqualified.**

The knee uses nominal 12 × 28 × 8 mm bearings, matching the common 6001 size.
The model has 28 mm seats and a 12 mm axle, with no physical fit evidence for
the chosen printed material or the finished metal parts. A nominal match does
not establish a press, sliding or removable fit.
[SKF dimensional catalog](https://cdn.skfmediahub.skf.com/api/public/0901d196802809de/pdf_preview_medium/0901d196802809de_pdf_preview_medium.pdf).

Native parameters already distinguish bearing, shaft, hole and pocket allowances.
Finish the drawings with measured supplier intervals and process-specific values.
For printing, use seat, bushing, nut-pocket and clamp coupons from the actual
filament/profile. Keep bearing datums fixed while adjusting local allowances.
For CNC, specify finished dimensions, tolerances and surface requirements;
tool compensation is not a universal offset on the CAD model.

The 2.6 mm extraction holes lie at a 12.7 mm radius, so their outer edges are
tangent to the 28 mm bearing-seat boundary: 12.7 + 1.3 = 14 mm. Avoid relying
on a zero-width tangent edge in the manufacturing model. Use an intentional
finite clearance profile that preserves the required bearing wall and shoulder.
Verify the press tool against the selected bearing's actual outer-race face;
the solid ring envelope does not distinguish that face from seals.

The paired GFM-0608-04 bushings are an obtainable manufacturer specification:
6 mm bore, 8 mm outside diameter, 12 mm flange and 4 mm overall length with a
1 mm flange. Igus specifies a housing fit and notes that the bore changes after
press-fitting. The current envelopes do not simulate that installation.
[Igus US product](https://www.igus.com/iglide-ibh/flange-bearings/product-details/iglide-g-m?artnr=GFM-0608-04).

The roll bearing is a provisional RA5008-size crossed-roller envelope. It is not
an ordinary radial-bearing substitution. Select the actual bearing, retention,
preload and housing tolerances before machining the cartridges. The manufacturer
identifies RA as a thin crossed-roller series; the CAD envelope alone does not
establish a mounting specification. [THK product family](https://www.thk.com/jp/ja/products/cross_roller_ring/cross_roller_ring/ra/ra/).

A separate [hip-roll bearing study](hip-roll-bearing-options.md) compares standard
sealed ball-bearing pairs and their complete packaging allowances. A 6808 pair
at 20 mm center spacing reduces local diameter, while a 6810 pair at 14 mm keeps
the cartridge shorter. The selected next design uses two sealed 6810 bearings
per hip-roll joint at 14 mm spacing. That replacement is being modeled; the
frozen model reviewed here still contains the provisional crossed roller.
The paired architecture needs its own retention, fit and load validation.

## Complete the attachment interfaces before final assembly

**Assembly release blockers; missing design information.**

- **Boot retention:** the boot is a shaped envelope. Its attachment cavity and
  retaining fastener are explicitly unfinished. Define retention, replaceability
  and a repeatable position before relying on its nominal clearance.
- **Lower enclosure and skid:** the lower protective shell lacks a complete
  attachment definition. The skid has no modeled retaining screws or documented
  alternative retention. Provide a serviceable fastening path and retain access
  to the battery cassette.
- **Battery installation:** commercial pack models, adapters, contacts and latch
  retention are unselected. Freeze those interfaces before finishing the cassette
  and trim panels. A pack envelope cannot verify insertion, release-button access
  or shock retention.
- **Sensors and computer:** exact device mounting, standoffs and connector/thermal
  space remain component-specific. The removable deck and sensor hood are useful
  architecture, but the equipment installation is not complete.
- **Wiring:** modeled plugs, boots and withdrawal spaces are provisional. Define
  wire sizes, cable exit directions, bend radii and strain relief. Cover and deck
  wiring must disconnect without removing actuator mounting screws.
- **Motor fasteners:** finalize screw lengths against the actuator's verified
  blind-hole depths and the actual flange stack. The mounting hole pattern alone
  does not establish thread engagement or clearance from bottoming.

The present assembly order should keep four independent service operations:
remove the main cover, remove the electronics deck, remove the sensor hood and
remove the battery cassette. A service screw must not also release a structural
frame joint. The revised separate cover and sensor-root fasteners support this
approach.

## Qualify printed structures with their real joint and thermal conditions

**Loaded-operation blocker; strength has not been established.**

The modeled assembly is a hybrid. Motor rails, cartridges, carriers, hubs,
mounting plates and input cranks are aluminum references. Printed copies of
those geometries require a separate structural qualification.
The older two-piece printed-carrier proposal is not the current assembled route.

The unchanged linkage can produce approximately 1.03 kN rod force at 17 N·m
actuator torque and a 20.14 N·m local mounting moment from its axial offset.
Printed fork ears, bearing seats, bosses and carrier joints therefore need
concentrated-load checks. Doubling an analytical load does not create a verified
safety factor.

The previous slimmer-thigh section screen assumes the two structural halves act
as one section. It does not qualify their connection. Its largest reported local
shear-transfer requirement was 4.79 N/mm, but that screen belongs to an earlier
model hash. Recalculate on the corrected clamp geometry and verify slip, torsion,
creep and bearing alignment with a complete assembled leg.

Keep the long limb axis near the print bed plane. This preserves more of the
longitudinal load path within layers, while fork opening and axial bearing loads
can still act across them. Solid infill does not remove that directional weakness.
Measure temperatures near motor-adjacent polymer and use the actual dry material
and profile for coupons and assembly tests. Prusa's guidance also treats orientation
and process-dependent clearances as part-specific design work.
[Printing guidance](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135?product=core-one).

Use heat-set inserts for reusable cover or equipment threads when their boss
wall, insertion direction and pull-out load are suitable. They do not replace
the compression and shear checks at structural shell joints. SPIROL recommends
sufficient solid material and wall loops around inserts; its examples do not
qualify this robot. [Printed-insert guidance](https://www.spirol.com/resources/white-papers/how-to-select-a-threaded-insert-for-your-3d-printed-assembly/).

## Plan each part family for printing and machining

Directions are local CAD axes for the left-hand part. Reflect Y directions for
right-hand parts. The setup plans below are proposed manufacturing approaches;
they are not verified CAM programs or sliced print jobs. Counts include assembled
left and right variants.

| Part family and quantity | Printed prototype approach | CNC approach and remaining concern |
| --- | --- | --- |
| Inner and outer thigh, four of each | Length near the bed plane; open mating cavity upward where possible. Support the accessible curved exterior. Preserve screw and socket access. | Opposed Y setups plus an explicitly demonstrated motor-pocket setup. Clamp correction and lobe access remain release blockers. |
| Inner and outer shin, four of each | Length in the bed plane; split face upward. This places the Y bearing axis approximately vertical, unlike the retired fore/aft-split print description. Keep support out of seats. | Split-face cavity machining and opposed outer-face bearing operations. Preserve complete support annuli and extraction paths. |
| Orthogonal motor carriers, four | Current aluminum shape is a fit mockup if printed. A two-piece print route would need independent print orientations and a qualified keyed bolted joint. | At least X- and Y-axis interfaces; additional access for side reliefs. Preserve pilot alignment and accessible clamping faces. |
| Roll cartridges, four | Fit mockups only until the actual bearing, retention and material stiffness are selected. | Bore and face operations with controlled bearing fit; finish retention and preload details first. |
| Hip hubs and stator plates, four of each | Prototype geometry only; do not infer metal mounting capacity from a polymer copy. | Axial plate/face work with reverse-side ribs and local pads. Patterned holes are conventional; thin regions need supported workholding. |
| Input cranks and pushrods, four of each | Use shape checks only for the metal transmission route. | Cranks need opposed faces/fork access. The flat 6 mm steel pushrod profile can be cut from plate, then its 8 mm bushing bores finished and edges deburred. |
| Side rails, two | Unloaded frame mockups. Orient for an accessible web and flange; verify supports at perpendicular bosses. | Opposed Y web/interface work and top Z drilling/tapping. Plan multiple machining directions for the integrated bosses. |
| Transverse ties, two | Unloaded fit prototypes. Seat lands must remain flat. | Main folded profile, top countersinks and underside sensor pads on the front tie require staged workholding. Verify purchased screw seating. |
| Lower brace and electronics deck, one each | The 4 mm deck prints broad face down; the metal brace remains a fit mockup if printed. | Flat profiling/drilling is straightforward. The 3 mm aluminum brace's deck threads need a repeated-service torque/engagement specification. |
| Upper cover, one | Roof-down is a candidate with the interior accessible upward. Check curved edge supports and local screw lands in the slicer. | Outer and inner surfacing in supported fixtures, followed by lateral holes. Cosmetic thin-wall machining is a cost risk. |
| Sensor hood and cradle, one each | Keep the cradle's mounting lands flat. Orient the hood to leave support removable through its open underside. Selected sensor fixtures remain unfinished. | Multiple surfacing and hole directions; prove access around the deep curved face and interior bosses. Retained nut pockets require direct insertion and tool access. |
| Battery cassette, one | Open top upward is the starting orientation, but internal guide/gusset supports may be trapped. Review actual support removal before printing. | Demonstrate full guide-window and gusset access with standard cutters and holders; no undercut exception is allowed. |
| Battery trim panels and latches, two of each | Panels can print flat; latch envelopes still need a complete functional design. | Thin panels are better profiled from sheet than pocketed from thick billet. Retention features need a finished design. |
| Belly shell and skid, one each | Open-shell orientation and retention hardware still require definition. | Belly needs supported thin-wall workholding; skid is a flat profile. Neither has a completed attachment release. |
| Knee axles, spacers and compression sleeves | Purchase or machine metal parts; do not replace them with polymer to retain nominal dimensions. | Cut/face and finish appropriate tubing or turned stock. Control length, perpendicular ends and burrs, then inspect fit stacks. |
| Boots and selected sensor/device covers | Boot retention and material are unselected. Equipment envelopes are not manufacturing definitions. | Keep purchased equipment separate; a provisional lidar lid is not an approved custom machined part. |

The H2D's published single-nozzle envelope is 325 × 320 × 325 mm. The current
thigh's approximate 242.5 mm length is not the limiting machine dimension.
Its asymmetric cup, support access and layer direction require more attention
than diagonal bed packing. Dual-nozzle usable volume differs; select the print
mode when generating the plate. [H2D specifications](https://cdn1.bambulab.com/documentation/h2d/en/H2D_Laser_Full_Combo_20250305.pdf).

Regenerate manufacturing files for the released geometry. Earlier thigh 3MF
preparations describe different hashes and do not cover the new wall or clamp
changes. Review support removal, bore compensation, perimeter continuity and
actual toolpaths in the slicer. A clean STL and a fitting bounding box do not
establish a printable structural part.

## Reduce machining effort and assembly handling

**Major cost and serviceability opportunities; not verified strength improvements.**

The side rails occupy a 262 × 15.5 × 54 mm rectangular bounding box but retain
only about 8.9% of that nominal billet volume. The large curved sensor hood
retains about 2.4%. These geometric stock-removal indicators do not estimate
machining time or supplier prices. They explain why an all-metal copy of every printed
shell may be expensive even when its finished mass is small.

Use flat profiling for the brace, deck, skid and pushrod where compatible with
their material. Keep large cosmetic enclosures printed for the first prototype.
If every enclosure must become metal, quote thin-wall fixtures and formed or
near-net alternatives before duplicating the polymer design in billet.

The motor pods contain two cut tube lengths per tie: 41 and 6 mm, giving six
pieces per leg. Assemble these as a bench cartridge and retain their positions
during service. A continuous tube cannot replace both pieces without changing
how the stator plate is clamped between them.

The shoulder screws also require the excess M5 thread to be shortened to 7 mm.
This is an additional cut, deburr and thread-inspection operation. Preserve the
loaded 6 × 20 mm shoulder. Standardize that operation with a stop and gauge;
do not require a special short-head screw as an unverified supply dependency.

Define tightening and locking methods for every structural connection. A captive
hex nut prevents nut rotation during assembly but does not, by itself, prevent
the screw from loosening. Do not select a chemical locking product for polymer
contact without checking compatibility.

The current M3 tie screw envelopes are also approximately 0.071 mm clear of
their countersink surfaces at the displayed positions. A small draw-down can
seat them, but the purchased head profile and seated position must be modeled
before treating this interface as a validated contact. This is separate from
the structural shell clamp defect.

Define the replaceable leg module before checking the under-$100 target.
Retaining the proximal motors, carriers and bearings while replacing printed
shells is a different service operation from replacing the complete limb.
No complete priced BOM, confirmed stock or manufacturing quote supports that
target yet.

## Required evidence before release

1. Corrected clamp geometry with measured washer/seat contact, bolt engagement,
   sleeve stack intervals, driver access and no new motion interference.
2. An open hip-motor installation route with removable stator closure, verified
   screw access and a supported flange load path.
3. A setup sheet for each CNC part, including cutter diameter, effective reach,
   holder clearance and fixturing at every internal feature.
4. Current print plates and layer previews, followed by dimensional coupons for
   bearing seats, bushings, sleeves, nut pockets and mating faces.
5. Completed boot, battery, equipment, lower-cover and skid retention interfaces.
6. Load, temperature, creep and repeated-service tests on the actual assembled
   leg and frame route selected for operation.

Read-only evidence and reproducible measurements are in
[`analysis/dfma/`](../analysis/dfma/). The clamp diagnosis preserves the reviewed
STEP inputs and their hashes. A later geometry correction must receive its own
review status; it does not invalidate the recorded defect in this input model.
