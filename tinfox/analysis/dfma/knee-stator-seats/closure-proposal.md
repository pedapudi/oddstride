# Recessed cup-closure screws

The frozen hardware reference confirms a 4.544 mm³ intersection between a
closure screw and a pod tie at neutral hip pitch. A second pairing has the
same overlap at −5°. At −10°, one pairing still intersects by 0.009262 mm³.
The original M4 screw head reaches Y2.1; the tie tip begins at Y1.0.

Use the existing ordinary M4 × 16 ISO 7380-1 button screws in recessed seats,
without the three separate closure washers. Put the seat floor at Y−2.2.
A maximum-height 2.2 mm head then ends at Y0, leaving a nominal 1 mm axial
gap to the tie tips through any hip rotation.

The closure plate has 1.1 mm deep locating pockets behind its screw seats.
A 1.3 mm counterbore alone would leave only 0.7 mm of material between the
two recesses. Preserve support by extending only the three closure lug backs
from Y−4.0 to Y−5.1. Fill the original locating pockets and move them back
with the lugs. Recess the corresponding cup lands by 1.1 mm and move their
locating bosses back by the same distance.

The resulting proposal has these dimensions:

| Feature | Nominal dimension |
|---|---|
| Front counterbore | 8.2 mm diameter, floor Y−2.2 |
| Closure pilot | 4.8 mm diameter |
| Rear locating pocket | 9.9 mm diameter, Y−5.1 to −4.0 |
| Cup locating boss | 9.6 mm diameter, Y−5.1 to −4.1 |
| Cup lug relief | 12.2 mm diameter, open toward +Y |
| Web between recesses | 1.8 mm |
| Outside land around counterbore | 1.9 mm |
| Screw tip | Y−18.2 |
| Ordinary M4 nut | Y−15.1 to −11.9 |
| Nominal nut engagement / tip projection | 3.2 mm / 3.1 mm |

The independently modified analysis cup and closure are each one valid solid.
All three screws, nuts and straight driver envelopes clear the proposed parts.
Each screw has 27.269 mm² of supported head-bearing area. Exact inputs and
measurements are in [closure-recess-proposal.json](closure-recess-proposal.json).
These results concern analysis geometry; native authoring and exported-part
verification remain required.

All nine tie/screw combinations have at least 1 mm nominal clearance through
continuous hip rotation. Rotation about Y preserves every point's Y coordinate:
the actual reference ties remain at Y≥1 and the recessed reference screws
remain at Y≤0. Ninety-nine exact sampled distances supplement this proof.
Fifty-one rear-tip and holding-wrench checks pass. The original contact cases,
hardware hash and individual checks are retained in
[closure-continuous-review.json](closure-continuous-review.json).

Fastenal specifies a 7.24–7.60 mm head diameter, 1.95–2.20 mm head height and
an underhead fillet diameter up to 4.7 mm for this M4 screw standard. The
4.8 mm pilot avoids forcing that fillet against a sharp 4.4 mm hole edge.
The ordinary hex key is 2.5 mm across flats. Stock was not verified.
[Fastenal dimensional standard](https://www.fastenal.com/content/product_specifications/M.BHSCS.73801.10.9.BO.04.pdf).

Machine the closure counterbores from +Y and its locating pockets from −Y.
The cup reliefs open toward +Y. The 1.3 mm radial gap around each locating
boss admits a standard 2 mm end mill. No reverse-facing cutter path is needed.
Install the closure and hold its ordinary nuts through the existing radial
cup slots before installing the hip output hub.

Print the separate closure with its broad Y−0.9 face on the bed. The shallow
counterbore floor bridges a 1.7 mm radial span outside the pilot. Printing on
only the three projecting rear lugs would leave the central ring above the
bed and require substantially more support. Inspect the sliced recess floors
and test their seating quality before assembly.

The cup relief near the 215° lug removes material from part of the cup's
connection to its bearing journal. Fifteen planar sections retain at least
99.012% of the original area. The smallest sampled section remains 657.836 mm².
Centroidal second moments of area retain at least 96.603% about Y and 96.715%
about Z. These geometric measurements do not establish strength or stiffness
of the manufactured part.

The 1.8 mm closure web also spans the locating pocket and requires preload,
creep and fatigue qualification. Keep this proposal limited to supported,
unpowered fit assembly until those checks pass. Native exported parts and
the complete assembly still require review before a new print package is issued.
