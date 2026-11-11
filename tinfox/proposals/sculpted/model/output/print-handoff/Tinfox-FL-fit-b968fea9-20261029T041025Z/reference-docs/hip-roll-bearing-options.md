# Hip-roll bearing options

The selected design direction replaces the provisional crossed roller with two
sealed 6810 ball bearings per hip-roll joint, at 14 mm center spacing.
The [paired-bearing fit prototype](paired-bearing-prototype-dfma.md) has generated
CAD and independent assembly, wrench-access and bearing-extraction checks.
Eight bearings are required for the robot.
The old crossed-roller geometry remains a dimensional reference.
The [IKO crossed-roller option](#the-iko-crossed-roller-option-is-deferred)
is deferred for a future packaging revision. The current prototype retains the
6810 pair. Its [printed housing limitations](#the-printed-housing-is-a-fit-prototype)
require a separate structural review before loaded use.

The paired 6810 preserves a nominal 50 mm journal and favors a shorter cartridge.
A 6808 pair at 20 mm spacing remains a smaller-diameter alternative if a later
packaging study justifies changing the journal. Neither architecture is qualified
for loaded stairs, self-righting or jumping yet.

The 6808 pair reduces the bearing outside diameter from 66 to 52 mm, but needs
a longer fore/aft cartridge. The 6810 pair preserves a nominal 50 mm journal and
keeps the cartridge shorter.

This study is for the builder choosing the next bearing and housing architecture.
It uses the frozen generated robot reviewed in
[the manufacturing review](dfma-review.md), with model SHA-256
`beeac749ee36ea254189f884d8be080e354d245108a6cbd2c7506d8f2f7c3dc8`.
The alternatives are proposals; this study does not change or validate CAD.

## Bearing diameter and assembly length favor different choices

The frozen reference model has a 50 × 66 × 8 mm crossed-roller bearing envelope.
Its cartridge barrel is 72 mm in diameter and 16.3 mm long. An 82 mm stator
flange increases the full cartridge envelope beyond that barrel diameter.
The modeled journal is 49.9 mm in diameter and 13.3 mm long.

The 0.1 mm difference between nominal bearing bore and modeled journal already
requires a fit decision. A new nominal 50 mm bearing is therefore not a validated
drop-in fit. The crossed-roller envelope also lacks a completed retention and
preload specification.

| Architecture per roll joint | Bearing envelope | Center spacing | Bearing/spacer pack | Estimated cartridge length | Diameter consequence |
| --- | --- | --- | --- | --- | --- |
| Current single crossed roller | 50 × 66 × 8 mm | Internal bearing geometry | 8 mm bearing | 16.3 mm current barrel | 72 mm barrel; 82 mm stator flange |
| Two 6810 sealed ball bearings | 50 × 65 × 7 mm each | 14 mm | 21 mm | About 25 mm | Barrel about 71–72 mm; stator flange still 82 mm |
| Two 6808 sealed ball bearings | 40 × 52 × 7 mm each | 20 mm | 27 mm | About 31 mm | Barrel about 58–60 mm; stator flange still 82 mm |
| Two 6808, shorter prototype | 40 × 52 × 7 mm each | 14 mm | 21 mm | About 25 mm | Same smaller barrel, less moment capacity at a given reaction limit |
| Two 6809, intermediate option | 45 × 58 × 7 mm each | 14 or 20 mm | 21 or 27 mm | About 25 or 31 mm | Barrel about 64–66 mm; revised journal required |

The estimated cartridge lengths allow 2 mm at each end of the bearing pack.
They are layout allowances, not finished retaining-wall dimensions. Retainers,
seal clearance, shoulders, tool access and the motor interface may increase them.
The 25 and 31 mm layouts add approximately 8.7 and 14.7 mm to the existing barrel.

A 21 mm bearing pack also exceeds the current 13.3 mm journal by 7.7 mm.
The 27 mm pack needs 13.7 mm more journal length before any separate end hardware.
Keeping the output face fixed requires that space to move toward the roll motor
or chassis; moving the output face shifts the entire limb fore/aft.

The roll axis runs fore/aft along CAD X. Axial growth need not widen the stance
along Y. A smaller bearing diameter does not directly reduce body width either:
the 78.5 mm motor and 82 mm stator flange remain larger than either ball bearing.
The benefit is local clearance, material reduction and room around the carrier.

The 6808 requires a new 40 mm journal and cartridge. Its smaller journal must
retain the six M4 output holes on their 24 mm bolt circle and the central passage.
The radial ligament beyond an M4 clearance hole becomes approximately 5.8 mm,
before tolerances or fillets. That load path needs a new section and fatigue check.

## A bearing pair must resist a moment through spacing

A crossed-roller bearing supports overturning within its own internal geometry.
Two ordinary radial ball bearings use their separation to develop an opposing
force couple. One thin radial bearing does not provide an equivalent replacement.

For a screening calculation, the moment contribution to each bearing reaction is
approximately `M/s`. Here `M` is transverse overturning moment in N·m and `s` is
bearing center spacing in metres. With radial force `F` applied at the pair
midpoint, a conservative maximum reaction is `F/2 + M/s`.

The actuator's 17 N·m drive torque acts about the roll axis. Transverse bearing
overturning acts about perpendicular axes, so 17 N·m is not the bearing's maximum
moment demand. Foot placement and contact forces determine that demand.

The following cases use the current left-front foot locations, a 13.3 kg robot,
a 1 kg payload and vertical ground force. The proposed pair midpoint stays at
the existing bearing midpoint. The 3g case is a force screen without payload.
It does not establish a feasible gait or impact envelope.

| Screen | Vertical force at foot | Transverse moment | Maximum reaction, 14 mm spacing | Maximum reaction, 20 mm spacing |
| --- | --- | --- | --- | --- |
| Loaded normal stance, two supporting feet | 70.1 N | 3.44 N·m | 281 N | 207 N |
| Loaded front reach, two supporting feet | 70.1 N | 16.62 N·m | 1,222 N | 866 N |
| Loaded front reach, one supporting foot | 140.3 N | 33.24 N·m | 2,445 N | 1,732 N |
| Unloaded front reach, 3g shared over two feet | 195.7 N | 46.37 N·m | 3,410 N | 2,417 N |

The front reach puts the foot about 237 mm fore/aft from the bearing midpoint.
That offset explains the higher moment compared with normal stance's 49 mm.
Horizontal contact forces, axial loads, limb acceleration and motor-bearing load
sharing are omitted. A full wrench analysis must replace this screen before release.

JTEKT lists the following ratings for its specific Koyo contact-sealed bearings.
`Cr` is the basic dynamic radial load rating; `C0r` is the basic static rating.
The ratings belong to those products, not to every bearing sold under the same
dimensional designation.

| Koyo product | Cr | C0r | Mass each | Eight-bearing mass |
| --- | --- | --- | --- | --- |
| 6808 2RS | 6.15 kN | 4.20 kN | 33 g | 264 g |
| 6809 2RS | 7.75 kN | 5.40 kN | 40 g | 320 g |
| 6810 2RS | 8.20 kN | 6.10 kN | 52 g | 416 g |

Sources: [Koyo 6808](https://www.jtekt.co.jp/products/bearing/en/p/detail/?pno=6808+2RS),
[Koyo 6809](https://www.jtekt.co.jp/products/bearing/en/p/detail/?pno=6809+2RS),
[Koyo 6810 sealed bearing](https://koyo.jtekt.co.jp/en/products/detail/print.php?pno=6810+2RS).

The reference CAD allocates 80 g per crossed roller, or 320 g total. Eight
Koyo 6810 bearings would weigh 416 g before revised spacers and housings.
The 96 g difference uses a provisional reference mass; the selected hardware
and completed cartridges still require weighing and a revised robot mass estimate.

For the 3g reach screen, `C0r/reaction` is about 1.23 for a 6808 pair at
14 mm spacing, 1.74 for a 6808 pair at 20 mm, and 1.79 for a 6810 pair at 14 mm.
These are catalog rating ratios, not structural safety factors or service-life
predictions. Axial load, operating clearance, housing distortion and impact margin
still require evaluation. JTEKT explains that static-equivalent load depends on
actual loading and required operating performance.
[Static-load selection guidance](https://www.jtekt.co.jp/products/bearing/en/support/bearing-knowledge/5-5000.html).

The 6808 pair at 20 mm therefore offers a useful diameter reduction with a
screened radial reaction similar, relative to its static rating, to the shorter
6810 pair. Reducing 6808 spacing to 14 mm consumes much of that allowance.
Use the shorter 6808 layout only with a separately restricted operating envelope.

## Retention and bearing fits determine whether the simpler parts remain serviceable

Keep both bores coaxial in a metal housing and both journal seats coaxial on the
carrier. Finish the seats in a common setup where practical. Independently printed
bores can become misaligned or distort the thin rings; their suitability under
load requires measured installation and operating tests.

Use accessible axial shoulders and bolted face retention. Arrange shoulders so
each feature can be machined from an open X face with a straight tool. A through
bore with separate end retention is another candidate. Avoid an internal trapped
snap-ring groove or an inaccessible central reverse ledge.

Size the retainer's screw lands separately from its bearing contact annulus.
A proposed ring from radius 31.5 to 35.5 mm is only 4 mm wide. A centered
3.4 mm M3 clearance hole leaves approximately 0.3 mm to each radial edge.
Use broad rounded screw lugs or an existing wider stationary flange, then check
their complete envelope against the adjacent motor case and body.

Separate inner-ring and outer-ring spacing from the fastening load path. A screw
must not transmit its clamp force through a seal or an unsupported thin wall.
Document which shoulder locates each ring, which ring can accommodate thermal
growth, and how both bearings can be removed using force on the fitted ring.

Do not assume two ordinary sealed bearings form a matched preloaded pair.
Choose the actual bearing clearance and supplier-approved fits, then specify
endplay or preload with a measured assembly procedure. Increasing bolt torque
until play disappears is not a controlled preload method.

Slow hip motion makes stiffness, play, seal drag and oscillatory wear more
relevant than catalog speed limits. NSK identifies small-amplitude oscillation
and vibration as causes of false brinelling, which damages raceway contacts.
Grease choice and inspection intervals need validation for the actual motion.
[NSK failure guidance](https://www.nsk.com/eu-en/tools-resources/troubleshooting/damage-by-type/false-brinelling/).

## Standard sizes improve sourcing without proving inventory

US retailer NextPoint lists 6808-2RS at $8.75 each and 6810-2RS at $12.75 each.
Eight cost $70 or $102 before tax, shipping, spacers and revised custom parts.
These are advertised prices checked on 2026-10-28; inventory and delivery were
not verified. The retailer's bearings are not identified as the Koyo products
used for the rating comparison.
[6808 listing](https://nextpointbearing.com/products/68082rs_chrome_steel_sealed_radial_ball_bearing_40mm_x_52mm_x_7mm),
[6810 listing](https://nextpointbearing.com/products/68102rs_chrome_steel_sealed_radial_ball_bearing_50mm_x_65mm_x_7mm).

Bearings Direct also lists a sealed 50 × 65 × 7 mm 6810. That is a second US
catalog route. Its indexed page reports only two available at $29.19 each,
which is insufficient for this robot. These supplier-reported quantities were
not verified through checkout and do not establish future inventory.
[Additional 6810 supplier](https://bearingsdirect.com/6810-2rs-ball-bearing-50x65x7-sealed/).

The following additional 6810 sources distinguish a specific product from a
dimensionally similar alternative. Supplier stock statements are reported as
advertised on 2026-10-28; delivery and eight-unit allocation remain unconfirmed.

| Source | Identified product and price | Availability evidence | Rating and fit limitations |
| --- | --- | --- | --- |
| Lily Bearing | 6810-2RS, $6.85 each; eight total $54.80 | Live product page says in stock and shipping from Amazon's US warehouse. Delivery text is internally inconsistent. | Manufacturer lists Cr 1,388 lbf and C0r 1,296 lbf, approximately 6.17 and 5.76 kN. Normal radial clearance is 6–23 µm. Verify supplied grease. |
| McMaster-Carr | 4668K273, sealed 440C stainless 6810-2RS; price not exposed | Product page says in stock, without a quantity. | Dynamic rating 1,450 lbf. Static rating and manufacturer are not exposed; its specialty lubricant differs from an ordinary greased bearing. |
| USA Bearings & Belts | 6810-2RS, $16.04 each; eight total $128.32 | Listing says many in stock; US address in Largo, Florida. | Exact brand, clearance and ratings need confirmation. The seller warns that interchange performance can differ. |

Sources: [Lily manufacturer product](https://www.lily-bearing.com/products/6810-2rs/),
[McMaster product family](https://www.mcmaster.com/products/bearings/bearing-trade-number~6810-2rs/),
[USA Bearings & Belts](https://usbearingsandbelts.com/products/6810-2rs).

Lily's listed bore spans 49.988–50.000 mm, outside diameter 64.987–65.000 mm,
and width 6.880–7.000 mm. Those intervals must be included in the housing,
journal and spacer stack. Its listed static rating gives about 1.69 times the
3g reach-screen reaction at 14 mm spacing, before omitted loads or impact allowance.
This is a catalog comparison, not qualification.

For Koyo's specific sealed 6810, the recommended inner shoulder diameter is
52–53 mm, outer shoulder diameter at most 63 mm and corner radius at most
0.3 mm. Apply the selected manufacturer's requirements when drawing the retainers.
Geometric fit alone does not establish that a retainer bears on the correct ring.

The old carrier's 58 mm flange therefore needs face relief or an appropriate
inner-ring spacer. Pressing its whole face against a sealed ball bearing can
contact the seal region. Model independent inner- and outer-ring contact lands
and clearance to the seal, rather than treating the bearing as one solid annulus.

The perpendicular hip-motor cup also needs a removable stator closure, as
documented in the manufacturing review. Preserve that motor installation route
while extending the roll journal; bearing access alone does not make the combined
motor carrier serviceable.

Specify exact dimensions, seal type, clearance and minimum verified ratings
when comparing Amazon or distributor offers. An anonymous multipack with the
right dimensions cannot inherit another manufacturer's load ratings. Check
quantity and delivery for the selected part before freezing its design dependency.

## Finish the selected paired-bearing cartridge before releasing hardware

Complete the selected 6810 pair at 14 mm spacing with full shoulders, spacers,
retainers, socket access and extraction paths. Preserve the limb's track while
measuring fore/aft growth, motor-pilot clearance and electronic clearance. Measure
the actual ring widths before setting axial endplay or preload with spacers.

The 6808 at 20 mm and intermediate 6809 remain future packaging comparisons.
Reopening those options requires revisiting the journal, carrier stiffness and
complete assembly envelope.

Finish the full contact-force envelope and motor-bearing load-sharing model,
then check bearing ratings and housing stiffness for those loads. Bench-measure
play, drag, ring alignment and temperature before loaded motion. The calculations
are reproducible in [the read-only screen](../analysis/dfma/hip_roll_bearing_screen.py)
and [its results](../analysis/dfma/hip-roll-bearing-screen.json).

## The IKO crossed-roller option is deferred

The current robot uses two sealed 6810 bearings per hip, with 14 mm between
bearing centers. A future revision may replace each pair with one IKO
ZB3794CRBH crossed-roller bearing, advertised as 50 × 66 × 8 mm.
Four crossed rollers would serve the robot. This option is a procurement and
packaging candidate; it does not change the current CAD or purchase requirement.

Two US eBay listings identify the candidate:

- [BeckGuinn, item 272821503641](https://www.ebay.com/itm/272821503641):
  $79.99 each and more than ten available, as reported by the seller on
  2026-10-28. The photograph shows the box designation ZB 3794 CRBH.
- [SP Bearings, item 331274345848](https://www.ebay.com/itm/331274345848):
  photographs show a ring engraved IKO JAPAN ZB3794CRBH and a visible black
  seal. The photograph establishes the marking; manufacturer specifications
  remain unverified.

The exact designation has no verified manufacturer drawing in the project.
Do not assign it another IKO model's ratings, internal clearance or preload.
Seller-reported quantities do not establish continuing replacement supply.

For comparison, IKO catalogs the sealed CRBS508AUU at 50 × 66 × 8 mm,
with a 5.81 kN basic static rating. A conditional load screen using that rating
gave approximately 1.52 kN equivalent static load for the current robot's
unloaded landing scenario, a rating-to-load ratio of about 3.8.
The robot mass assumption was 14.15 kg, with 1 kg added for loaded scenarios.
This comparison does not establish the ZB3794CRBH rating, bearing life, housing
strength or landing capability. See the [IKO catalog](https://www.ikont.eu/files/Documents/Catalogues/CAT-57151UKv3_IKO_CRB.pdf)
for equivalent-load equations and the bearing table.

Revisit this option when the exact part's drawing, ratings, seals and clearance
are established, or a measured sample and manufacturer confirmation are available.
Compare the complete cartridge, including supports, fasteners and service access.
The nominal bearing pack could shrink from 21 mm to 8 mm, but that 13 mm
difference is not a measured reduction in the complete assembly.
The 66 mm outer diameter also requires a revised housing bore and race shoulders.
The future robot carrying a 20 kg payload requires a separate bearing selection.

## The printed housing is a fit prototype

The generated paired-bearing housing can be printed for unpowered assembly
and service checks. Its current metal-oriented sections are not qualified for
carrying the robot. Layer separation is one possible failure; bore distortion,
gradual deformation under sustained load, and fastener loosening also matter.

The current housing has a 72 mm nominal barrel outside diameter and a
65.15 mm trial seat diameter. That leaves about 3.43 mm of nominal radial wall
before local holes or pockets. The removable rear plate's bearing-stop collar
has a 1 mm radial wall, and the front retainer is 2 mm thick.
These fit-prototype dimensions do not establish minimum acceptable polymer
sections. Existing solid-contact and extraction checks establish access and
nominal interfaces; they do not establish printed strength.

The [current load study](../proposals/sculpted/model/output/roll-spacing-study/loads.json)
uses the generated model with SHA-256
`b968fea927022ba467e05eb52ab602a680e14fd7295c263eefcb95a58a90cdc6`.
It estimates a maximum bearing reaction near 1.86 kN for the loaded stair
screen and 2.76 kN for the unloaded landing screen at 14 mm center spacing.
The calculation samples instantaneous loads; motion trajectories remain unvalidated.
The landing screen uses 3g contact force shared over two feet and horizontal
force up to 40% of vertical force. It exceeds actuator peak torque in some joints.

The landing overturning moment is about 37.4 N·m. Resisting it through a
0.014 m bearing separation requires approximately 2,670 N of opposing radial
force at each bearing, before the direct-force contribution.
The bearing reactions therefore greatly exceed the force at the foot.
They must pass through the barrel and mounting roots into the chassis.

Printing with the bearing axis vertical is the starting orientation for the
separate housing. This places continuous circular walls in each horizontal
layer and avoids a supported bearing bore. It does not eliminate interlayer
shear between the two bearing seats or bending at the mounting roots.
An integrated chassis rail may require a different orientation and a new review.
Stratasys discusses orientation-dependent strength and deformation under sustained
load in its [FDM design guide](https://www.stratasys.com/contentassets/1a0cc7a8e7d14f29ac972189bfeade4c/dg_fdm_designconsiderationsfdmtooling_0718a.pdf).

A polymer structural revision should use continuous walls around each seat,
broad rounded mounting roots and accessible gussets. Inspect sliced wall paths
around bolt holes; high infill alone does not strengthen a thin root.
Use a measured bearing fit and removable face retention. Do not compensate
for a loose seat with an uncontrolled interference fit or excessive bolt torque.

PETG is a reasonable material for the initial fit print. A structural decision
requires the actual filament, drying, orientation and print profile to be tested.
Neither carbon-filled PETG nor a solid print establishes sufficient interlayer
strength or temperature resistance for this assembly.

For a loaded prototype, evaluate metal bearing-stop and retainer plates with
standard through-bolts and metal compression sleeves. The plates would spread
axial clamp loads, while sleeves would limit crushing beneath the fasteners.
They would not remove radial stress, interlayer shear or creep from the printed
barrel. These reinforcements remain proposed; they are not in the checked fit CAD.

Before loaded operation, bench-test the complete housing and its chassis
attachment under radial force and overturning moment in both directions.
Measure bearing play, bore deformation and bolt-clamp retention under repeated
loading and sustained loading at the measured operating temperature.
Set allowable displacement and permanent-set limits before that test.
Running, jumping and loaded stair use remain unqualified until those checks pass.
