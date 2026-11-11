# Native three-motor fit assembly

These thirteen custom parts come from the saved, audited native Fusion motor
complex. The source manifest records document versions and export hashes.
The native 3MF files preserve CAD coordinates; the prepared plates apply only
recorded rigid print transforms. No custom CAD is rebuilt for this package.

Open the files in `plates/` in Bambu Studio. They are unsliced. Select the actual
H2D, nozzle and filament, review supports and layers, and preserve scale and
orientation. This package is for a detached, supported, unpowered fit assembly.
It does not qualify printed strength or powered operation.

The prepared layouts use the H2D single-nozzle envelope, 325 × 320 × 325 mm.
Dual-nozzle mode has a narrower 300 mm envelope; rearrange the objects in Bambu
Studio if using that mode. See the [manufacturer specifications](https://cdn1.bambulab.com/documentation/h2d/en/H2D_Laser_Full_Combo_20250305.pdf).

Read `ASSEMBLY.md` and `hardware.csv` before assembly. Install motor stator and
output screws in the specified order before enclosing the thigh. Use metal
compression sleeves for operation. Any optional printed sleeve plate contains
finger-tight dimensional surrogates only.

The [static assembly review](checks/static-screen-review.md) and its linked
reports are included. `checks/assembled-native-reference.step` is the exact
121-body reference used by that screen; its hash is recorded in the native
source manifest. This STEP is an assembly reference rather than a print plate.
