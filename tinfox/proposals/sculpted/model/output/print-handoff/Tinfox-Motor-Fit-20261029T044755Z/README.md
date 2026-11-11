# RS02 motor fit tests

Open `00-RS02-motor-fit.3mf` in Bambu Studio. It contains five independent parts
for checking an actual RS02 before printing the larger motor carrier and thigh.
The motor remains disconnected from power throughout these checks.

Select the actual H2D printer, nozzle and intended filament profile. Retain the
supplied orientations and scale. Inspect the first layer, flange locating pockets
and small output-hub ribs before slicing. This is unsliced geometry with no
printer profile or G-code. Support decisions remain part of slicer preparation.

## Compare the printed gauges with the motor case

- `01-thigh-case-gauge-80p50`: the K80.5 marking identifies the 80.50 mm bore
  used by the proximal knee-motor housing in the thigh.
- `02-hip-case-gauge-81p50`: the H81.5 marking identifies the 81.50 mm bore
  used by the perpendicular hip-motor cup.

Both gauges are 8 mm deep. Slide each over the circular motor case from the
output end. They test radial case clearance only. They do not test connector
access, complete insertion depth or the final housing's stiffness.
The reference case diameter is 78.5 mm, so visible clearance is intentional.
The motor is retained by its stator bolts; these case bores are not clamp fits.
Do not squeeze the motor case or force a tight gauge over it.

## Check the reusable mounting parts

- `03-knee-stator-plate`: align its nine 3.4 mm clearance holes with the
  motor's M3 stator holes on a 73 mm pitch circle. The three outer holes
  belong to the structural motor ties, not the actuator bolt pattern.
- `04-hip-stator-flange`: check the second nine-hole stator pattern, the
  face clearance and the three rear locating pockets for the motor cup.
- `05-hip-output-hub`: align its six 4.4 mm clearance holes with the M4
  output holes on a 24 mm pitch circle. Check its central opening and the
  seating face against the motor output. This printed hub is a fit surrogate.

A pitch circle is the circle through the mounting-hole centers. The knee
stator plate and hip stator flange use different motor clocking in the assembly.
Rotate each loose part to align the nine-hole pattern before judging its fit.
None of these printed parts replaces a factory motor cover or factory screw.

Offer the parts to the motor by hand before inserting mounting screws. Check
that every hole aligns while the faces sit flat. A screw should start by hand
without pulling a misaligned plate into position.
The manufacturer's drawing shows M3 stator threads 8 mm deep and M4 output
threads marked 7 mm minimum depth. Actual screw penetration depends on the
printed part thickness, head seating and the motor's usable thread depth.
This test does not prescribe a motor tightening torque.

## Record the result before printing the full motor complex

Record the motor model/revision, filament, profile, gauge behavior and which
mounting faces or holes interfere. Let prints cool before measuring them.
If a seat needs adjustment, change the specific bore or hole parameter.
Scaling the entire part changes its bolt pattern and is not a fit correction.

The three mounting pieces can be reused for the unpowered three-motor assembly
if their fit is acceptable. The case gauges are diagnostic tools only.
The complete complex also needs the paired 6810 cartridge, full motor cup,
thigh halves, bearing spacers, retainers, input crank and confirmed fasteners.
Its instructions will be separate from this initial fit plate.

The source part hashes and exact gauge dimensions are recorded in `manifest.json`.
The included STEP files preserve the corresponding nominal interfaces.
This package uses the checked generated source while native Fusion conversion
is being audited. It does not qualify powered or loaded operation.
