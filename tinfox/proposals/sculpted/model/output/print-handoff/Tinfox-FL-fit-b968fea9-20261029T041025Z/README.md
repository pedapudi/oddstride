# Tinfox front-left limb fit prints

This package contains one front-left limb for an unpowered bench assembly.
It uses the checked generated CAD while native Fusion conversion remains under
review. The source model hash is `b968fea927022ba467e05eb52ab602a680e14fd7295c263eefcb95a58a90cdc6`.

## Open the bearing-fit tests first

Open `plates/00-bearing-fit-tests.3mf` in Bambu Studio. The file contains three
small dimensional test pieces: a 65.15 mm hip-bearing seat, a 49.90 mm journal
and a 28.10 mm knee-bearing seat. The journal axis is horizontal to reproduce
the motor carrier's print orientation and supported underside.

Select the actual H2D printer, nozzle, build plate and filament profile.
Keep the objects separate and retain their orientation. Disable automatic
orientation changes. Inspect supports and the layer preview before printing.
The 3MF files contain unsliced geometry; they contain no printer settings or G-code.
Allow both the print and bearings to reach room temperature before checking fit.
Record which bearing and filament were used and measure the resulting fit.
Do not drive a bearing into a tight print or load the limb to judge its strength.

Print the adjacent sizes in `coupons/` if needed. The optional
`bearing-fit-coupons.3mf` contains all nine sizes. It is not necessary to print
all nine before testing the three nominal sizes.

## Print one assembly stage at a time

| File in `plates/` | Contents | Preparation |
| --- | --- | --- |
| `00-bearing-fit-tests.3mf` | Three nominal bearing-fit test pieces | Match the final material and supports. |
| `01-hip-assembly.3mf` | Motor cup, removable motor flange, paired-bearing housing, rear plate and front retainer | Support the cup's horizontal journal; preserve access for support removal. |
| `02-thigh-halves.3mf` | Inner and outer structural thigh halves | Retain the long limb direction near the bed plane. Review exterior support under curved faces. |
| `03-shin-and-pushrod.3mf` | Inner and outer shin halves and a pushrod fit surrogate | Keep mating cavities upward. The printed pushrod is for assembly checks. |
| `04-small-fit-parts.3mf` | Hip hub, motor mount ring, input crank, inner backplate and two spacers | Printed metal-part surrogates establish fit only. |

Each limb part appears once across stages 01 through 04. The plate layouts
use 10 mm nominal gaps and fit within the project's 325 × 320 mm H2D bed
envelope with edge margins. Added supports or brims may require more spacing.
Do not scale parts to fit a different printer profile.

Use the individual files in `print-stl/` or `print-3mf/` to reprint one part.
The corresponding STEP files are in `reference-step/`. Standard bolts, metal
shafts and purchased bearings are not print jobs.

## Assemble with the purchased hardware

Follow [the hardware list and assembly sequence](ASSEMBLY.md). That guide covers
motor installation, fastener access, bearing retention and bearing removal.
A fit check of a print against another print does not establish fit against
the purchased motors, bearings, shafts or fasteners.

The bearing housing and thin retainers remain unqualified for loaded use.
See [the housing assessment](reference-docs/hip-roll-bearing-options.md#the-printed-housing-is-a-fit-prototype)
for the proposed reinforcements. This package does not add them.

## Package verification

The manifest records source and output hashes, part counts and plate layouts.
Fifteen limb meshes match the checked fit package byte for byte. The outer
thigh removes an obsolete 0.6 mm knee stub that obstructed its entry chamfer.
The bearing backup and M5 washer floor are preserved. The exact cut and hashes
are recorded in `geometry-corrections.json`; its revised STEP is included.
This correction uses the generated source rather than unfinished native solids.
The handoff checks confirm
closed meshes, consistent winding, matching bounding boxes and nonoverlapping
plate rectangles. They do not certify slicer toolpaths or operating tolerances.

The `checks/` folder contains the source CAD interface and sampled motion
reports. Those reports describe the base source model; the outer-thigh cleanup
has the separate checks above. Fixed contacts with the chassis remain unresolved;
this is a detached
limb assembly package. The assembly and housing notes reflect the documentation
available when the handoff was prepared.
