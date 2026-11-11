# Assemble one unpowered RS02 motor complex

This guide assembles three RS02 actuators: hip roll, hip pitch and the proximal
knee-pitch actuator. It includes the paired 6810 support, perpendicular motor
carrier and integrated thigh housing. The shin, knee axle and pushrod are not
part of this assembly stage.

The small motor-fit plate is available on the Mac at
`~/Downloads/Tinfox/Current-Motor-Fit/00-RS02-motor-fit.3mf`.
The complete motor-complex package passed its recorded nominal assembly-access checks.
Its export source is generated CAD. Native Fusion features and native-derived
print exports remain under review; these 3MF files are not Fusion exports.

## Check the motor interfaces before printing the large housings

Print the five objects on the motor-fit plate with the actual H2D, nozzle and
filament profile. Preserve their orientation and dimensions. Inspect the layer
preview before printing; the files contain unsliced geometry without a printer
profile or G-code.

The two short rings check motor-case clearance. The other objects are the actual
knee stator plate, hip stator flange and hip output hub, so acceptable prints
can be reused in the assembly. Let the prints cool before measuring them.
Align every mounting hole while each part sits flat against the appropriate
motor face. Do not use screw tension to pull a misaligned part into position.

The thigh gauge has an 80.5 mm bore and the hip gauge has an 81.5 mm bore.
The nominal motor case is 78.5 mm diameter, so clearance is intentional.
The thigh shell's assembly passage locally enlarges its entry beyond the
80.5 mm gauge. That gauge remains a conservative case-clearance check; it does
not reproduce the full passage, connectors or axial installation path.

## Obtain hardware for one motor complex

The counts below cover one complex without spares. The screws use metric
coarse threads. Use ordinary socket caps to ISO 4762, button heads to ISO 7380-1
and the specified countersunk head geometry. A different head standard may
change seating depth and tool clearance.

| Connection | Specification | Quantity |
| --- | --- | ---: |
| Actuators | RobStride RS02 | 3 |
| Roll bearing pair | 6810-2RS, 50 × 65 × 7 mm | 2 |
| Long motor ties | M3 × 60 socket-head cap screw | 3 |
| Hip output to hub | M4 × 8 socket-head cap screw | 6 |
| Knee output to input crank | M4 × 12 socket-head cap screw | 6 |
| Knee stator to plate | M3 × 8 socket-head cap screw | 9 |
| Hip stator to removable flange | M3 × 8 countersunk screw; modeled DIN 7991 head geometry | 9 |
| Roll output coupling | M4 × 25 countersunk screw | 6 |
| Roll stator and housing | M3 × 30 button-head screw | 9 |
| Roll outer-race retainer | M3 × 25 button-head screw | 3 |
| Removable hip flange closure | M4 × 16 button-head screw | 3 |
| Thigh shell clamps | M4 × 25 button-head screw | 2 |
| Tie and retainer nuts | M3 hex nut, 5.5 mm across flats | 6 |
| Flange and shell-clamp nuts | M4 hex nut, 7 mm across flats | 5 |
| Flange washers | 4.3 mm ID × 9 mm OD × 0.8 mm | 3 |
| Shell-clamp washers | 4.3 mm ID × 12 mm OD × 1 mm nominal | 4 |

This stage uses M3 and M4 threads. The M5 knee-retention bolt, 6001 bearings,
pushrod bushings and shoulder screws belong to the later complete-limb stage.
Amazon.com is the preferred source for ordinary fasteners when the head,
dimensions and grade match. Order quantities, seller stock and delivery have
not been verified for this kit.

The motor manufacturer's drawing shows nine M3 stator holes on a 73 mm pitch
circle and six M4 output holes on a 24 mm pitch circle. It specifies 8 mm
depth for M3 and marks the M4 holes 7 mm minimum depth.
The prototype screw choices target no more than 6 mm penetration.
Confirm the actual motor revision, usable thread depth and printed stack before
tightening. The 7 mm minimum marking does not define a maximum permissible
screw length. [Manufacturer manual](https://www.robstride.com/assets/product_manual_robStride02-e7f9f7c4.pdf).

Expected nominal penetrations are 4.3 mm for the hip-output M4 × 8 screws,
5.4 mm for the crank's M4 × 12 screws and about 4.9 mm for the knee-stator
M3 × 8 screws. Countersunk screw penetration also depends on actual head seating.
An M3 × 65 tie is not interchangeable with the specified M3 × 60 tie.

## Use the sleeve stack to establish motor spacing

The three tie positions each use a 41 mm long tube and a 6 mm short tube,
both 5 mm OD with a 3.4 mm clearance bore. The stator plate and its integral
pads separate these segments. The screw head bears on the short tube's end;
the ordinary nut bears against the hip hub.

The two thigh-shell clamps each use an 18 mm compression sleeve, 8 mm OD
with a 4.3 mm bore. Their two large washers bear on the shell faces.

The package provides optional printed sleeve surrogates for checking spacing
before metal tubes are cut. Keep that assembly supported and finger-tight.
Printed sleeves, bearing spacers, hubs and retainers do not establish operating
preload or structural strength. Use measured metal components for subsequent
clamp-load and powered tests.

## Assemble the roll support and perpendicular hip carrier

Keep all three motors disconnected from power and support their weight on the
bench throughout assembly. Use metric hex keys and ordinary 5.5 mm and 7 mm
wrenches. No tightening torque is prescribed for the printed fit parts.

1. Keep the roll motor and rear stator plate off the housing while preparing
   the bearing cartridge. Insert the loose inner backplate from the motor side
   before trapping it behind the bearing pack.
2. Fit the two bearings with separate inner- and outer-ring spacers. Start the
   front retainer screws while the rear nut pockets remain accessible.
   The nuts must sit at their forward pocket floors; do not let them fall back
   while starting the screws. Fit the rear plate and roll motor afterward.
3. Attach the roll stator/housing stack with its nine M3 × 30 screws.
   The retainer controls the outer-ring stack separately from the motor screws.
   Tightening the retainer does not establish a controlled bearing preload.
4. Insert the perpendicular carrier's journal into the bearing pair. Align the
   inner backplate and install the six M4 × 25 roll-output screws through the
   empty hip-motor cavity. The hip motor is absent so the tool can reach them.
5. Insert the hip-pitch motor. Fit its removable stator flange with the nine
   M3 × 8 countersunk screws. Align the three flange locating pads and secure
   the flange to the cup with M4 × 16 screws, ordinary washers and nuts.
6. Attach the hip output hub with its six M4 × 8 socket-head screws before
   the knee motor occupies the space in front of those screws.

For the lower flange nut, use the checked 7 mm wrench route described in the
package's base service report. A generic 16 mm-wide, 3.8 mm-thick wrench head
clears with its handle approximately 15 degrees below the radial direction.
The screw is turned from the front while the wrench holds the nut.

## Close the thigh around the preassembled knee motor

The stator plate and crank screws are installed while the outer shell is off.
Their straight driver paths are blocked by the installed shell's front roof.
That roof remains continuous; service requires removing the shell.

1. Fit the inner thigh, long spacing tubes and knee motor to the hub assembly.
   Check both motor connector orientations against the molded openings.
2. Attach the knee stator plate with the nine M3 × 8 screws. Align its three
   outer tie holes and integral pads with the long tubes.
3. Attach the input crank with six M4 × 12 screws. Use the revised crank,
   whose screw-head counterbores remain open through the arm.
4. Install the short spacing tubes. Slide the revised outer shell over the
   preassembled module using its open internal stator-plate passage.
5. Insert the three M3 × 60 ties through their straight outer-shell channels.
   Seat each head on the short tube and start its ordinary M3 nut at the hub.
   The nominal stack gives 2.4 mm nut engagement and 1.6 mm thread projection.
6. Fit the two shell-clamp sleeves, four large washers, M4 × 25 screws and
   M4 nuts. Check mating faces and connector access before gentle closure.

Check the actual screw projection and seated faces. Do not add washers to the
specified motor-tie stack without recalculating engagement. Keep the assembly
supported; lifting or driving it through printed fit surrogates is outside this
test's scope.

## Match every print to its source revision

The updated outer thigh removes an obsolete knee-end lip and opens three tie
driver channels plus the inboard stator-plate passage. The updated crank opens
six screw-head counterbores through the arm. Both corrections remove trapped
features while preserving their defined seating faces.

The package's `geometry-corrections.json` records the source and corrected STEP
hashes. Its access report applies to those exact targets. Earlier limb print
files remain historical references; they do not include every correction in
this motor-complex package. Final bearing fits, motor-case tolerances, cable
routing, printed strength and operating preload require physical confirmation.
