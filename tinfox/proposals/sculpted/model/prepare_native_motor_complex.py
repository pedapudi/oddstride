"""Prepare print plates from approved saved Fusion exports without rebuilding CAD."""
import argparse
import csv
import hashlib
import json
import math
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import cadquery as cq
import numpy as np
import trimesh
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from prepare_mac_print_package import arrange, write_3mf

ROOT = Path(__file__).resolve().parent
TINFOX = ROOT.parents[2]
NATIVE = ROOT / 'fusion_native'
CORE = '{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
PLATES = [
    ('01-roll-and-hip-carrier', ['motor_carrier_1', 'hip_stator_closure_1', 'roll_cartridge_1',
      'roll_stator_backplate_1', 'roll_outer_retainer_1', 'roll_inner_backplate_1',
      'roll_inner_spacer_1', 'roll_outer_spacer_1']),
    ('02-thigh-motor-housing', ['thigh_inner', 'thigh_outer']),
    ('03-motor-flanges-and-crank', ['hip_hub', 'motor_mount_ring', 'input_crank'])]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_file(relative, expected):
    path = (NATIVE / relative).resolve()
    assert path.is_relative_to(NATIVE.resolve()) and path.is_file(), relative
    assert sha(path) == expected, ('Native export hash mismatch', relative)
    return path


def read_3mf(path):
    """Read ordinary native component meshes, units and all build transforms."""
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        candidates = [name for name in archive.namelist() if name.lower().endswith('.model')]
        assert len(candidates) == 1, 'External 3MF resource graphs require explicit support.'
        root = ET.fromstring(archive.read(candidates[0]))
    scale = {'micron': .001, 'millimeter': 1, 'centimeter': 10, 'inch': 25.4,
             'foot': 304.8, 'meter': 1000}[root.attrib.get('unit', 'millimeter')]
    objects = {obj.attrib['id']: obj for obj in root.find(CORE+'resources').findall(CORE+'object')}

    def transform(text):
        matrix = np.eye(4)
        if text:
            values = [float(v) for v in text.split()]
            assert len(values) == 12
            matrix[:3, :] = np.array(values).reshape(4, 3).T
        return matrix

    def meshes(key, parent, ancestors):
        assert key not in ancestors, 'Cyclic 3MF component graph'
        obj = objects[key]
        geometry = obj.find(CORE+'mesh')
        if geometry is not None:
            vertices = [[float(v.attrib[a]) for a in ['x', 'y', 'z']]
                        for v in geometry.find(CORE+'vertices')]
            faces = [[int(f.attrib[a]) for a in ['v1', 'v2', 'v3']]
                     for f in geometry.find(CORE+'triangles')]
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
            mesh.apply_transform(parent)
            return [mesh]
        components = obj.find(CORE+'components')
        assert components is not None, key
        return [mesh for item in components for mesh in meshes(item.attrib['objectid'],
                parent @ transform(item.attrib.get('transform')), {*ancestors, key})]

    result = trimesh.util.concatenate([mesh for item in root.find(CORE+'build')
        for mesh in meshes(item.attrib['objectid'], transform(item.attrib.get('transform')), set())])
    result.apply_scale(scale)
    result.merge_vertices(digits_vertex=7)
    assert result.is_watertight and result.is_winding_consistent and result.volume > 0, path
    return result


def oriented(mesh, axis, degrees):
    result = mesh.copy()
    matrix = trimesh.transformations.rotation_matrix(math.radians(degrees), axis)
    result.apply_transform(matrix)
    delta = [-(result.bounds[0, 0]+result.bounds[1, 0])/2,
             -(result.bounds[0, 1]+result.bounds[1, 1])/2, -result.bounds[0, 2]]
    result.apply_translation(delta)
    matrix[:3, 3] = delta
    return result, matrix


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=NATIVE/'manifests/motor-complex-native-exports.json')
    parser.add_argument('--validate-only', action='store_true', help='Check candidate exports without preparing a release.')
    args = parser.parse_args()
    authority = json.loads(args.manifest.read_text())
    integrated = authority.get('assembly_architecture') == 'integrated-dfma'
    assert authority['native_source_of_truth'] is True or args.validate_only, 'Native promotion is not approved.'
    assert args.validate_only or authority.get('assembly_release_ready') is True, 'Complete assembly print release is withheld.'
    plates_to_prepare = [(name, [key for key in parts if key in authority['parts']])
                         for name, parts in PLATES]
    plates_to_prepare = [(name, parts) for name, parts in plates_to_prepare if parts]
    keys = [key for _, parts in plates_to_prepare for key in parts]
    assert set(keys) == set(authority['parts']) and len(keys) == (10 if integrated else 13)
    if integrated:
        assert not {'hip_hub', 'motor_mount_ring', 'hip_stator_closure_1'} & set(keys)
        assert {'thigh_inner', 'thigh_outer', 'motor_carrier_1'}.issubset(
            authority.get('print_orientation_overrides', {})), 'Review orientations for the integrated motor parts.'
    orientation = json.loads((ROOT/'output/paired-roll-work/prototype-limb/manifest.json').read_text())
    orientations = {part['part']: part for part in orientation['parts']}
    staged = []
    for key in keys:
        record = authority['parts'][key]
        assert record.get('saved_version'), ('Unsaved native source', key)
        step = source_file(record['native_step'], record['native_step_sha256'])
        three_mf = source_file(record['native_3mf'], record['native_3mf_sha256'])
        mesh = read_3mf(three_mf)
        solid = cq.importers.importStep(str(step)).val()
        assert solid.isValid() and len(solid.Solids()) == 1, key
        bb = solid.BoundingBox()
        assert np.allclose(mesh.bounds, [[bb.xmin,bb.ymin,bb.zmin],[bb.xmax,bb.ymax,bb.zmax]],atol=.05), key
        props = GProp_GProps()
        BRepGProp.VolumePropertiesGK_s(solid.wrapped, props, 1e-9, True, True)
        volume_error = abs(mesh.volume-props.Mass())/props.Mass()
        assert volume_error < .005, (key, volume_error)
        recipe = orientations[key]
        recipe = {**recipe, **authority.get('print_orientation_overrides',{}).get(key,{})}
        print_mesh, matrix = oriented(mesh, recipe['rotation_axis'], recipe['rotation_deg'])
        staged.append((key, step, three_mf, print_mesh, matrix, volume_error, record))
    if args.validate_only:
        print(json.dumps({'candidate_validation_passed':True,'release_prepared':False,
            'parts':[{'part':key,'native_step_sha256':sha(step),'native_3mf_sha256':sha(three_mf),
                      'mesh_volume_relative_error':error,'print_bounds_mm':mesh.extents.tolist()}
                     for key,step,three_mf,mesh,matrix,error,source in staged]},indent=2))
        return
    label = f'Tinfox-Native-Motor-Complex-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}'
    target = ROOT/'output/print-handoff'/label
    target.mkdir(parents=True, exist_ok=False)
    for directory in ['native-3mf', 'reference-step', 'individual-stl', 'individual-3mf', 'plates', 'checks']:
        (target/directory).mkdir()
    records, meshes = [], {}
    for key, step, three_mf, mesh, matrix, volume_error, source in staged:
        shutil.copy2(step, target/'reference-step'/f'{key}.step')
        shutil.copy2(three_mf, target/'native-3mf'/f'{key}.3mf')
        mesh.export(target/'individual-stl'/f'{key}.stl')
        single = mesh.copy(); single.apply_translation([162.5,160,0])
        write_3mf(target/'individual-3mf'/f'{key}.3mf', [(key,single)])
        meshes[key] = mesh
        records.append({'part':key,'quantity':1,'source':source,
            'print_transform_mm':matrix.tolist(),'bounds_mm':mesh.extents.tolist(),
            'native_3mf_step_volume_relative_error':volume_error})
    plates = []
    for name, parts in plates_to_prepare:
        placed = arrange([(key,meshes[key]) for key in parts])
        write_3mf(target/'plates'/f'{name}.3mf',placed)
        plates.append({'file':f'plates/{name}.3mf','objects':parts,
                       'bounds_mm':{key:mesh.bounds.tolist() for key,mesh in placed}})
    optional = authority.get('stock_references', [])
    if optional:
        assert len(optional) == (2 if integrated else 3)
        assert sum(record['quantity'] for record in optional) == (6 if integrated else 8)
        stock_items = []
        for record in optional:
            key = record['part']
            source = source_file(record['native_3mf'], record['native_3mf_sha256'])
            raw_mesh = read_3mf(source)
            outside, inside, length = record['nominal_od_id_length_mm']
            assert np.allclose(raw_mesh.extents, [outside,length,outside], atol=.05)
            expected_volume = math.pi*(outside**2-inside**2)*length/4
            assert abs(raw_mesh.volume-expected_volume)/expected_volume < .005
            mesh, matrix = oriented(raw_mesh,[1,0,0],90)
            shutil.copy2(source,target/'native-3mf'/f'{key}.3mf')
            mesh.export(target/'individual-stl'/f'{key}.stl')
            single = mesh.copy();single.apply_translation([162.5,160,0])
            write_3mf(target/'individual-3mf'/f'{key}.3mf',[(key,single)])
            stock_items.extend((f'{key}-{i+1}',mesh) for i in range(record['quantity']))
            records.append({'part':key,'quantity':record['quantity'],'source':record,
                'print_transform_mm':matrix.tolist(),'bounds_mm':mesh.extents.tolist(),
                'status':'Optional printed dimensional surrogate; finger-tight unpowered fit only.'})
        placed = arrange(stock_items)
        write_3mf(target/'plates/04-optional-fit-only-sleeves.3mf',placed)
        plates.append({'file':'plates/04-optional-fit-only-sleeves.3mf',
                       'objects':[key for key,_ in placed],
                       'bounds_mm':{key:mesh.bounds.tolist() for key,mesh in placed}})
    shutil.copy2(args.manifest,target/'native-source-manifest.json')
    guide = TINFOX/'design'/('integrated-motor-complex-fit.md' if integrated else 'motor-complex-fit.md')
    text = guide.read_text().replace(
        'Its export source is generated CAD. Native Fusion features and native-derived\n'
        'print exports remain under review; these 3MF files are not Fusion exports.',
        'This package derives from the saved, audited native Fusion motor complex.\n'
        'Its source manifest records native export hashes and saved document versions.')
    text = text.replace('../analysis/dfma/knee-stator-seats/static-screen-review.md',
                        'checks/static-screen-review.md')
    (target/'ASSEMBLY.md').write_text(text)
    if integrated:
        for check in authority['checks']:
            source = source_file(check['path'], check['sha256'])
            shutil.copy2(source, target/'checks'/source.name)
        hardware = [dict(item) for item in authority['hardware']]
    else:
        static_review = TINFOX/'analysis/dfma/knee-stator-seats'
        for name in ['static-screen-review.md', 'native-bench-static-classification.json', 'native-bench-static-screen.json']:
            shutil.copy2(static_review/name, target/'checks'/name)
        audit = TINFOX/'analysis/dfma/motor-complex-fit/release-report.json'
        shutil.copy2(audit,target/'checks/reference-assembly-access.json')
        hardware = json.loads(audit.read_text())['hardware']
    if authority.get('assembly_step'):
        assembly_step = source_file(authority['assembly_step'], authority['assembly_step_sha256'])
        shutil.copy2(assembly_step, target/'checks/assembled-native-reference.step')
    for override in authority.get('hardware_overrides',[]):
        matches=[item for item in hardware if item['item']==override['item']]
        assert len(matches)==1,override['item']
        matches[0].update(override)
    stock = {item['part']: item for item in authority['stock_references']}
    clamp_stock = stock['fit-only-thigh-clamp-sleeve']
    clamp_od, clamp_id, clamp_length = clamp_stock['nominal_od_id_length_mm']
    clamp_specification = f'Metal tube, {clamp_od:g} mm OD / {clamp_id:g} mm ID, {clamp_length:g} mm length'
    clamp_rows = [item for item in hardware if item['item'] == 'Thigh clamp compression tubes']
    assert len(clamp_rows) == 1
    clamp_rows[0].update(specification=clamp_specification, quantity=clamp_stock['quantity'])
    with (target/'hardware.csv').open('w',newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Connection','Specification','Quantity / screws','Nuts','Washers','Physical checks remaining'])
        for item in hardware:
            specification = item['specification']
            if item['item'] == 'Two structural thigh clamps':
                specification += f'; sleeve OD {clamp_od:g} mm, ID {clamp_id:g} mm, length {clamp_length:g} mm, matching native stock reference'
            writer.writerow([item['item'],specification,item.get('quantity',''),
                item.get('nut_quantity',''),item.get('washer_quantity',''),item.get('remaining_physical_checks','')])
    readme = '''# Native three-motor fit assembly

These thirteen custom parts come from the saved, audited native Fusion motor
complex. The source manifest records document versions and export hashes.
The native 3MF files preserve CAD coordinates; the prepared plates apply only
recorded rigid print transforms. No custom CAD is rebuilt for this package.

Open the files in `plates/` in Bambu Studio. They are unsliced. Select the actual
H2D, nozzle and filament, review supports and layers, and preserve scale and
orientation. This package is for a detached, supported, unpowered fit assembly.
It does not qualify printed strength or powered operation.

The prepared layouts use the H2D single-nozzle envelope, 325 × 320 × 325 mm.
Dual-nozzle mode has a narrower 300 mm envelope; rearrange the objects in Bambu
Studio if using that mode. See the [manufacturer specifications](https://cdn1.bambulab.com/documentation/h2d/en/H2D_Laser_Full_Combo_20250305.pdf).

Read `ASSEMBLY.md` and `hardware.csv` before assembly. Install motor stator and
output screws in the specified order before enclosing the thigh. Use metal
compression sleeves for operation. Any optional printed sleeve plate contains
finger-tight dimensional surrogates only.

The [static assembly review](checks/static-screen-review.md) and its linked
reports are included. `checks/assembled-native-reference.step` is the exact
121-body reference used by that screen; its hash is recorded in the native
source manifest. This STEP is an assembly reference rather than a print plate.
'''
    if integrated:
        readme = readme.replace('These thirteen custom parts', 'These ten custom parts')
        readme = readme[:readme.index('The [static assembly review]')] + (
            'The native source manifest and focused assembly checks are included in\n'
            '`checks/`. Read their scope before assembly. Printed material strength,\n'
            'bearing fits and preload retention require physical qualification.\n')
    (target/'README.md').write_text(readme)
    manifest = {'source_kind':'fusion-native','source_manifest_sha256':sha(args.manifest),
        'source_manifest_relative':str(args.manifest.resolve().relative_to(NATIVE.resolve())),
        'units':'mm','motor_count_required':3,'limb_components':len(keys),'sliced':False,
        'layout_bed_mm':[325,320,325],'layout_nozzle_mode':'single',
        'hardware_overrides':authority.get('hardware_overrides',[]),
        'print_orientation_overrides':authority.get('print_orientation_overrides',{}),
        'parts':records,'plates':plates,'scope':'Detached supported unpowered fit assembly only.'}
    (target/'manifest.json').write_text(json.dumps(manifest,indent=2))
    hashes = {str(p.relative_to(target)):sha(p) for p in sorted(target.rglob('*')) if p.is_file()}
    (target/'SHA256SUMS').write_text(''.join(f'{value}  {name}\n' for name,value in hashes.items()))
    archive = target.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(target.rglob('*')):
            if path.is_file():z.write(path,path.relative_to(target.parent))
    print(json.dumps({'directory':str(target),'archive':str(archive),'archive_sha256':sha(archive)},indent=2))


if __name__ == '__main__':
    main()
