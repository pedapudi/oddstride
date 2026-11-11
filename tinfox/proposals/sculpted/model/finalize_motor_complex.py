"""Package a checked generated motor complex; never label it Fusion-derived."""
import argparse
import csv
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from cad_authority import require_generated_authority

ROOT = Path(__file__).resolve().parent
TINFOX = ROOT.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    require_generated_authority(ROOT)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('--audit', type=Path, required=True)
    args = parser.parse_args()
    package = args.package.resolve()
    assert package.is_relative_to(ROOT / 'output/print-handoff')
    assert not package.with_suffix('.zip').exists(), 'Refusing to overwrite a released package.'
    audit = json.loads(args.audit.read_text())
    assert audit['overall_passed'] and not audit['failed_checks'], 'Motor-complex access checks remain unresolved.'
    manifest = json.loads((package / 'manifest.json').read_text())
    assert manifest['source_model_sha256'] == audit['source_model_sha256']
    for part, expected in audit['corrected_target_sha256'].items():
        assert sha(package / 'reference-step' / f'{part}.step') == expected, part
    guide = (TINFOX / 'design/motor-complex-fit.md').read_text().replace(
        'The complete motor-complex package is staged for final assembly-access checks.',
        'The complete motor-complex package passed its recorded nominal assembly-access checks.')
    (package / 'ASSEMBLY.md').write_text(guide)
    (package / 'README.md').write_text('''# Three-motor fit and assembly package

This package assembles three RS02 motors into one detached hip/thigh complex.
It contains thirteen custom parts plus optional printed spacing surrogates.
The shin, knee axle, pushrod and their hardware are not needed at this stage.

The files are generated-CAD exports. They are not native Fusion 3MF exports.
The native implementation and its exports remain a separate audited conversion.

## Start with the small motor-fit plate

The separate motor-fit package is on the Mac at
`~/Downloads/Tinfox/Current-Motor-Fit/`. Open `00-RS02-motor-fit.3mf` in
Bambu Studio to test the actual motor before committing to the larger housings.
The tested knee stator plate, hip stator flange and hip output hub can be
reused if their fit is acceptable; omit those objects from the later plates.

## Print the assembly in stages

| File in `plates/` | Contents |
| --- | --- |
| `01-roll-and-hip-carrier.3mf` | Paired-bearing housing, rear plate, retainer, inner backplate, both race spacers, motor cup and removable stator flange. |
| `02-thigh-motor-housing.3mf` | Both structural thigh halves, including the revised internal installation passage and screw access. |
| `03-motor-flanges-and-crank.3mf` | Hip output hub, knee stator plate and revised input crank. |
| `04-optional-fit-only-sleeves.3mf` | Three long pod sleeves, three short pod sleeves and two thigh-clamp sleeves for supported, finger-tight fit checks. |

These are unsliced 3MF files. Select the actual H2D, nozzle and filament profile,
preserve orientation and scale, and review supports and every layer before
printing. Curved shell exteriors and the horizontal carrier journal require
particular support review. Added brims and supports may need more plate spacing.

The individual STL/3MF files are available for single-part reprints. The STEP
files preserve the corresponding nominal geometry. The bearing and motor
hardware are purchased parts, not print jobs.

## Follow the assembly order

Read `ASSEMBLY.md` and `hardware.csv`. Install the hip-output screws before
the knee motor blocks their tool path. Install the knee stator plate and crank
screws with the outer shell removed, then close the shell over the module.
The front roof intentionally blocks those tools after closure; service requires
removing the outer shell. Keep all motors disconnected and support their weight.

Use the revised thigh and crank supplied here for this assembly. Earlier
complete-limb print packages do not contain every access correction.
`geometry-corrections.json` records the exact changes and STEP hashes.

## Interpret the checks

`checks/motor-complex-access.json` records nominal screw engagement, seating,
head/tool entry and sampled assembly paths on these corrected targets.
The other base reports apply to their identified source geometry.
The manifest identifies the source and every printed file is listed in
`SHA256SUMS`. These checks do not establish printer calibration, physical motor
tolerances, bearing preload, polymer strength or powered operation.
''')
    shutil.copy2(args.audit, package / 'checks/motor-complex-access.json')
    with (package / 'hardware.csv').open('w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Connection', 'Specification', 'Screws', 'Nuts', 'Washers', 'Physical checks remaining'])
        for item in audit['hardware']:
            writer.writerow([item['item'], item['specification'], item.get('quantity', ''),
                             item.get('nut_quantity', ''), item.get('washer_quantity', ''),
                             item.get('remaining_physical_checks', '')])
    manifest.update(export_source='Generated CAD with explicitly hashed corrections; not native Fusion exports.',
                    nominal_assembly_access_passed=True, access_report_sha256=sha(args.audit),
                    fabrication_scope='Supported, detached, unpowered fit and assembly only.')
    (package / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    hashes = {str(path.relative_to(package)): sha(path) for path in sorted(package.rglob('*'))
              if path.is_file() and path.name != 'SHA256SUMS'}
    (package / 'SHA256SUMS').write_text(''.join(f'{value}  {name}\n' for name, value in hashes.items()))
    archive_path = package.with_suffix('.zip')
    with zipfile.ZipFile(archive_path, 'x', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(package.rglob('*')):
            if path.is_file():
                archive.write(path, str(Path(package.name) / path.relative_to(package)))
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
    report = {'directory': str(package), 'archive': str(archive_path), 'archive_sha256': sha(archive_path),
              'checked_files': len(hashes), 'nominal_assembly_access_passed': True, 'source': manifest['export_source']}
    archive_path.with_suffix('.release.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
