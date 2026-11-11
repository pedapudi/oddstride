"""Stage a detached, unpowered three-RS02 assembly with accessible screw entries."""
import hashlib
import json
import math
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps

from export_closed_mesh import closed_mesh
from prepare_mac_print_package import arrange, write_3mf
from slim_limb import extrusion, lobed_wire
from cad_authority import require_generated_authority


ROOT = Path(__file__).resolve().parent
TINFOX = ROOT.parents[2]
SOURCE = ROOT / 'output/paired-roll-work/prototype-limb'
KNEE_SOURCE = ROOT / 'fusion_native/snapshots/knee-stub-cleanup/thigh_outer.step'
PLATES = [
    ('01-roll-and-hip-carrier', ['motor_carrier_1', 'hip_stator_closure_1', 'roll_cartridge_1',
                               'roll_stator_backplate_1', 'roll_outer_retainer_1', 'roll_inner_backplate_1',
                               'roll_inner_spacer_1', 'roll_outer_spacer_1']),
    ('02-thigh-motor-housing', ['thigh_inner', 'thigh_outer']),
    ('03-motor-flanges-and-crank', ['hip_hub', 'motor_mount_ring', 'input_crank']),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def volume(shape):
    props = GProp_GProps()
    BRepGProp.VolumePropertiesGK_s(shape.wrapped, props, 1e-9, True, True)
    return props.Mass()


def cylinder(radius, y0, y1, x=0, z=0):
    return cq.Solid.makeCylinder(radius, y1-y0, cq.Vector(x, y0, z), cq.Vector(0, 1, 0))


def orient(mesh, axis, degrees):
    result = mesh.copy()
    result.apply_transform(trimesh.transformations.rotation_matrix(math.radians(degrees), axis))
    bounds = result.bounds
    result.apply_translation([-(bounds[0, 0]+bounds[1, 0])/2, -(bounds[0, 1]+bounds[1, 1])/2, -bounds[0, 2]])
    return result


def export_print(shape, key, target, axis, degrees):
    assert shape.isValid() and len(shape.Solids()) == 1, key
    step = target / 'reference-step' / f'{key}.step'
    cq.exporters.export(shape, str(step))
    reopened = cq.importers.importStep(str(step)).val()
    assert reopened.isValid() and len(reopened.Solids()) == 1
    with tempfile.TemporaryDirectory(prefix='tinfox-complex-') as temporary:
        stl = Path(temporary) / f'{key}.stl'
        cq.exporters.export(shape, str(stl), tolerance=.02, angularTolerance=.08)
        mesh, check = closed_mesh(step, stl, volume(shape))
    mesh = orient(mesh, axis, degrees)
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0
    mesh.export(target / 'individual-stl' / f'{key}.stl')
    single = mesh.copy()
    single.apply_translation([162.5, 160, 0])
    write_3mf(target / 'individual-3mf' / f'{key}.3mf', [(key, single)])
    return mesh, check


def main():
    require_generated_authority(ROOT)
    source = json.loads((SOURCE / 'manifest.json').read_text())
    name = f'Tinfox-Motor-Complex-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}'
    target = ROOT / 'output/print-handoff' / name
    target.mkdir(exist_ok=False, parents=True)
    for folder in ['plates', 'individual-stl', 'individual-3mf', 'reference-step', 'checks']:
        (target / folder).mkdir()
    meshes = {}
    corrections = []
    records = []
    required = [key for _, keys in PLATES for key in keys]
    assert len(required) == len(set(required)) == 13
    for key in required:
        record = next(p for p in source['parts'] if p['part'] == key)
        assert sha(SOURCE / record['print_stl']) == record['stl_sha256'], key
        if key in ['thigh_outer', 'input_crank']:
            original_file = KNEE_SOURCE if key == 'thigh_outer' else ROOT / 'output/integrated-candidate/step/input_crank.step'
            before = cq.importers.importStep(str(original_file)).val()
            if key == 'input_crank':
                model = json.loads((ROOT / 'output/paired-roll-work/model.json').read_text())
                expected_volume = next(p['volume_mm3'] for p in model['parts'] if p['name'] == 'FL_input_crank')
                assert abs(volume(before) - expected_volume) < .01
            shape = before
            if key == 'thigh_outer':
                assert sha(KNEE_SOURCE) == '444e1937618b2f33438fbc0684d8eedcad4b366b791220c9fcfe778d1a02c0e2'
                for angle in [90, 210, 330]:
                    x = 43.5*math.cos(math.radians(angle)); z = 43.5*math.sin(math.radians(angle))
                    shape = shape.cut(cylinder(3.2, 61, 110, x, z))
                shape = shape.cut(extrusion(lobed_wire(40.8, 4.8, -5), 60.2))
                operation = ('Three straight diameter6.4 mm socket-head/driver channels, Y61..110, radius43.5 mm at90/210/330 degrees. '
                             'Inboard stator-plate silhouette passage, coreR40.8/lobeR4.8, Y-5..55.2. '
                             'Includes prior0.6 mm knee-stub removal.')
            else:
                for angle in range(0, 360, 60):
                    x = 12*math.cos(math.radians(angle)); z = 12*math.sin(math.radians(angle))
                    shape = shape.cut(cylinder(4, 61, 90, x, z))
                operation = 'Six diameter8 mm output-screw head counterbores opened through the arm, Y61..90; original Y61 seating plane preserved.'
            shape = shape.clean()
            mesh, mesh_check = export_print(shape, key, target, record['rotation_axis'], record['rotation_deg'])
            corrections.append({'part': key, 'input_step_sha256': sha(original_file),
                                'output_step_sha256': sha(target / 'reference-step' / f'{key}.step'),
                                'operation': operation, 'removed_volume_mm3': volume(before)-volume(shape),
                                'mesh_check': mesh_check})
        else:
            mesh = trimesh.load_mesh(SOURCE / record['print_stl'], process=True)
            assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0
            shutil.copy2(SOURCE / record['print_stl'], target / 'individual-stl' / f'{key}.stl')
            shutil.copy2(SOURCE / record['print_3mf'], target / 'individual-3mf' / f'{key}.3mf')
            shutil.copy2(SOURCE / 'reference-step' / f'{key}.step', target / 'reference-step' / f'{key}.step')
        meshes[key] = mesh
        records.append({'part': key, 'quantity': 1, 'bounds_mm': mesh.extents.tolist(),
                        'stl_sha256': sha(target / 'individual-stl' / f'{key}.stl'),
                        'corrected': key in ['thigh_outer', 'input_crank']})
        print('Prepared', key, flush=True)
    # Optional spacing surrogates allow a light, unpowered dry fit before metal
    # tubes are cut. They are not operating compression sleeves.
    spacer_keys = []
    for family, outside, inside, length, count in [('pod-long', 5, 3.4, 41, 3),
                                                  ('pod-short', 5, 3.4, 6, 3),
                                                  ('thigh-clamp', 8, 4.3, 18, 2)]:
        shape = cylinder(outside/2, 0, length).cut(cylinder(inside/2, -1, length+1))
        key = f'fit-only-{family}-sleeve'
        mesh, _ = export_print(shape, key, target, [1, 0, 0], 90)
        meshes[key] = mesh
        for i in range(1, count+1):
            spacer_keys.append(f'{key}-{i}')
            meshes[spacer_keys[-1]] = mesh
        records.append({'part': key, 'quantity': count, 'outside_mm': outside, 'inside_mm': inside,
                        'length_mm': length, 'status': 'Optional printed spacing surrogate; finger-tight bench fit only.'})
    plate_records = []
    for name_, keys in [*PLATES, ('04-optional-fit-only-sleeves', spacer_keys)]:
        placed = arrange([(key, meshes[key]) for key in keys])
        filename = target / 'plates' / f'{name_}.3mf'
        write_3mf(filename, placed)
        plate_records.append({'file': str(filename.relative_to(target)), 'objects': keys,
                              'bounds_mm': {key: mesh.bounds.tolist() for key, mesh in placed}})
    (target / 'geometry-corrections.json').write_text(json.dumps(corrections, indent=2))
    # Keep original reports labelled by scope. They do not certify the corrected
    # parts; the accompanying independent access checks cover those deltas.
    for filename in ['paired-roll-interfaces.json', 'independent-service.json']:
        path = SOURCE / 'checks' / filename
        if path.exists():
            shutil.copy2(path, target / 'checks' / ('base-' + filename))
    (target / 'manifest.json').write_text(json.dumps({'source_model_sha256': source['model_sha256'],
        'units': 'mm', 'parts': records, 'plates': plate_records, 'limb_components': 13,
        'optional_spacing_surrogates': 8, 'motor_count_required': 3, 'sliced': False,
        'scope': 'Detached, supported and unpowered motor-complex fit assembly. Current hardware and physical fit require confirmation.'}, indent=2))
    capture = TINFOX / 'viewer/captures/three-actuators.png'
    if capture.exists():
        shutil.copy2(capture, target / 'three-motors-reference.png')
    print(json.dumps({'directory': str(target), 'corrections': corrections}), flush=True)


if __name__ == '__main__':
    main()
