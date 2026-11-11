# Three-motor fit and assembly package

This package assembles three RS02 motors into one detached hip/thigh complex.
It contains thirteen custom parts plus optional printed spacing surrogates.
The shin, knee axle, pushrod and their hardware are not needed at this stage.

The files are generated-CAD exports. They are not native Fusion 3MF exports.
The native implementation and its exports remain a separate audited conversion.

## Start with the small motor-fit plate

The separate motor-fit package is on the Mac at
`~/Downloads/Tinfox/Current-Motor-Fit/`. Open `00-RS02-motor-fit.3mf` in
Bambu Studio to test the actual motor before committing to the larger housings.
The tested knee stator plate, hip stator flange and hip output hub can be
reused if their fit is acceptable; omit those objects from the later plates.

## Print the assembly in stages

| File in `plates/` | Contents |
| --- | --- |
| `01-roll-and-hip-carrier.3mf` | Paired-bearing housing, rear plate, retainer, inner backplate, both race spacers, motor cup and removable stator flange. |
| `02-thigh-motor-housing.3mf` | Both structural thigh halves, including the revised internal installation passage and screw access. |
| `03-motor-flanges-and-crank.3mf` | Hip output hub, knee stator plate and revised input crank. |
| `04-optional-fit-only-sleeves.3mf` | Three long pod sleeves, three short pod sleeves and two thigh-clamp sleeves for supported, finger-tight fit checks. |

These are unsliced 3MF files. Select the actual H2D, nozzle and filament profile,
preserve orientation and scale, and review supports and every layer before
printing. Curved shell exteriors and the horizontal carrier journal require
particular support review. Added brims and supports may need more plate spacing.

The individual STL/3MF files are available for single-part reprints. The STEP
files preserve the corresponding nominal geometry. The bearing and motor
hardware are purchased parts, not print jobs.

## Follow the assembly order

Read `ASSEMBLY.md` and `hardware.csv`. Install the hip-output screws before
the knee motor blocks their tool path. Install the knee stator plate and crank
screws with the outer shell removed, then close the shell over the module.
The front roof intentionally blocks those tools after closure; service requires
removing the outer shell. Keep all motors disconnected and support their weight.

Use the revised thigh and crank supplied here for this assembly. Earlier
complete-limb print packages do not contain every access correction.
`geometry-corrections.json` records the exact changes and STEP hashes.

## Interpret the checks

`checks/motor-complex-access.json` records nominal screw engagement, seating,
head/tool entry and sampled assembly paths on these corrected targets.
The other base reports apply to their identified source geometry.
The manifest identifies the source and every printed file is listed in
`SHA256SUMS`. These checks do not establish printer calibration, physical motor
tolerances, bearing preload, polymer strength or powered operation.
