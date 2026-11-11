# Knee stator screw-seat review

Nine ordinary M3 × 8 DIN 7991 countersunk screws can replace the projecting
socket heads. The proposed recesses clear the crank without changing the plate
envelope, motor position, compression tubes or thigh. Native authoring and the
resulting exports remain separate checks.

The analysis uses the current native plate and crank STEPs. Their exact hashes
and the measured results are in [review.json](review.json). At the nominal
standing crank angle, the existing screw at 140° intersects the crank by
14.877 mm³. This is a solid intersection, not only a mesh-screen indication.

Use a 90° countersink with a 5.90 mm nominal mouth at Y53.5, meeting the
existing 3.40 mm through bore at Y52.25. The cut is 1.25 mm deep in the
3 mm base plate, leaving 1.75 mm of straight web. The minimum measured
radial land to the outside edge is 1.05 mm; the central-bore land is 3.55 mm.
All nine seats have complete nominal support around the conical bearing area.

The existing head reference seats without the old conical clearance gap.
Its tip is Y45.5, giving 4.9 mm nominal penetration past the motor's Y50.4
stator face. Aligned crank-ear checks give 2.30 mm nominal clearance.
The proposed plate remains one valid solid.

DIN 7991 M3 heads are not all exactly 5.90 mm. Fastenal specifies a
5.70–6.00 mm diameter and a 90–92° head angle. Actual rim geometry, screw
length and printer error also change proud height and engagement. Check the
purchased head and physical seat before tightening; do not assume an ISO 10642
listing has identical dimensions. Inventory and delivery were not verified.
[Fastenal dimensional standard](https://www.fastenal.com/content/product_specifications/M.FHSCS.7991.FT.A4-70.02.pdf).

Machine the seats from +Y with a conventional 90° countersink. They are open
features with no trapped cutter path. Keep the holder above the nearby 55 mm
tie pads; an ordinary small countersink and shank have room between them.
Install and tighten these screws while the outer thigh is removed.

For printing, put the Y50.5 base on the bed and the countersinks upward.
This gives unsupported 45° cone walls and keeps support material out of the
seats. Use continuous perimeters around the holes and inspect the sliced
1.05 mm outer lands.

The dimensions establish nominal fit, not operating strength. A countersunk
head wedges radially as it is tightened, and the narrow outer land can split
or creep in a printed plate. Keep this stage finger-tight and unpowered.
Printed preload, cyclic loading and eventual machined-plate strength require
separate qualification. No mandatory plate or thigh redesign was identified
for this nominal fit proposal.

After native publication, the bench hardware table should replace nine knee
M3 × 8 socket screws with nine countersunk screws. Together with the hip
stator flange, that makes eighteen M3 × 8 countersunk screws per motor complex.
