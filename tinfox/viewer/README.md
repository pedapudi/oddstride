# Tinfox robot design review

The viewer inspects the robot assembly, joint motion, section views and individual
parts. It uses local Three.js modules and recorded CAD exports. Live clearance
requests go only to the local review server.

The current low-profile robot derives from native Fusion Master63, referencing
Leg30, Chassis18 and Head22. Its 88 custom and cut-stock definitions are canonical.
The viewer supports whole-robot motion and individual part inspection; motors,
connectors and ordinary hardware remain separate references. The optional
electronics clearance envelope is hidden until requested.

The integrated motor complex is selectable as a detached fit assembly from Leg37.
**Current fit files** lists its approved unpowered fit packages. The complete
one-leg proposal is separately selectable while four-leg adoption is in progress.

## Run one current viewer

From the repository root:

```sh
tinfox/.venv/bin/python tinfox/viewer/serve.py
```

Open [the local viewer](http://127.0.0.1:8770/viewer/). The server binds to the
local computer and serves the `tinfox` directory. The CAD environment supplies
NumPy, trimesh and python-fcl for live rigid-part collision checks.

For static inspection without live checks:

```sh
python3 -m http.server 8770 --directory tinfox
```

Use HTTP to load browser modules and CAD files. Directly opening `index.html`
from the filesystem does not provide the required HTTP origin.

## Inspect assembly, motion and individual parts

- **Robot:** select a component, inspect its dimensions, show internal hardware
  or connector reservations, and focus on a limb or the body.
- **Motion:** select a recorded pose or adjust roll, hip pitch and knee pitch.
  Animation previews geometry; its intermediate positions are not simulated gaits.
- **Parts:** search the selected design's part library, isolate one part, inspect
  a section and open its recorded CAD exports.

The part list belongs only to the selected design. **Qty 2** identifies two
instances, not two revisions. Differently shaped left and right parts have
separate entries. Each limb has three actuators; **Show only the actuators**
labels them and hides passive housings.

Current fit packages are also on the Mac:

- `~/Downloads/Tinfox/Current-Motor-Fit/` for the three-object motor fit plate.
- `~/Downloads/Tinfox/Current-Motor-Complex/` for the corrected three-motor assembly.

Read [the motor-complex guide](../design/integrated-motor-complex-fit.md). The current
102-item proximal assembly uses ten custom pieces and six metal tubes. Its
changed interfaces passed 78 focused native checks. The fit plate combines
the native primary motor cradle with two generated auxiliary case gauges.
Complete assembly plates derive from native Fusion meshes with
recorded rigid print transforms. All files are unsliced and qualify only
supported, unpowered fit checks; strength and physical tolerances remain unqualified.

## Load historical catalogs only when requested

The viewer opens the current design in `catalog.json`. **Show archived designs**
adds earlier proposals to the selector. Their detailed part libraries are stored
as compressed, hashed entries under `archive/designs/` and load on selection.
A direct historical URL still works and displays an archive notice.
The startup catalog retains the model paths needed for comparison overlays.

The [historical index](archive/index.html) lists archived designs and the archive
of obsolete pages, screenshots and render iterations. Older standalone viewers
now show archive notices instead of presenting their geometry as current.

The historical part libraries, detached motor complex and limb proposal load
on selection to keep the startup catalog small.
Historical geometry and CAD migration snapshots remain in their original model
locations; the browser cleanup does not remove them.

## Restore an original browser artifact

The archive stores each distinct payload once and maps every original path to
its SHA-256 hash. Every original was verified before its active copy was replaced
or removed. The archive manifest records the files and restore command.

To restore one historical file from the repository root:

```sh
python3 tinfox/viewer/archive_artifacts.py \
  --restore tinfox/archive/browser/20261029T054951Z/browser-history.zip \
  --file viewer/captures/camera-cradle.png
```

Use `--overwrite` only when intentionally replacing an existing file, such as
an HTML archive notice. Omitting `--file` restores the complete archive.
Backups of the preceding README documents are stored alongside the archive.

## Interpret geometry checks and authority

A recorded clearance result applies to its specific model hash and joint pose.
A custom pose remains unchecked until its live request completes. Results for
an earlier design, pose or inspection mode are discarded after the view changes.

Live checks detect rigid-mesh intersections with listed mating and attached
interfaces excluded. They do not establish physical fits, flexible-cable motion,
polymer strength, thermal endurance or loaded locomotion. Fixed interfaces require
separate checks. Slider limits are inspection bounds rather than operating limits.

The native whole-robot export manifest records authority, saved versions,
audits and exact export hashes. Native-derived review files replace the generated
whole-robot view. Current print packages retain their narrower fit-only scope.
Older generated source and hash snapshots remain migration references.

## Publish metadata without restoring obsolete entry points

`catalog_io.py` writes the small current catalog and compressed historical entries.
The legacy metadata publisher can refresh generated references before native
promotion:

```sh
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/publish_viewer.py
```

It refuses to overwrite an active native Fusion review. After promotion, publish
from the verified saved native export allowlist. Do not use old generation scripts
to recreate competing current geometry or browser entry points.
Legacy manufacturing and prototype packagers also refuse to republish parts
that are canonical in Fusion. Their previous outputs remain historical references.

Run the full browser regression only for substantive viewer changes:

```sh
tinfox/.venv/bin/python tinfox/viewer/check_viewer.py --full-regression
```

It covers loading, deferred archives, part isolation, sectioning, release links
and request state. Routine CAD iteration uses changed-part engineering checks
and a visual review instead.
The source, local Three.js modules and license remain in `viewer/`. The cleanup
created no repository commit.

The native motor-complex publisher reads only its approved export manifest:

```sh
python3 tinfox/viewer/publish_native_motor_complex.py --model NATIVE_REVIEW_JSON_GZ
```

It requires native authority, saved part versions and the recorded review hash.
The `--candidate` option stages an explicitly unapproved preview in the ignored
`.native-candidate/` directory without changing the current catalog.
Add `--print-package PATH` to expose prepared STL/3MF downloads from a package
whose source-manifest hash matches the native export manifest.
The detached motor complex supports static assembly and part inspection. Joint
motion is available on the current native whole-robot review.

The native print preparer reads direct Fusion 3MF and STEP exports:

```sh
tinfox/.venv/bin/python tinfox/proposals/sculpted/model/prepare_native_motor_complex.py
```

It checks units, bounds and mesh volume against each native solid, then records
rigid print transforms and arranges the plates. The `--validate-only` option checks candidate exports without preparing a release.
The normal command refuses to prepare an unapproved native candidate. The generated print builders and finalizer refuse
to publish once that scope becomes canonical in Fusion.
