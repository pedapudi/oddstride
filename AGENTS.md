# Project conventions

Describe Tinfox's visual direction as a precision-instrument aesthetic, using
concrete features such as restrained surfaces, legible labels, and functional color.
Do not attribute this aesthetic to external design brands in project artifacts,
rendering briefs, source comments, documentation, issues, or commit messages.

Prefer US-accessible hardware sources. Default to Amazon.com for ordinary
fasteners when the exact dimensions and grade match; Lowe's is only a local
fallback. Use McMaster-Carr, Fastenal,
or a manufacturer with US ordering for precision bearings, shafts, bushings and
shoulder screws. Distinguish verified dimensions from unverified stock or delivery.

Hardware must use common, replaceable specifications with broad US supply. Do not
make a special low-profile fastener a required design dependency without evidence
of ample stock and interchangeable sources. Catalog listings, package sizes and
price tiers do not establish inventory. Prefer geometric recesses or a standard
bolt with a smooth sleeve when a specialty fastener cannot meet this requirement.

The current hip-roll design must use more available standard bearings instead
of depending on the scarce 50 x 66 x 8 mm crossed-roller bearing. Evaluate a
spaced pair of sealed 6810 bearings and validate the complete housing, shaft,
retention, loading and motion envelope. Do not substitute a single radial ball
bearing for a crossed-roller bearing. Keep the previous crossed-roller layout
as a reference; access to that part in the future does not justify retaining it
as a dependency in the current design.

## Keep robot modeling central

Prioritize successfully modeling buildable robots. Do not add process layers,
general infrastructure, test harnesses, or broad browser/repository tests unless
they resolve a concrete blocker in the current modeling task or the user requests
them. Do not gate CAD progress on unrelated archive, UI, release, or bookkeeping
checks. Consider wall time, tool calls and tokens when choosing a workflow.

Use focused engineering cross-checks where relevant: motion and interference,
mounting interfaces, assembly and tool access, load paths, and manufacturability.
Check the changed parts and affected interfaces; reuse evidence for unchanged
geometry. A small visual check of an exported proposal is sufficient for routine
browser review. Full browser regressions belong to substantive viewer changes;
full migration audits belong to source adoption, not every CAD iteration.
Do not repeat whole-robot exports, inventories, reopen cycles or backup sets for
small isolated part changes without a specific unresolved reason.

Use Fusion's native modeling, tessellation, mesh and validation capabilities
where appropriate. Check existing capabilities before recreating them externally.
Use an external tool only for a demonstrated capability gap or a concrete
efficiency benefit with the required fidelity retained. Prefer small direct
operations and batched checks on loaded native geometry over new infrastructure.
Record only the evidence needed to understand and verify the design change.

## Design for manufacture and assembly

Apply DFMA throughout robot design, rather than as a final review. Minimize
physical pieces, fastening operations, hardware variants and separate mounting
stages. Prefer structural shells that also locate and mount components over
stacks of adapters, covers and ties. Share fastening duties when the load path,
preload control and service sequence permit it.

Use broad continuous walls, ribs, bosses, gussets and positive locating surfaces
to carry loads. Do not achieve a lower part count through weak necks, tiny
attachment areas or inaccessible joints. Preserve bearing support, controlled
fits, extraction access and cable clearance. Account for print orientation,
layer strength and polymer creep; use straight-tool access for CNC variants.

Design the actual assembly sequence alongside the geometry, including motor
insertion, output-pilot passage, connector routing, driver access and later
disassembly with common hand tools. Integration is useful only when the parts
can still be made, assembled and serviced. Preserve cohesive, flowing exterior
surfaces while simplifying their underlying construction.

Compare actual fabricated pieces, purchased hardware and assembly operations.
CAD bodies or repeated instances are not unique physical parts; replacing a nut
with an insert does not remove a piece. Count added spreaders, sleeves and
reinforcements. Prefer common replaceable hardware and reuse parts where practical.
Reduce screw counts through an engineered joint design, considering combined
loads and material behavior; an available motor hole pattern establishes neither
a mandatory full screw count nor approval for a reduced one.

Use ordinary ISO 4762 socket-head cap screws as the default for M3 and M4
connections. Consolidate lengths where motor thread engagement and assembly
access permit. Retain another head style only for a documented clearance or
functional requirement; review the surrounding geometry before adding that
exception. Keep exterior head recesses shallow without sacrificing washer
support, compression sleeves, structural walls, or tool access.

## CNC access and undercuts

Do not use undercuts in custom robot parts, including the initial printed
versions. Every machined feature must be reachable by a standard straight
end mill, drill, or tap from a documented setup direction. Multiple setups
and access from opposite faces are allowed; special undercut cutters do not
satisfy this rule. Avoid trapped internal grooves, dovetails, roofed captive
hardware pockets, and reverse-facing ledges that obstruct cutter access.
Use open pockets, through holes, accessible shoulders, or the existing
structural part split instead. Preserve bearing support and load paths when
removing an undercut. Audit existing geometry before describing it as
compliant; unreviewed features remain unverified.

## Native Fusion migration

Name the top-level Fusion document `Tinfox`. Use this single-word name in
Fusion document and component labels. Refer to it as the Tinfox assembly in prose.

Rebuild custom parts as native, editable Fusion features and sketches. Imported
meshes or imported BRep solids do not satisfy this requirement. Standard hardware
may remain reference geometry.

Until the native conversion passes comparison audits, the current generated CAD
remains authoritative. Preserve a hashed reference snapshot for each converted
part. Audit surfaces and silhouettes, critical dimensions and interfaces,
assembly placement, linkage closure, motion clearance, and service access.
Record existing limitations separately from translation defects. Check that
design parameters can be edited and restored without breaking the model.

Use Fusion for review and validation where native geometry improves the check:
targeted solid interference and critical interfaces, feature health, parameter
edit/restore behavior, occurrence placement, and independent component visibility.
Batch related checks inside Fusion scripts and reuse loaded native geometry.
Use local batch checks for broad motion and removal sweeps when they are more
efficient, then inspect suspect or critical pairs on native solids in Fusion.
Record the document versions or model hashes, checker, conditions and limitations
with each result. A native check of an older revision does not validate a newer
browser candidate. Interference results alone do not establish CNC cutter access
or structural strength; retain separate validation for those requirements.

After the audited native models are ready, make Fusion the source of truth and
generate review meshes, manufacturing exports, and downstream checks from those
models. Keep the previous generators as migration references; do not silently
regenerate competing authoritative geometry from them.

Fusion uses the Personal plan. Before creating a document or saving a cloud
copy, inspect `app.data.personalUseLimits` and account for editable files across
all projects. Keep the robot assembly and current work editable, and retain one
free slot after publication. Closing a document tab does not release its editable
slot. Saved referenced parts can remain Read-Only in the assembly.

The documented `PersonalUseLimits` inventory and `DataFile.isReadOnly` properties
are read-only. Change editable status only through a supported control. Only
verified, saved Tinfox documents that are no longer being edited are eligible;
preserve unsaved work and unrelated documents. Never delete files to free slots.
If a limit dialog blocks the MCP, stop sending writes. Reconcile any interrupted
publication before retrying it, even after the endpoint responds again.

Fusion's `Make Editable` and `Make Read-Only` commands can be invoked through
`userInterface.commandDefinitions` when available. Select the verified Tinfox
document first, check capacity and saved state, then verify the resulting status
in a separate read. Do not infer success from command acceptance. Working
subsystems and the robot assembly remain protected from automatic deactivation.
