"""Prepare RS02 fit gauges and reusable motor-interface parts for the Mac."""
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh

from mesh_cleanup import clean_mesh
from prepare_mac_print_package import arrange, write_3mf
from cad_authority import require_generated_authority


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'output/paired-roll-work/prototype-limb'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    require_generated_authority(ROOT)
    name = f'Tinfox-Motor-Fit-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}'
    target = ROOT / 'output/print-handoff' / name
    target.mkdir(parents=True, exist_ok=False)
    for folder in ['individual-stl', 'reference-step']:
        (target / folder).mkdir()
    source = json.loads((SOURCE / 'manifest.json').read_text())
    items = []
    records = []
    for key, bore, outer, label in [
        ('01-thigh-case-gauge-80p50', 80.5, 90.8, 'K80.5'),
        ('02-hip-case-gauge-81p50', 81.5, 88.0, 'H81.5'),
    ]:
        outer_radius = outer / 2
        tab_y_min = bore / 2 + .05
        tab = cq.Workplane('XY').box(32, 15, 2, centered=(True, False, False)).translate((0, tab_y_min, 0)).val()
        shape = cq.Workplane('XY').circle(outer_radius).extrude(8).val().fuse(tab)
        shape = shape.cut(cq.Solid.makeCylinder(bore / 2, 10, cq.Vector(0, 0, -1)))
        text = cq.Workplane('XY').text(label, 4.0, .6, font='DejaVu Sans', combine=False).val()
        shape = shape.fuse(text.translate((0, tab_y_min + 8, 2))).clean()
        assert shape.isValid() and len(shape.Solids()) == 1, key
        step = target / 'reference-step' / f'{key}.step'
        cq.exporters.export(shape, str(step))
        vertices, faces = shape.tessellate(.015, .04)
        mesh = clean_mesh(trimesh.Trimesh(vertices=[v.toTuple() for v in vertices], faces=faces, process=False))
        assert mesh.is_watertight and mesh.is_winding_consistent
        items.append((key, mesh))
        records.append({'part': key, 'role': 'Diagnostic case-clearance gauge, not a robot component',
                        'bore_mm': bore, 'gauge_height_mm': 8, 'outer_diameter_mm': outer,
                        'source_dimension': 'slim_limb.CASE_BORE_RADIUS' if bore == 80.5 else 'paired_roll.PARAMETERS.carrier_motor_bore_mm'})
    for key, original in [('03-knee-stator-plate', 'motor_mount_ring'),
                          ('04-hip-stator-flange', 'hip_stator_closure_1'),
                          ('05-hip-output-hub', 'hip_hub')]:
        record = next(p for p in source['parts'] if p['part'] == original)
        source_stl = SOURCE / record['print_stl']
        assert sha(source_stl) == record['stl_sha256']
        mesh = trimesh.load_mesh(source_stl, process=True)
        assert mesh.is_watertight and mesh.is_winding_consistent
        items.append((key, mesh))
        shutil.copy2(SOURCE / 'reference-step' / f'{original}.step', target / 'reference-step' / f'{key}.step')
        records.append({'part': key, 'role': 'Reusable current motor-complex part', 'source_part': original,
                        'source_stl_sha256': record['stl_sha256']})
    for key, mesh in items:
        mesh.export(target / 'individual-stl' / f'{key}.stl')
    placed = arrange(items)
    write_3mf(target / '00-RS02-motor-fit.3mf', placed)
    (target / 'README.md').write_text('''# RS02 motor fit tests

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
''')
    manifest = {'source_model_sha256': source['model_sha256'], 'units': 'mm',
                'printer_envelope_mm': [325, 320, 325], 'parts': records,
                'objects': len(items), 'sliced': False,
                'plate_bounds_mm': {key: mesh.bounds.tolist() for key, mesh in placed},
                'scope': 'Unpowered RS02 radial case-clearance and mounting-interface fit checks; not a complete motor-complex release.'}
    (target / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    hashes = {str(p.relative_to(target)): sha(p) for p in sorted(target.rglob('*')) if p.is_file()}
    (target / 'SHA256SUMS').write_text(''.join(f'{value}  {key}\n' for key, value in hashes.items()))
    archive_path = target.with_suffix('.zip')
    with zipfile.ZipFile(archive_path, 'x', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(target.rglob('*')):
            if path.is_file():
                archive.write(path, str(Path(name) / path.relative_to(target)))
    print(json.dumps({'directory': str(target), 'archive': str(archive_path), 'archive_sha256': sha(archive_path)}), flush=True)


if __name__ == '__main__':
    main()
