Tinfox uses native, editable Fusion sketches and features in the
**Tinfox** project. The four active documents contain the robot assembly, leg,
chassis and head subsystems. Shared parts and handed copies belong inside these
documents rather than separate cloud files for each part.

Fusion is authoritative for the current low-profile robot: Tinfox v65 references
Leg40, Chassis18 and Head22. Its four integrated limbs use structural motor
cradles, shared bearing caps and ordinary socket-head screws. The assembly uses
72 distinct native custom and cut-stock definitions.
`manifests/native-low-profile-cleanup-master65-exports.json` records the approved
native review, STEP provenance, saved versions and qualification limits.
Changed interfaces and all four leg placements passed focused native checks;
unchanged definitions retain their earlier comparison evidence. Four obsolete
pose assemblies and their 32 frame/datum definitions have been deleted. The crossed-roller reference layouts and required construction sources
remain labelled and hidden. Existing body contacts and combined joint-range
limitations remain recorded.

The detached motor-complex fit package uses ten custom definitions saved in
Leg37. Its geometry is also installed in the current four-leg assembly. Native
exports and 78 focused interface checks are recorded in
`manifests/dfma-integrated-motor-complex-exports.json`. The print package supports
unpowered fit assembly. Polymer strength, loaded operation and the optional
raised-head variant remain unqualified.

`manifests/source-authority.json` identifies the canonical scopes. Earlier targets
and snapshots remain comparison evidence; their filenames do not establish
current authority.

The saved robot assembly exposes each motor, XT30 connector and cable envelope in its
own named reference body within its motion group. These bodies can be hidden
independently of the structural shells. `manifests/native-master-status.json` identifies the verified
saved versions and their scope; an in-progress subsystem does not replace that
saved assembly checkpoint.

The refined thigh and shin use shared native construction features and linked
manufacturing halves. A change to their design dimensions must regenerate both
halves and their handed counterparts. Motor patterns, bearing fits and fastener
clearances remain independent of limb length. Parameter count alone does not
establish that the complete robot can be resized.

Each native scope becomes authoritative after its current assembly passes the
comparison requirements in `AGENTS.md`. These include surface and
silhouette fidelity, dimensions and interfaces, placement, linkage closure,
motion clearance, service access, and parameter edit and restore tests. Native
features and sketches must remain editable. Imported mesh or BRep bodies satisfy
only the purchased-hardware reference role.

| Location | Contents |
| --- | --- |
| `source/` | Native authoring, export and independent comparison scripts |
| `snapshots/current-targets/` | Frozen current low- and high-profile references |
| `snapshots/cohesive-limb/` | Refined limb reference and construction dimensions |
| `snapshots/` | Earlier source references and captured construction recipes |
| `manifests/cohesive-leg-status.json` | Saved leg checkpoint and remaining tasks |
| `manifests/head-status.json` | Saved head checkpoint and its source scope |
| `manifests/native-master-status.json` | Verified saved assembly, references and open gates |
| `manifests/source-authority.json` | Current canonical scopes and whole-robot promotion status |
| `manifests/native-low-profile-exports.json` | Approved native low-profile baseline and export provenance |
| `manifests/current-native-backups.json` | Versioned native archives and their reference dependencies |
| `manifests/whole-robot-integration-target.json` | Current full-robot migration reference |
| `manifests/whole-purchased-reference-groups.json` | Exact purchased references, grouped by placement frame; custom parts excluded |
| `manifests/current-rpc.json` | Current or most recent Fusion operation |
| `manifests/publication-state.json` | Interrupted-publication reconciliation state |
| `audits/` | Geometry, parameter, fit, motion and service evidence |
| `exports/` | Native checkpoints and exported comparison geometry |

A geometry report applies only to its recorded source and export hashes. The
standard surface screen requires sampled distances below 0.05 mm and relative
volume and area errors below 0.1%. Cylindrical interfaces require axis and radius
agreement within 0.0001 mm. Section comparisons require sampled curve distances
below 0.05 mm and perimeter differences below 0.2%. Finite samples do not prove a
maximum error over every surface or a collision-free continuous motion range.

Some source spline surfaces produce unstable ordinary volume integration or
incorrect exported face-distance results. Reports must retain those failures and
record independent evidence, such as converged span-aware integration, direct
native sections or boundary classification. A numerical exception does not
justify relaxing bearing dimensions or omitting an unexplained discrepancy.

The low-profile source has clear nominal knee-folding samples and separate
hood, cover and cradle removal paths. Some combined roll and pitch poses still
collide in the generated source. Translation must preserve these limitations
explicitly and must not claim the full independent joint-limit box is usable.
Printed strength, physical bearing fit, flexible cables and loaded motion need
hardware qualification after CAD migration.

Custom parts must also meet the straight-tool access rule in `AGENTS.md`,
including parts intended for the first printed prototype. The initial review in
`audits/native-cnc-access-review.json` flags cassette guide windows and thigh
flange return ledges. Bearing seats need documented approaches from the outer
faces of the separated shells. These features remain unverified; native history,
surface agreement and successful motion checks do not establish machinability.
Do not remove bearing shoulders or load-carrying gussets to clear an access
warning without reviewing the resulting load path.

Only one process may own the Fusion MCP connection at a time. Reconcile any
interrupted mutation before another write. Inspect the Personal plan editable
inventory before creating or publishing a cloud document; preserve the robot assembly,
current work and at least one free editable slot. Closing a tab does not free a
slot. Never delete cloud files to make capacity.

For future history cleanup, roll the timeline back to the affected features
before a batch of early edits or deletions, then restore the end once. Replaying
the complete later history after each deletion makes even small cleanup batches
slow. Record native recomputation time separately from RPC transport time.
Journal long mutations so a client timeout can be reconciled without repeating
the writes.

Batch related parameter changes with Fusion's
[`Design.modifyParameters`](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Design_modifyParameters.htm).
It accepts user and model parameters in one atomic update. Use
`ValueInput.createByString` to preserve units and formulas. This applies to pose
changes, edit/restore checks and groups of dimension edits. Continue to roll the
timeline back before editing early features; parameter batching does not replace
the required feature-edit context.

Review export calculates a mesh once per native component definition and applies
each occurrence's recorded transform numerically. Mesh reuse requires identical
faces and corresponding coordinates within 0.0000001 mm; otherwise the occurrence
keeps its own geometry. Cache entries belong to that saved export only. Duplicate
hardware names do not establish component identity.

The earlier automatic worker targets an obsolete source inventory. Its stop
marker remains in place. Resume the current subsystem scripts through the
recorded checkpoints instead of running that worker against the latest robot.
