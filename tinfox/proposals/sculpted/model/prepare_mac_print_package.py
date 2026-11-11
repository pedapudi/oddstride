"""Stage checked limb-fit meshes as an unsliced, portable Bambu Studio handoff."""
import argparse
import hashlib
import json
import shutil
import zipfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import trimesh
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps

from export_closed_mesh import closed_mesh
from cad_authority import require_generated_authority


ROOT = Path(__file__).resolve().parent
TINFOX = ROOT.parents[2]
SOURCE = ROOT / 'output/paired-roll-work'
CORE = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('', CORE)
PLATES = [
    ('00-bearing-fit-tests', ['6810-seat-65p15', '6810-journal-49p90', '6001-seat-28p10']),
    ('01-hip-assembly', ['motor_carrier_1', 'hip_stator_closure_1', 'roll_cartridge_1',
                         'roll_stator_backplate_1', 'roll_outer_retainer_1']),
    ('02-thigh-halves', ['thigh_inner', 'thigh_outer']),
    ('03-shin-and-pushrod', ['shin_inner', 'shin_outer', 'pushrod']),
    ('04-small-fit-parts', ['roll_inner_backplate_1', 'roll_inner_spacer_1',
                           'roll_outer_spacer_1', 'hip_hub', 'motor_mount_ring', 'input_crank']),
]
KNEE_REFERENCE = ROOT / 'fusion_native/snapshots/knee-stub-cleanup/thigh_outer.step'
KNEE_REFERENCE_SHA = '444e1937618b2f33438fbc0684d8eedcad4b366b791220c9fcfe778d1a02c0e2'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def arrange(items):
    """Place bounding rectangles within a 305 x 300 mm bed area, with 10 mm gaps."""
    placed = []
    x = y = 10.0
    row_height = 0.0
    for name, original in sorted(items, key=lambda item: -item[1].extents[1]):
        mesh = original.copy()
        width, height, _ = mesh.extents
        if x + width > 315.0:
            x = 10.0
            y += row_height + 10.0
            row_height = 0.0
        assert y + height <= 310.0, (name, width, height, y)
        mesh.apply_translation([x - mesh.bounds[0, 0], y - mesh.bounds[0, 1], -mesh.bounds[0, 2]])
        assert np.all(mesh.bounds[0] >= -1e-5), name
        assert np.all(mesh.bounds[1] <= [315.0001, 310.0001, 315.0001]), name
        for _, other in placed:
            overlap = np.minimum(mesh.bounds[1, :2], other.bounds[1, :2]) - np.maximum(mesh.bounds[0, :2], other.bounds[0, :2])
            assert not np.all(overlap > 0), name
        placed.append((name, mesh))
        x += width + 10.0
        row_height = max(row_height, height)
    return placed


def write_3mf(path, items):
    root = ET.Element(f'{{{CORE}}}model', unit='millimeter', attrib={'xml:lang': 'en-US'})
    resources = ET.SubElement(root, f'{{{CORE}}}resources')
    build = ET.SubElement(root, f'{{{CORE}}}build')
    for i, (name, mesh) in enumerate(items, 1):
        obj = ET.SubElement(resources, f'{{{CORE}}}object', id=str(i), type='model', name=name)
        geometry = ET.SubElement(obj, f'{{{CORE}}}mesh')
        vertices = ET.SubElement(geometry, f'{{{CORE}}}vertices')
        triangles = ET.SubElement(geometry, f'{{{CORE}}}triangles')
        for vertex in mesh.vertices:
            ET.SubElement(vertices, f'{{{CORE}}}vertex', x=f'{vertex[0]:.6f}', y=f'{vertex[1]:.6f}', z=f'{vertex[2]:.6f}')
        for face in mesh.faces:
            ET.SubElement(triangles, f'{{{CORE}}}triangle', v1=str(face[0]), v2=str(face[1]), v3=str(face[2]))
        ET.SubElement(build, f'{{{CORE}}}item', objectid=str(i))
    content_types = ('<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    relationships = ('<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                     '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
                     'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', content_types)
        archive.writestr('_rels/.rels', relationships)
        archive.writestr('3D/3dmodel.model', ET.tostring(root, encoding='utf-8', xml_declaration=True))


def main():
    require_generated_authority(ROOT)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    source_manifest = json.loads((SOURCE / 'prototype-limb/manifest.json').read_text())
    release = json.loads((SOURCE / 'prototype-release.json').read_text())
    stamp = sha(SOURCE / 'model.json')
    assert stamp == source_manifest['model_sha256'] == release['model_sha256']
    assert sha(SOURCE / 'prototype-limb.zip') == release['archive_sha256']
    label = f'Tinfox-FL-fit-{stamp[:8]}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}'
    target = args.output or ROOT / 'output/print-handoff' / label
    if target.exists():
        raise FileExistsError(f'Refusing to overwrite a print handoff: {target}')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE / 'prototype-limb', target)
    (target / 'plates').mkdir()
    (target / 'reference-docs').mkdir()
    meshes = {}
    part_checks = []
    assert sha(KNEE_REFERENCE) == KNEE_REFERENCE_SHA
    original = cq.importers.importStep(str(SOURCE / 'step/thigh_outer.step')).val()
    corrected = cq.importers.importStep(str(KNEE_REFERENCE)).val()
    assert corrected.isValid() and len(corrected.Solids()) == 1
    cut_box = cq.Solid.makeBox(80, 20, 80, cq.Vector(-40, 97, -210))
    expected = original.cut(cut_box)
    def volume(shape):
        props = GProp_GProps()
        BRepGProp.VolumePropertiesGK_s(shape.wrapped, props, 1e-9, True, True)
        return props.Mass()
    assert volume(expected.cut(corrected)) + volume(corrected.cut(expected)) < .01
    corrected_volume = volume(corrected)
    with tempfile.TemporaryDirectory(prefix='tinfox-print-mesh-') as folder:
        candidate_stl = Path(folder) / 'thigh_outer.stl'
        cq.exporters.export(corrected, str(candidate_stl), tolerance=.02, angularTolerance=.08)
        corrected_mesh, corrected_mesh_check = closed_mesh(KNEE_REFERENCE, candidate_stl, corrected_volume)
    # Preserve the checked print orientation, including the existing supported
    # curved exterior. A geometry cleanup does not authorize reorienting a limb.
    corrected_mesh.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(-90), [1, 0, 0]))
    bounds = corrected_mesh.bounds
    corrected_mesh.apply_translation([-(bounds[0, 0]+bounds[1, 0])/2,
                                      -(bounds[0, 1]+bounds[1, 1])/2, -bounds[0, 2]])
    corrected_mesh.export(target / 'print-stl/thigh_outer.stl')
    single = corrected_mesh.copy()
    single.apply_translation([162.5, 160, 0])
    write_3mf(target / 'print-3mf/thigh_outer.3mf', [('thigh_outer', single)])
    shutil.copy2(KNEE_REFERENCE, target / 'reference-step/thigh_outer.step')
    correction = {'part': 'thigh_outer', 'source_step_sha256': sha(SOURCE / 'step/thigh_outer.step'),
                  'corrected_step_sha256': KNEE_REFERENCE_SHA,
                  'operation': 'Remove obsolete knee stub inside X[-40,40], Y[97,117], Z[-210,-130] mm.',
                  'reason': 'Expose the entry chamfer and remove its reverse-facing return lip.',
                  'removed_volume_mm3': volume(original) - corrected_volume,
                  'preserved_interfaces': ['M5 washer floor at Y94 mm', 'Bearing backup at Y85.3 mm'],
                  'mesh_check': corrected_mesh_check,
                  'scope': 'Corrected generated reference. Native Fusion source-of-truth promotion remains pending.'}
    (target / 'geometry-corrections.json').write_text(json.dumps(correction, indent=2))
    for part in source_manifest['parts']:
        path = target / part['print_stl']
        if part['part'] == 'thigh_outer':
            part.update(stl_sha256=sha(path), three_mf_sha256=sha(target / part['print_3mf']),
                        oriented_bounds_mm=corrected_mesh.extents.tolist(), geometry_correction='geometry-corrections.json')
        else:
            assert sha(path) == part['stl_sha256'], part['part']
            assert sha(target / part['print_3mf']) == part['three_mf_sha256'], part['part']
        mesh = trimesh.load_mesh(path, process=True)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, part['part']
        assert np.allclose(mesh.extents, part['oriented_bounds_mm'], atol=.001), part['part']
        meshes[part['part']] = mesh
        part_checks.append({'part': part['part'], 'closed': True, 'consistent_winding': True,
                            'bounds_match_manifest': True, 'triangles': len(mesh.faces)})
    assert len(source_manifest['parts']) == 16
    stage_parts = [key for _, names in PLATES[1:] for key in names]
    assert len(stage_parts) == len(set(stage_parts)) == 16
    assert set(stage_parts) == set(meshes)
    for name in source_manifest['coupons']:
        mesh = trimesh.load_mesh(target / 'coupons' / f'{name}.stl', process=True)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, name
        meshes[name] = mesh
    plate_records = []
    for name, keys in PLATES:
        items = arrange([(key, meshes[key]) for key in keys])
        path = target / 'plates' / f'{name}.3mf'
        write_3mf(path, items)
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            xml = ET.fromstring(archive.read('3D/3dmodel.model'))
            assert xml.attrib['unit'] == 'millimeter'
            assert len(xml.findall(f'{{{CORE}}}build/{{{CORE}}}item')) == len(items)
        plate_records.append({'file': str(path.relative_to(target)), 'objects': keys,
                              'bounds_mm': {key: mesh.bounds.tolist() for key, mesh in items},
                              'sha256': sha(path)})
    guide = (TINFOX / 'design/prototype-limb.md').read_text()
    guide = guide.replace('../proposals/sculpted/model/output/paired-roll-work/prototype-limb.zip', '.')
    guide = guide.replace('(hip-roll-bearing-options.md', '(reference-docs/hip-roll-bearing-options.md')
    (target / 'ASSEMBLY.md').write_text(guide)
    (target / 'README.md').write_text(f'''# Tinfox front-left limb fit prints

This package contains one front-left limb for an unpowered bench assembly.
It uses the checked generated CAD while native Fusion conversion remains under
review. The source model hash is `{stamp}`.

## Open the bearing-fit tests first

Open `plates/00-bearing-fit-tests.3mf` in Bambu Studio. The file contains three
small dimensional test pieces: a 65.15 mm hip-bearing seat, a 49.90 mm journal
and a 28.10 mm knee-bearing seat. The journal axis is horizontal to reproduce
the motor carrier's print orientation and supported underside.

Select the actual H2D printer, nozzle, build plate and filament profile.
Keep the objects separate and retain their orientation. Disable automatic
orientation changes. Inspect supports and the layer preview before printing.
The 3MF files contain unsliced geometry; they contain no printer settings or G-code.
Allow both the print and bearings to reach room temperature before checking fit.
Record which bearing and filament were used and measure the resulting fit.
Do not drive a bearing into a tight print or load the limb to judge its strength.

Print the adjacent sizes in `coupons/` if needed. The optional
`bearing-fit-coupons.3mf` contains all nine sizes. It is not necessary to print
all nine before testing the three nominal sizes.

## Print one assembly stage at a time

| File in `plates/` | Contents | Preparation |
| --- | --- | --- |
| `00-bearing-fit-tests.3mf` | Three nominal bearing-fit test pieces | Match the final material and supports. |
| `01-hip-assembly.3mf` | Motor cup, removable motor flange, paired-bearing housing, rear plate and front retainer | Support the cup's horizontal journal; preserve access for support removal. |
| `02-thigh-halves.3mf` | Inner and outer structural thigh halves | Retain the long limb direction near the bed plane. Review exterior support under curved faces. |
| `03-shin-and-pushrod.3mf` | Inner and outer shin halves and a pushrod fit surrogate | Keep mating cavities upward. The printed pushrod is for assembly checks. |
| `04-small-fit-parts.3mf` | Hip hub, motor mount ring, input crank, inner backplate and two spacers | Printed metal-part surrogates establish fit only. |

Each limb part appears once across stages 01 through 04. The plate layouts
use 10 mm nominal gaps and fit within the project's 325 × 320 mm H2D bed
envelope with edge margins. Added supports or brims may require more spacing.
Do not scale parts to fit a different printer profile.

Use the individual files in `print-stl/` or `print-3mf/` to reprint one part.
The corresponding STEP files are in `reference-step/`. Standard bolts, metal
shafts and purchased bearings are not print jobs.

## Assemble with the purchased hardware

Follow [the hardware list and assembly sequence](ASSEMBLY.md). That guide covers
motor installation, fastener access, bearing retention and bearing removal.
A fit check of a print against another print does not establish fit against
the purchased motors, bearings, shafts or fasteners.

The bearing housing and thin retainers remain unqualified for loaded use.
See [the housing assessment](reference-docs/hip-roll-bearing-options.md#the-printed-housing-is-a-fit-prototype)
for the proposed reinforcements. This package does not add them.

## Package verification

The manifest records source and output hashes, part counts and plate layouts.
Fifteen limb meshes match the checked fit package byte for byte. The outer
thigh removes an obsolete 0.6 mm knee stub that obstructed its entry chamfer.
The bearing backup and M5 washer floor are preserved. The exact cut and hashes
are recorded in `geometry-corrections.json`; its revised STEP is included.
This correction uses the generated source rather than unfinished native solids.
The handoff checks confirm
closed meshes, consistent winding, matching bounding boxes and nonoverlapping
plate rectangles. They do not certify slicer toolpaths or operating tolerances.

The `checks/` folder contains the source CAD interface and sampled motion
reports. Those reports describe the base source model; the outer-thigh cleanup
has the separate checks above. Fixed contacts with the chassis remain unresolved;
this is a detached
limb assembly package. The assembly and housing notes reflect the documentation
available when the handoff was prepared.
''')
    for filename in ['hip-roll-bearing-options.md', 'paired-bearing-prototype-dfma.md']:
        shutil.copy2(TINFOX / 'design' / filename, target / 'reference-docs' / filename)
    capture = TINFOX / 'viewer/captures/paired-prototype-limb.png'
    if capture.exists():
        shutil.copy2(capture, target / 'assembled-limb-reference.png')
    source_manifest['handoff'] = {'prepared_utc': datetime.now(timezone.utc).isoformat(),
                                  'source_archive_sha256': release['archive_sha256'],
                                  'plates': plate_records, 'mesh_checks': part_checks,
                                  'sliced': False, 'printer_profile_selected': False}
    (target / 'manifest.json').write_text(json.dumps(source_manifest, indent=2))
    all_hashes = {str(path.relative_to(target)): sha(path) for path in sorted(target.rglob('*')) if path.is_file()}
    (target / 'SHA256SUMS').write_text(''.join(f'{value}  {name}\n' for name, value in all_hashes.items()))
    archive_path = target.with_suffix('.zip')
    with zipfile.ZipFile(archive_path, 'x', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(target.rglob('*')):
            if path.is_file():
                archive.write(path, str(Path(target.name) / path.relative_to(target)))
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
    report = {'package': str(target), 'archive': str(archive_path), 'archive_sha256': sha(archive_path),
              'archive_bytes': archive_path.stat().st_size, 'model_sha256': stamp,
              'limb_parts': len(part_checks), 'coupons': source_manifest['coupon_count'], 'plates': len(PLATES)}
    archive_path.with_suffix('.release.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
