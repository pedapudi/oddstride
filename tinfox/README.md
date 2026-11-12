# Tinfox

Tinfox is the quadruped in [Oddstride](../README.md). The design uses twelve
RobStride RS02 actuators, approximately 170 mm leg links and a 1 kg additional
cargo target. The exterior uses a precision-instrument aesthetic with restrained
surfaces, fox-like color accents and legible functional details.

## Use the current robot viewer and fit packages

Start the review server from the repository root:

```sh
tinfox/.venv/bin/python tinfox/viewer/serve.py
```

Open [the robot viewer](http://127.0.0.1:8770/viewer/) to inspect the assembly,
individual parts, section views and joint motion. The [viewer guide](viewer/README.md)
explains its source labels, downloads and clearance limitations.
Earlier proposals are available through [the historical review index](viewer/archive/index.html).

The current low-profile robot is canonical in native Fusion: Master63 references
Leg30, Chassis18 and Head22. Its 88 custom and cut-stock definitions passed the
migration comparisons, assembly placement, motion and saved/reopen checks.
The browser now derives from those native models. Earlier generated designs
are archived migration references.

The separately selectable integrated motor complex uses ten native custom
parts from saved Leg37. Its changed interfaces passed 78 focused native checks;
the native print meshes also passed dimension and volume checks against STEP.
All ordinary M3/M4 limb screws use ISO 4762 socket heads. The approved fit scope
is a detached, supported, unpowered assembly. Adoption of the revised parts
across the four installed limbs is in progress.

The saved Fusion state is now Tinfox v66, referencing Leg module v41, Chassis v18
and Head v22. Leg v41 revises the knee linkage for hardware in hand; see
[knee linkage pivots and test pushrod](design/knee-linkage-pivots.md). The
browser exports have not been regenerated from v66.

The prepared files are on the Mac mini:

- Three-object motor fit plate: `~/Downloads/Tinfox/Current-Motor-Fit/`.
- Integrated three-motor assembly: `~/Downloads/Tinfox/Current-Motor-Complex/`.

Read [the hardware and assembly guide](design/integrated-motor-complex-fit.md)
before printing. The fit plate contains the reusable native primary motor
cradle and two unchanged generated case gauges. The complete package uses native Fusion
exports with recorded print transforms. All files are unsliced; choose the
actual H2D, nozzle and filament profile and review layers/supports in Bambu Studio.

## Use native Fusion as the CAD source of truth

The native migration uses four logical documents: Tinfox (the complete assembly),
Chassis, Leg and Head.
Custom parts require editable native sketches and features. Imported custom
meshes or BRep solids do not satisfy the migration requirement; purchased
hardware can remain reference geometry.

The current low-profile assembly passed surface and interface comparisons,
parameter edit/restore checks, native placement and motion checks, and saved
document reopening. Motors and connectors remain independently hideable
references. The optional raised-head variant is outside this baseline's scope.

Generate review geometry, print files and manufacturing exports
from the verified saved native parts. Preserve the generated source and hashed
snapshots as migration references. Do not regenerate competing current geometry
from them. The [native export manifest](proposals/sculpted/model/fusion_native/manifests/native-low-profile-exports.json)
records the approved baseline, source versions, native backups and part provenance.

## Keep actuator mass close to the body

A body-fixed hip-roll motor points fore/aft and drives a bearing-supported
carrier. The carrier mounts the hip-pitch motor on a perpendicular axis.
The hip output carries a coaxial knee-pitch actuator at the thigh root.
Two equal 28 mm cranks and one straight pushrod transmit knee motion.
The two structural halves of each thigh and shin contribute to limb stiffness.

The current hip-roll support uses two sealed 6810 bearings per joint at
14 mm center spacing. The complete robot needs eight. The shin uses two
6001 bearings per knee. The proximal motor-fit stage does not need the knee
axle, shin bearings, pushrod or shoulder screws.

The [bearing comparison](design/hip-roll-bearing-options.md) records loading
assumptions and the deferred crossed-roller option. The
[prototype limb guide](design/prototype-limb.md) distinguishes the older
complete-limb package from the revised motor-complex prints.

## Separate design targets from demonstrated performance

The earlier generated reference estimates approximately 14.15 kg base mass;
the target near 10 kg remains unmet. The native baseline has no qualified mass
estimate because material assignments remain provisional.
The underside battery cassette uses provisional tool-battery envelopes.
Exact packs, adapters and the complete electrical system remain unselected.

Loaded residential stairs, self-righting, running, jumping and 12 inches of
raised clearance remain development targets. Rigid geometry checks do not
establish gait performance, printed strength, thermal endurance or cable behavior.
The printed bearing housing and thin metal-part surrogates are fit prototypes.

Custom parts must avoid CNC undercuts. A complete machining setup and structural
qualification remain separate from CAD translation and print-fit checks.

## Preserve the studio references and archive obsolete browser reviews

The [studio reference](proposals/sculpted/design/studio-reference.png),
[earlier instrument concept](design/06-tinfox-instrument-concept.png) and
[articulated concept](design/08-articulated-hip-studio.png) remain visual references.
Low-profile sensors and an optional raised equipment head remain design variants.

Obsolete browser pages, screenshots and render iterations are preserved in
hashed archives under `archive/browser/`. Old HTML entry points display archive
notices. Their original payloads can be restored using the viewer guide.
CAD/native snapshots, audit inputs, source generators and current print releases
remain in place for migration and reproducibility.
