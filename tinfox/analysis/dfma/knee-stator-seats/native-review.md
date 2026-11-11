# Native knee screw-seat comparison

Both native plate exports reproduce the nine countersinks in the reviewed
reference. Each plate is one valid solid with nine conical faces. The independent
volume difference is below 0.000000001 mm³, and sampled boundary error is below
0.000000001 mm in both directions. Exact input hashes and individual measurements
are retained in [native-seat-validation.json](native-seat-validation.json).

Each seat has a 5.90 mm mouth, a 90° included angle and 1.25 mm depth. The
remaining straight plate web is 1.75 mm. The modeled M3 × 8 DIN 7991 screws
seat without solid overlap and retain 4.9 mm nominal motor-thread penetration.
All eighteen nominal seat and straight-driver checks pass across the two hands.

The rotating crank stays at least 0.9 mm beyond the screw tops in the axial
direction. Rotation around that axis preserves this conservative bound.
The measured separation at the aligned crank fork is 2.3 mm. These dimensions
describe rigid nominal geometry; neither includes printed tolerances or loaded
deflection.

Coincident-solid subtraction produced spurious residual volumes. Those results
are retained as excluded numerical diagnostics. The comparison uses independently
integrated volume, matching bounds and symmetric boundary samples instead.

The minimum 1.05 mm outside-edge land remains a physical qualification concern.
A countersunk screw applies radial wedging force as it tightens. Purchased head
dimensions, printed seats, preload, polymer creep and fatigue require measurement
and testing before powered use. This review validates the native shape and nominal
fit; it does not qualify the printed plate for operation.
