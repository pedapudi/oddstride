"""Publish the measured body service arrangement."""
import hashlib,json
from kinematics import ROOT
out=ROOT/'output';audit=json.loads((out/'assembly-audit.json').read_text())
assert audit['model_sha256']==hashlib.sha256((out/'model.json').read_bytes()).hexdigest()
assert audit['passed'], 'Resolve assembly checks before publishing.'
text=f'''TINFOX — ASSEMBLY AND SERVICE ACCESS

A removable central clamshell combines the roof and both side walls. Four side
screws secure it to the internal frame. Lifting it exposes the electronics and
inboard motor connections without dismantling the motor frame. This gives better
side access than a deep bottom tub. Roof-mounted sensors need a disconnectable
harness and enough slack to lift the shell; those connectors remain unmodeled.

The motor load path runs through two aluminum longitudinal rails and two arched
transverse ties, plus a flat lower brace. The brace stays attached when the
electronics deck is removed. End caps attach independently to those ties, so removing the
clamshell does not release the front or rear shell. The ties sit beyond the
computer tray opening. Their metal sections and screw connections need stiffness,
fatigue and preload verification. Printed copies are unloaded fit models.

The front and rear upper/lower skins form two ribbed modules. The central shell
has a 2.8 mm nominal wall, integral ribs and screw bosses. Its open underside
allows printing roof-down with the interior facing upward. Local roof curvature,
bosses and end-cap returns still require slicer support review.

BENCH ASSEMBLY
1. Assemble each motor cartridge with its output fasteners accessible. Install
   the bearings, spacer, structural shin halves with integral rocker and retained pushrod
   pins in the order described in limb-hardware-guide.txt. Finish the unresolved
   axle preload and motor tie retention before applying loads.
2. Attach the cartridges to the longitudinal rails. Fit the two transverse ties
   with eight M3 countersunk screws and nuts. Four screws attach the ribbed end
   modules to the ties. Install these while the central shell is removed.
3. Prepare the underside battery cassette. Insert four M3 nuts from above before
   fitting packs or electronics. Battery adapters, latches, contacts and skid
   retention remain unspecified; the CAD reserves their envelopes only.
4. Fit the flat lower brace to the integral rail ledges with four M3 x 6 screws.
   Support the cassette and secure its four independent M3 x 12 side screws.
   Lower the flat PETG deck onto the brace and install four top-access M3 x 8 screws.
   Verify tapped engagement and screw-tip clearance before fitting actual batteries.
5. Install electronics on the flat deck. The computer envelope is 130 x 135 x 32 mm.
   Adapter bars, cooling, connectors and wiring still need the actual components.
   Route wires with the sides open and clear of moving hip and crank surfaces.
6. Connect the roof harness, lower the top-and-side shell and install its four
   side screws. Fit the separate convex fascia after checking sensor apertures.

SERVICE ORDER
Remove the four central cover screws, disconnect the roof harness and lift the
clamshell. The front and rear modules stay attached to the metal frame. Electronics
and inner motor wiring are then accessible from above and both sides.

To service electronics, remove the four top-access deck screws and disconnect its
harness. Lift the deck and computer through the top opening. The battery cassette
and fixed lower frame brace remain attached. No side-facing deck holes or mounting
ears are used.

To service the battery module, support the cassette and remove its four side
screws. Lower the module through the belly opening. The electronics deck can stay
installed. The cassette nuts are inserted before the upper frame is closed.

The 134 x 186 x 4 mm deck prints flat. Its six rounded openings and four adapter
slots pass vertically through the part. The fixed 3 mm aluminum brace is a separate
flat-cut and tapped part; its plastic copy is only an unloaded fit mockup. The
computer envelope remains 130 x 135 x 32 mm and is 2 mm above the deck. Measured
roof clearance is {audit['computer_to_roof_gap_mm']:.2f} mm. This is a geometric gap,
not a thermal airflow qualification. Actual standoffs, connectors and cooling need
the selected computer.

CAD CHECKS
The assembly passes {len(audit['paths'])} sampled withdrawal paths,
{len(audit['tool_access'])} straight driver approaches and four nut insertion paths.
The driver envelopes include a 3 mm tip, 6 mm shaft and 20 mm handle. Independent
attachment holes pass a 2.96 mm probe. Nominal attachment overlaps are checked.

The review does not qualify hand access, real connector clearance, continuous
trajectories, thread engagement, structural strength, printed creep or sealing.
Motor cartridges still require bench assembly before adjacent flanges close
access. Knee axle preload, motor tie stacks, roll bearing retainers,
foot attachment and cable routing remain open engineering tasks.

Interactive assembly and isolated frame:
http://127.0.0.1:8768/review/assembly.html
'''
(out/'assembly-guide.txt').write_text(text)
print('Wrote clamshell, frame and cassette service guide.')
