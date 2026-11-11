"""Freeze both current robot variants for native migration comparison.

STEP and mesh files are immutable audit references, never Fusion authoring inputs.
The original conversion manifest remains intact until a replacement is qualified.
"""
import datetime
import gzip
import hashlib
import json
import shutil
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]
MODEL = NATIVE.parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def freeze():
    original = json.loads((NATIVE / 'manifests/parts.json').read_text())
    custom = {p['id'] for p in original['parts']}
    targets = {}
    for variant, folder in [('low', 'limb-refinement'), ('high', 'shoulder-head-prototype')]:
        source = MODEL / 'output' / folder
        raw = (source / 'model.json').read_bytes()
        model = json.loads(raw)
        identity = sha(raw)
        dest = NATIVE / 'snapshots/current-targets' / identity
        dest.mkdir(parents=True, exist_ok=True)
        frozen = dest / 'model.json.gz'
        if frozen.exists():
            assert gzip.decompress(frozen.read_bytes()) == raw
        else:
            frozen.write_bytes(gzip.compress(raw, mtime=0))
        rows = {}
        for instance in model['parts']:
            key = instance['mesh']
            if key not in custom and instance['material'] not in ['petg', 'rubber', 'aluminum']:
                continue
            if key not in rows:
                mesh = json.dumps(model['meshes'][key], sort_keys=True, separators=(',', ':')).encode()
                row = rows[key] = {'key': key, 'material': instance['material'],
                    'mesh_sha256': sha(mesh), 'instances': [], 'files': {}}
                for fmt in ['step', 'stl']:
                    folders = [source / fmt, MODEL / 'output/integrated-candidate' / fmt,
                               MODEL / 'output/v0-rounded-body' / fmt,
                               MODEL / 'output/service-design' / fmt,
                               MODEL / 'output' / ('step-parts' if fmt == 'step' else 'stl')]
                    path = next((f / (key + '.' + fmt) for f in folders
                                 if (f / (key + '.' + fmt)).exists()), None)
                    if path is None:
                        row['files'][fmt] = {'missing_source_export': True}
                        continue
                    target = dest / fmt / path.name
                    target.parent.mkdir(exist_ok=True)
                    if target.exists():
                        assert sha(target.read_bytes()) == sha(path.read_bytes())
                    else:
                        shutil.copyfile(path, target)
                    row['files'][fmt] = {'path': str(target.relative_to(NATIVE)),
                                         'sha256': sha(target.read_bytes()),
                                         'resolved_source': str(path.relative_to(MODEL))}
            rows[key]['instances'].append({k: instance.get(k) for k in ['name', 'leg', 'group']})
        record = {'variant': variant, 'source_model_sha256': identity,
                  'source_folder': str(source.relative_to(MODEL)),
                  'reference_model': str(frozen.relative_to(NATIVE)),
                  'custom_parts': list(rows.values()), 'source_of_truth_changed': False}
        (dest / 'reference.json').write_text(json.dumps(record, indent=2))
        targets[variant] = record
    low = {p['key']: p for p in targets['low']['custom_parts']}
    high = {p['key']: p for p in targets['high']['custom_parts']}
    shared = [k for k in sorted(low.keys() & high.keys()) if low[k]['mesh_sha256'] == high[k]['mesh_sha256']]
    result = {'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'targets': targets, 'shared_meshes': shared,
              'variant_specific_meshes': sorted((low.keys() | high.keys()) - set(shared)),
              'missing_source_exports': [{'variant': v, 'key': p['key'], 'format': fmt}
                  for v, t in targets.items() for p in t['custom_parts']
                  for fmt, f in p['files'].items() if f.get('missing_source_export')],
              'migration_gate_passed': False}
    (NATIVE / 'manifests/current-targets.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({'custom_low': len(low), 'custom_high': len(high),
                      'shared': len(shared), 'variant_specific': result['variant_specific_meshes']}))


if __name__ == '__main__':
    freeze()
