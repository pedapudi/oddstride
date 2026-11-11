"""Publish an approved native low-profile robot without generating geometry."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import os
from pathlib import Path

from catalog_io import read_catalog, write_catalog

VIEWER = Path(__file__).resolve().parent
TINFOX = VIEWER.parent
NATIVE = TINFOX / 'proposals/sculpted/model/fusion_native'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def url(path):
    path = path.resolve()
    assert path.is_relative_to(TINFOX.resolve()) and path.is_file(), path
    return Path(os.path.relpath(path, VIEWER)).as_posix()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    assert manifest.get('native_source_of_truth') is True, 'Whole native authority is pending.'
    authority = json.loads((NATIVE/'manifests/source-authority.json').read_text())
    assert authority.get('full_robot_native_source_of_truth') is True, 'Whole-robot native authority has not passed its remaining gates.'
    approved = authority['canonical_scopes']['low_profile_robot']
    assert (NATIVE/approved['manifest']).resolve() == args.manifest.resolve()
    assert approved['manifest_sha256'] == sha(args.manifest.read_bytes())
    model_path = NATIVE / manifest['review_model']
    raw = model_path.read_bytes()
    if model_path.suffix == '.gz':
        raw = gzip.decompress(raw)
    identity = sha(raw)
    assert identity == manifest['review_model_sha256']
    model = json.loads(raw)
    assert model['parameters'] and model['poses']
    assert len({p['name'] for p in model['parts']}) == len(model['parts'])
    assert all(p['mesh'] in model['meshes'] for p in model['parts'])
    assert all(p.get('leg') in (None, 'FL', 'FR', 'RL', 'RR') for p in model['parts'])
    assert {p['leg'] for p in model['parts'] if p.get('leg')} == {'FL', 'FR', 'RL', 'RR'}
    names = {p['name'] for p in model['parts']}
    assert all(f'{leg}_{axis}_motor' in names for leg in ('FL', 'FR', 'RL', 'RR') for axis in ('roll', 'hip', 'knee'))
    assert all(not p.get('leg') or p['group'] in ('mount', 'roll', 'thigh', 'knee', 'crank', 'rod') for p in model['parts'])
    physical = [p for p in model['parts'] if p.get('service_role') not in ('keepout', 'withdrawal')]
    auxiliary = [p for p in model['parts'] if p.get('service_role') in ('keepout', 'withdrawal')]
    inventory = manifest['inventory']
    assert len(model['parts']) == inventory['review_records']
    assert len(physical) == inventory['visible_model_items']
    assert len(auxiliary) == inventory['hidden_auxiliary_envelopes'] == 1
    assert auxiliary[0]['name'] == 'electronics_clearance' and auxiliary[0].get('native_visible') is False
    parts = manifest['parts']
    assert isinstance(parts, dict) and parts
    used = Counter(p['mesh'] for p in model['parts'])
    assert set(parts).issubset(used), 'A canonical custom definition is absent from the review.'
    catalog = read_catalog(VIEWER)
    former = next(d for d in catalog['designs'] if d['id'] == 'v14')
    labels = {r['id']: r for r in former['parts']}
    rows = []
    for key, quantity in used.items():
        instances = [p for p in model['parts'] if p['mesh'] == key]
        first = instances[0]
        points = model['meshes'][key]['vertices']
        dimensions = [max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]
        reference_role = first.get('reference_role', '')
        native = parts.get(key)
        prior = labels.get(first.get('source_mesh_key', key), {})
        row = {'id': key, 'label': prior.get('label', first['name'].replace('_', ' ')),
               'instances': [p['name'] for p in instances], 'quantity': quantity,
               'custom': native is not None, 'material': first.get('material', 'envelope'),
               'category': prior.get('category', 'Legs' if native and first.get('leg') else 'Body' if native else 'Hardware'),
               'mass_kg': 0, 'dimensions_mm': dimensions,
               'note': 'Editable native Fusion definition. Manufacturing and operating qualification are recorded separately.' if native else 'Reference geometry; verify actual purchased parts. Display markings are nonmanufacturing references.' if reference_role == 'nonmanufacturing_display_reference' else 'Purchased hardware or equipment envelope reference; verify the actual part.'}
        if reference_role.startswith('provisional_'):
            row['note'] = first.get('note') or 'Provisional equipment envelope. Its manufactured part and supplier remain unselected.'
        if first.get('service_role') in ('keepout', 'withdrawal'):
            assert native is None, key
            row.update(category='Sensors and wiring', note='Nonphysical electronics clearance envelope. Optional inspection reference; excluded from fabrication and physical motion checks.')
        if native:
            assert native.get('saved_version'), key
            step = NATIVE / native['native_step']
            assert sha(step.read_bytes()) == native['native_step_sha256'], key
            row['step'] = url(step)
        rows.append(row)
    audit_path = VIEWER/'checks/native-robot-review.json'
    audit_path.write_text(json.dumps({'model_sha256': identity, 'motion_samples': [],
        'native_source_manifest': url(args.manifest),
        'scope': 'Native low-profile robot geometry. Each custom pose requires a live check; recorded migration and physical limitations remain separate.'}, indent=2)+'\n')
    design = {'id': 'native-low-profile', 'title': 'Native Fusion · low-profile Tinfox',
        'description': 'Current low-profile robot assembled from editable native Fusion parts. Inspect the complete robot, joint poses, sections and individual parts.',
        'model': url(model_path), 'model_sha256': identity, 'audit': url(audit_path),
        'assembly': None, 'estimated_mass_kg': None, 'physical_components': len(physical),
        'auxiliary_components': len(auxiliary), 'review_records': len(model['parts']),
        'scope_label': 'Whole low-profile robot', 'presentation': 'whole-robot',
        'scope': 'Canonical native low-profile CAD. Known source contacts and joint-range limitations remain documented; physical strength, tolerances, cables and loaded locomotion are unqualified.',
        'motion_available': True, 'live_check_available': True, 'default_focus': 'all',
        'clearance_scope': 'motion-only',
        'archived': False, 'lifecycle': 'current-review',
        'source': {'kind': 'fusion-native', 'label': 'Native Fusion · canonical low-profile robot',
                   'manifest': url(args.manifest), 'manifest_sha256': sha(args.manifest.read_bytes())},
        'reports': [{'title': 'Native source and validation evidence', 'url': url(args.manifest)},
                    {'title': 'CAD authority scopes', 'url': url(NATIVE/'manifests/source-authority.json')}],
        'parts': sorted(rows, key=lambda row: (not row['custom'], row['label']))}
    catalog['designs'] = [d for d in catalog['designs'] if d['id'] != design['id']]
    for old in catalog['designs']:
        if old['id'] == 'native-motor-complex':
            old.update(archived=False, lifecycle='fit-subassembly', defer_details=True)
        elif not old.get('archived'):
            old.update(archived=True, lifecycle='archived', defer_details=True)
    catalog['designs'].insert(0, design)
    catalog['current_design'] = design['id']
    write_catalog(VIEWER, catalog)
    print(json.dumps({'current_design': design['id'], 'components': len(model['parts']),
                      'native_export_entries': len(parts), 'model_sha256': identity}))


if __name__ == '__main__':
    main()
