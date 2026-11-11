"""Document the prepared geometry and package the printable and machining files."""
import json,zipfile,hashlib
from pathlib import Path
from kinematics import ROOT
out=ROOT/'output';dest=out/'manufacturing';plan=json.loads((out/'manufacturing-plan.json').read_text());result=json.loads((out/'refinement-checks.json').read_text())
assert plan['model_sha256']==result['model_sha256']==hashlib.sha256((out/'model.json').read_bytes()).hexdigest()
printed=[p for p in plan['parts'] if p['route']=='printed'];machining=[p for p in plan['parts'] if p['route']=='machining']
text=f'''TINFOX — PARTS AND PRINT PREPARATION

This kit contains {len(printed)} unique PETG part geometries, used in {sum(p['quantity'] for p in printed)} positions,
and {len(machining)} separate machining candidates. The TPU foot files are shape/fit
samples; their retention cavity and fastener are unresolved. Installed quantities
and handedness are listed in inventory.csv and manufacturing-plan.json.

FILES
printed-step/: editable solid geometry for printed prototypes and later CAD work.
printed-stl/: oriented PETG prototypes and TPU fit samples, in millimetres.
cnc-step/: custom metal components for manufacturing review.
fit-only-stl/: plastic mockups of metal components, for unloaded fit checks.
plates/: {len(plan['plates'])} unsliced 3MF layouts and top-view SVG diagrams.

Every individual STEP was reopened and checked for valid solid topology and
volume agreement. Offset boundary curves use a supported spline representation.
STEP does not contain a native Fusion feature timeline. The parametric source
remains in model/build.py in the full CAD package.

PRINTER AND PLATE ASSUMPTIONS
The layouts use the H2D single-nozzle volume of 325 x 320 x 325 mm.
They reserve 10 mm at each bed edge and 10 mm between part bounding boxes.
The usable geometry envelope is 305 x 300 x 315 mm. Brims and supports can
extend beyond those boxes; separate parts onto additional plates when needed.
Source: https://cdn1.bambulab.com/documentation/h2d/en/H2D_Laser_Full_Combo_20250305.pdf

The 3MF files contain meshes and placements only. They contain no filament or
machine profile, generated supports, layer preview, time estimate or G-code.
Import them into Bambu Studio and confirm the printer, nozzle and material.

ORIENTATION AND SUPPORTS
The roof and both sides form one 2.8 mm nominal-wall central clamshell. Print it
roof-down with the open interior, ribs and screw bosses facing upward. This avoids
bridging the body width. The curved roof needs local support where it leaves the
bed. The front and rear are ribbed modules with separate print orientations.

The convex fascia and sensor bezel print with the exterior facing upward.
Use shallow supports beneath their curved rear surfaces. Keep support contact
off the visible front and out of screw holes. The face has independent 8 mm horizontal and 10 mm vertical crowns. In a section above the sensor opening, the measured center
projects {result['face_center_to_y90_bow_mm']:.2f} mm beyond the section at +/-90 mm.

Structural thigh and shin lengths lie along the bed. The motor cradle remains
integral with the inner thigh; the outer structural half includes the service ring. The offset cup and inner web still require
accessible local supports. The outer thigh and shin cavities face upward where
possible. Do not print a limb upright merely to reduce its footprint.

Body end panels and rotating shoulder cowlings require support at selected
curves, internal steps and recesses. Their individual notes identify the regions.
The geometric screen counts downward-facing area; it does not distinguish every
printable bridge or calculate actual slicer support volume.
Source: https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135

ELECTRONICS DECK
The 134 x 186 x 4 mm PETG deck prints flat, with all holes and openings vertical.
Its geometry needs no designed supports. The fixed 3 mm aluminum brace is a flat
cutting and tapping candidate; it stays attached when the deck is removed. Select
metal stock thickness and thread engagement before fabrication.

STARTING SLICER SETUP FOR FIT PROTOTYPES
Assume a 0.4 mm nozzle and 0.2 mm layers, then use the printer manufacturer's
profile for the selected PETG. Start with six perimeters on structural limbs
and four on body covers. The modeled thin skins may fill completely with walls.
Use local support painting and inspect every layer around mounting seats,
channels and underside lips. Add a brim where contact is narrow. These are
starting settings, not tested strength or support-removal results.

Use PLA for appearance and unloaded fit checks. PETG, PETG-CF and ABS require
separate print qualification; their strength and shrinkage are not interchangeable.
The mass estimate uses solid CAD volume and does not assume an infill reduction.
Solid infill does not eliminate weak interlayer tension, creep or local stress
concentrations. Read print-strength-review.txt before structural testing.

ASSEMBLY AND MACHINING REVIEW
Print one inner/outer thigh pair and one inner/outer shin pair before duplicating all legs.
Check motor envelopes, mating faces, sleeves, integral shin rockers and split bearing seats and tool access.
The motor datums are nominal; verify them against the delivered actuators.
Select screw lengths, retention and fits before loading an assembled leg.

Metal carriers, output couplings and cranks retain metal load paths in the CAD.
Their plastic mockups are only for unloaded fit. Tubular sleeves, knee shafts
and spacers are identified as stock fabrication; bearings and fasteners are
purchased components. A modeled lidar lid is part of the provisional sensor
package, not an instruction to machine a sensor housing.

For future CNC work, retain the motor and bearing datums. Curved exterior
surfaces need finishing passes; deep cups and ring recesses may require multiple
setups or a removable retaining plate. Thin body shells need suitable workholding.
The kit contains no CAM toolpaths, tolerance drawings or approved machining stock.

REMAINING VALIDATION
Rigid CAD motion checks do not establish printed strength, fatigue, thermal
performance or loaded locomotion. Foot retention, exact battery adapters,
selected sensors, cables and flexible shoulder seals remain development items.
'''
(dest/'README.txt').write_text(text)
with zipfile.ZipFile(out/'tinfox-manufacturing-kit.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(dest.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(dest))
 for name in ['electronics-deck-audit.json','broad-root-audit.json','print-strength-audit.json','print-strength-review.txt','roll-shell-audit.json','integration-audit.json','hardware-research.json','hardware-shortlist.csv','limb-hardware-guide.txt','limb-assembly-audit.json','assembly-guide.txt','assembly-audit.json','manufacturing-plan.json','manufacturing-verification.json','refinement-checks.json','step-roundtrip.json','parts-catalog.json']:
  z.write(out/name,name)
 for p in sorted((out/'print-fixtures').glob('*')):
  if p.is_file():z.write(p,'print-fixtures/'+p.name)
 for p in sorted((out/'flat-patterns').glob('*')):
  if p.is_file():z.write(p,'flat-patterns/'+p.name)
print('Wrote manufacturing guide and fabrication kit.')
