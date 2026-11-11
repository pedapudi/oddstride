# Chassis enclosure and assembly review

The quadruped uses a metal motor frame inside a removable printed enclosure.
The frame carries actuator loads through two side rails, two transverse ties
and a lower brace. The cover, sensor hood and battery cassette have separate
service fasteners. The CAD is a review candidate; physical strength and
production fits remain unqualified.

## Continuous shoulder openings replace corner tabs

The upper cover has one tangent lower-edge curve at each end and a rounded
plan boundary. These boundaries remove the short tabs left by overlapping
motor, connector and frame cuts. The cover ends above the fixed frame hardware
and lifts upward after four lateral screws are removed.

Four M3 × 10 screws attach the cover to integral metal rail bosses at
X = ±64 mm and Z = 18 mm. Broad ribs connect these bosses to the rail web and
upper flange. The cover has clearance holes; its thin wall does not retain
the screw threads. The display and power switch move with the cover.

The lower protective shell ends around the battery opening with rounded
corners. It does not provide actuator support. Its attachment and sealing
still need a complete hardware definition before fabrication.

## Tapped metal pads simplify frame assembly

Eight M3 × 8 countersunk screws join the transverse ties to integral rail
pads. The screw axes are X = ±115 mm, with a ±3 mm pair spacing, and
Y = ±104 mm. Each screw has 6 mm nominal metal engagement. The screw cones
seat in the ties; the model does not retain the previous front screw stand-off.

The forward transverse tie also contains two integral M4 sensor-mount bosses.
They replace the nuts underneath the sensor cradle and provide 6.8 mm nominal
engagement. The sensor hood still attaches separately to the cradle.

These changes remove ten nuts from the frame and sensor-root assembly.
The hole models show tap-drill geometry and nominal screw envelopes, without
helical threads. Purchased screw dimensions, aluminum grade, thread stripping,
preload and fatigue still require verification. Printed copies of the metal
frame are unloaded fit mockups.

## Fastener choices depend on the load path

| Connection | Design approach | Status |
| --- | --- | --- |
| Metal frame ties and sensor root | Standard screws into integral tapped pads | Modeled; strength unqualified |
| Main printed cover | Clearance holes into gusseted metal frame bosses | Modeled |
| Printed sensor hood and cradle | Heat-set inserts in broad, ribbed bosses are a candidate replacement for retained nuts | Proposed; current cradle retains nuts |
| Structural thigh and shin closures | Through-bolts with metal compression sleeves and accessible nuts | Retained; connection strength unqualified |
| Knee pivot and pushrod | Metal bearing, shoulder and compression interfaces | Retained; bearing ratings and fatigue unverified |

An insert provides a reusable thread, but its pull-out resistance depends on
the surrounding print. SPIROL recommends sufficient solid material around
the insert and reports improved performance with larger bosses and additional
wall loops. Its guidance does not establish an allowable load for this robot.
See the [manufacturer's printed-assembly guide](https://www.spirol.com/resources/white-papers/how-to-select-a-threaded-insert-for-your-3d-printed-assembly/).

Printed structural joints must also transfer shear between the two halves.
Replacing a through-bolt with an insert does not establish that transfer or
prevent creep. Insert dimensions, hole compensation and print orientation
must be matched to a selected component and verified with test pieces.
No insert inventory or delivery has been verified.

## Assembly and service sequence

1. Assemble the fixed roll motors, their cartridges and the limb motor carriers
   on the bench. Install connectors before enclosing the mounting faces.
   Verify the manufacturer mounting screws and connector orientations.
2. Attach the motor cartridges to the side rails while their mounting screws
   remain accessible. Join the rails with the lower brace and transverse ties.
   Install the eight top-access tie screws into the tapped pads.
3. Fit the battery cassette from below. Install its retained nuts before
   closing access. Its four side screws remain independent of the deck and
   frame screws. Pack adapters, contacts and strain relief remain unselected.
4. Lower the electronics deck onto the fixed lower brace. Its four top-access
   screws allow removal without dismantling the motor frame or battery mounts.
   Computer-specific standoffs, cooling and cable retention remain to be defined.
5. Attach the sensor cradle to the two M4 tapped bosses from above. Fit the
   sensor hood after connecting its wiring. Hood removal leaves the cradle
   and frame installed.
6. Fit the main cover with its display and switch. Connect their cables through
   the open enclosure, then install four lateral M3 screws. Service requires
   removing these screws and disconnecting the cover wiring before lifting.

Cable bend radii, connector latches, strain relief, hand access and electrical
assembly are not established by a clear rigid-part removal path. Motors,
connectors and cable-routing references remain separate objects for inspection.

## CNC undercuts are prohibited

Every custom part, including a printed prototype, must permit each feature
to be reached by a standard straight end mill, drill or tap. Opposite-face
and multiple setups are allowed. Special undercut cutters do not satisfy
the requirement. The persistent rule is in [AGENTS.md](../../AGENTS.md).

Existing geometry is not yet certified against this requirement. The battery
cassette's internal guide windows and upper guide gussets need review for
trapped cutter access. The thigh's stator-pocket return ledges also need
documented cutter directions. Bearing backup shoulders require opposite-face
access or an accessible structural split; removing a shoulder without restoring
bearing support is unacceptable.

The two-piece limb construction should expose bearing seats, nut pockets and
linkage cavities directly from the mating faces. A rounded recess is not
automatically machinable: cutter diameter, flute length, holder clearance and
fixture access must also be checked. Any unresolved undercut prevents release
of the affected part for CNC manufacture.

## Review files

Open the [body and fixed motors](http://127.0.0.1:8770/viewer/?design=v11&focus=chassis)
or the [whole robot](http://127.0.0.1:8770/viewer/?design=v11). The viewer provides
individual STEP and STL files and reports for motion, frame seating, driver
access and sensor-module removal. The smoother thigh face removes the exterior
waist depression while preserving its internal linkage cavity.

The generated candidate remains separate from the audited native Fusion
baseline. Native migration must preserve the reference shape and pass its
comparison checks before replacing the generated CAD as the source of truth.
