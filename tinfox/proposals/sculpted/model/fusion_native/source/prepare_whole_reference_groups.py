"""Export grouped exact purchased references for the current native assembly.

Custom parts and native cut-stock definitions are excluded. Proximal hardware
comes from the audited native bench STEP, not from tessellated geometry.
Remaining references come from the frozen generated source's exact STEP files.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path

import cadquery as cq
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
H = ROOT.parents[3] / 'analysis/dfma/knee-stator-seats'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk(node, location=None, prefix=''):
    location = (location or cq.Location()) * node.loc
    prefix += '/' + node.name
    for shape in node.shapes:
        for solid in shape.Solids():
            yield prefix, solid.moved(location)
    for child in node.children:
        yield from walk(child, location, prefix)


def bounds(shape):
    b = shape.BoundingBox()
    return np.array([b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax])


def validate(shape, mesh):
    points = np.asarray(mesh['vertices'])
    expected = np.r_[points.min(axis=0), points.max(axis=0)]
    be = float(np.max(np.abs(bounds(shape) - expected)))
    boundary = cq.Compound.makeCompound(shape.Faces())
    # Exact surfaces are compared with every frozen tessellation vertex.
    error = max(boundary.distance(cq.Vertex.makeVertex(*p)) for p in points)
    assert be < .01 and error < .002, (be, error)
    assert shape.isValid() and len(shape.Solids()) >= 1
    return {'bounds_error_mm': be, 'all_mesh_vertices_boundary_error_mm': error,
            'vertices_checked': len(points), 'valid_solid_count': len(shape.Solids())}


def main():
    target_path = ROOT / 'manifests/whole-robot-integration-target.json'
    target = json.loads(target_path.read_text())
    raw = gzip.decompress((ROOT / target['reference_model']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == target['model_sha256']
    model = json.loads(raw)
    custom = set(json.loads((ROOT / 'manifests/whole-native-component-map-candidate.json').read_text())['parts'])
    authority_path = ROOT / 'manifests/motor-complex-native-exports.json'
    authority = json.loads(authority_path.read_text())
    assert sha(authority_path) == target['native_bench_manifest_sha256']
    bench = json.loads(gzip.decompress((ROOT / authority['review_model']).read_bytes()))
    screen_path = H / 'native-bench-static-screen.json'
    screen = json.loads(screen_path.read_text())
    bench_step = ROOT / 'exports/motor-complex-leg23-native/assembled-motor-complex.step'
    assert sha(bench_step) == screen['step']['sha256']
    leaves = list(walk(cq.Assembly.load(str(bench_step))))
    assert len(leaves) == 121
    bindings = {x['inventory']['path']: x for x in screen['identity_binding']}
    native_shapes = {}
    for part in bench['parts']:
        if part['reference_role'] in ('custom_structure', 'cut_stock'):
            continue
        binding = bindings[part['native_path']]
        label, solid = leaves[binding['source_solid_index']]
        assert label == binding['step_label']
        assert np.max(np.abs(bounds(solid) - binding['step_bounds_mm'])) < 1e-6
        native_shapes[part['name']] = solid
    assert len(native_shapes) == 100
    mappings = {x['instance']: x for x in target['instance_mappings'] if 'bench_instance' in x}
    source_folder = ROOT / 'snapshots/paired-bearing-target' / target['generated_whole_reference_sha256'] / 'step'
    # Newly introduced ordinary hardware has explicit reviewed specifications.
    # These keys were absent from the earlier hardware-only allowlist.
    ordinary = {x['key'] for x in json.loads((ROOT / 'manifests/current-hardware-references.json').read_text())['variants']['low']['reference_meshes']}
    previous_exact = {x['key']: x for x in json.loads((ROOT / 'manifests/current-exact-hardware-references.json').read_text())['parts']}
    additions = {f'body_service_screw_{s}_{y}_18' for s in (-1, 1) for y in (-64, 64)}
    additions |= {f'shin_clamp_washer_{z}_{side}{hand}' for z in (37, 105) for side in ('inner', 'outer') for hand in ('', '_right')}
    additions |= {f'axle_washer_{side}{hand}' for side in ('inner', 'outer') for hand in ('', '_right')}
    output = ROOT / 'snapshots/whole-purchased-reference-groups' / target['model_sha256']
    if output.exists():
        assert not any(output.iterdir()), 'Preserve an existing completed reference batch.'
    else:
        output.mkdir(parents=True)
    groups, rows, excluded = {}, [], []
    cache = {}
    for part in model['parts']:
        key = part['mesh']
        if part.get('service_role') in ('keepout', 'withdrawal') or key in custom or key.startswith('bench_stock_'):
            excluded.append(part['name'])
            continue
        name = part['name']
        if name in mappings:
            mapping = mappings[name]
            shape = native_shapes[mapping['bench_instance']]
            if mapping['roll_axis_x_reflection']:
                shape = shape.mirror('YZ')
            if mapping['handed_y_reflection']:
                shape = shape.mirror('XZ')
            shape = shape.translate(tuple(mapping['neutral_to_group_translation_mm']))
            provenance = {'source': str(bench_step.relative_to(ROOT)), 'source_sha256': sha(bench_step),
                          'bench_instance': mapping['bench_instance'], 'mapping': mapping}
        else:
            assert key in ordinary | additions, ('Unreviewed reference classification', name, key)
            path = source_folder / (key + '.step')
            if not path.exists():
                generated = ROOT.parent / 'output/paired-roll-work/step' / (key + '.step')
                if generated.exists():
                    path = generated
            if not path.exists() and key in previous_exact:
                prior = previous_exact[key]
                path = ROOT / prior['path']
                assert sha(path) == prior['sha256']
            assert path.exists(), ('Missing exact source STEP', path)
            if key not in cache:
                cache[key] = cq.importers.importStep(str(path)).val()
            shape = cache[key]
            provenance = {'source': os.path.relpath(path, ROOT), 'source_sha256': sha(path)}
            points = np.asarray(model['meshes'][key]['vertices'])
            wanted_bounds = np.r_[points.min(axis=0), points.max(axis=0)]
            source_bounds = bounds(shape)
            if np.max(np.abs(wanted_bounds - source_bounds)) >= .01:
                # Earlier exact hardware can retain an older local placement.
                # Accept only a translation with unchanged extents, followed by
                # the complete current-vertex boundary comparison below.
                assert np.max(np.abs((wanted_bounds[3:] - wanted_bounds[:3]) -
                                     (source_bounds[3:] - source_bounds[:3]))) < .01, name
                offset = ((wanted_bounds[:3] - source_bounds[:3]) +
                          (wanted_bounds[3:] - source_bounds[3:])) / 2
                shape = shape.translate(tuple(offset))
                provenance['current_local_placement_translation_mm'] = offset.tolist()
        try:
            check = validate(shape, model['meshes'][key])
        except AssertionError as error:
            raise AssertionError((name, key, provenance, error.args)) from error
        group = (part.get('leg') or 'Body') + '_' + part['group']
        groups.setdefault(group, cq.Assembly(name=group + ' purchased references')).add(shape, name=name)
        display = 'wordmark' in name or 'marking' in name or name == 'body_serial'
        rows.append({'name': name, 'mesh': key, 'group': group, 'source': provenance,
                     'reference_role': 'nonmanufacturing_display_reference' if display else 'purchased_hardware_or_equipment_envelope',
                     'bounds_mm': bounds(shape).tolist(), 'volume_mm3': shape.Volume(),
                     'geometry_comparison': check, 'custom_part': False})
        if len(rows) % 50 == 0:
            print(json.dumps({'checked': len(rows), 'last': name}), flush=True)
    assert len([r for r in rows if r['name'] in mappings]) == 400
    group_records = []
    for key, assembly in groups.items():
        path = output / (key + '-reference-assembly.step')
        assembly.save(str(path))
        expected = [r for r in rows if r['group'] == key]
        recovered = list(walk(cq.Assembly.load(str(path))))
        assert len(recovered) == sum(r['geometry_comparison']['valid_solid_count'] for r in expected)
        expected_names = [r['name'] for r in expected for _ in range(r['geometry_comparison']['valid_solid_count'])]
        assert sorted(p.rsplit('/', 1)[-1] for p, s in recovered) == sorted(expected_names)
        for record in expected:
            solids = [shape for label, shape in recovered if label.rsplit('/', 1)[-1] == record['name']]
            assert np.max(np.abs(bounds(cq.Compound.makeCompound(solids)) - record['bounds_mm'])) < .0001
        group_records.append({'group': key, 'path': str(path.relative_to(ROOT)),
                              'sha256': sha(path), 'instances': len(expected),
                              'solid_count': len(recovered),
                              'names': [r['name'] for r in expected], 'roundtrip_passed': True})
    result = {'passed': True, 'source_model_sha256': target['model_sha256'],
              'source_target_manifest_sha256': sha(target_path),
              'bench_manifest_sha256': sha(authority_path), 'groups': group_records,
              'instances': len(rows), 'parts': rows, 'excluded_instances': excluded,
              'native_proximal_purchased_instances': 400, 'custom_import_count': 0,
              'scope': 'Exact standard hardware, motors, connectors and equipment envelopes only. Coordinates are local to each recorded kinematic frame. Native custom and cut-stock definitions and nonphysical reservations are excluded. Imported child solids may be flattened into separately named reference bodies.',
              'limitations': 'Geometry comparison does not verify supplier stock, actual purchased dimensions, thread fit or flexible cable behavior.'}
    encoded = json.dumps(result, indent=2) + '\n'
    (output / 'manifest.json').write_text(encoded)
    (ROOT / 'manifests/whole-purchased-reference-groups.json').write_text(encoded)
    print(json.dumps({'passed': True, 'instances': len(rows), 'groups': len(groups), 'directory': str(output)}), flush=True)


if __name__ == '__main__':
    main()
