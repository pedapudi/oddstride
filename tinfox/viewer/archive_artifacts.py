"""Archive obsolete browser payloads with hashes and reversible restoration."""
import argparse
import hashlib
import html
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEEP_CAPTURES = {'current-review.png'}
LEGACY_REVIEWS = [ROOT/'model/review', ROOT/'proposals/compact/model/review', ROOT/'proposals/sculpted/model/review']


def digest(data):
    return hashlib.sha256(data).hexdigest()


def candidates():
    files = set()
    for directory in LEGACY_REVIEWS:
        files.update(p for p in directory.rglob('*') if p.is_file() and not p.is_symlink()
                     and '__pycache__' not in p.parts and p.suffix != '.py')
    files.update(p for p in (ROOT/'viewer/captures').glob('*')
                 if p.is_file() and p.name not in KEEP_CAPTURES)
    for directory in [ROOT/'proposals/sculpted/design/iterations', ROOT/'proposals/compact/design/iterations']:
        files.update(p for p in directory.rglob('*')
                     if p.is_file() and not p.is_symlink() and p.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp', '.svg'])
    files.update(p for p in [ROOT/'viewer/enclosure-review.html', ROOT/'viewer/thigh-manufacturing.html',
                             ROOT/'proposals/index.html', ROOT/'design/body-options/index.html',
                             ROOT/'proposals/sculpted/model/fusion_native/exports/index.html'] if p.exists())
    # Previously replaced HTML notices remain working entry points on reruns.
    return sorted(p for p in files if p.suffix != '.html' or 'tinfox-archived-entry' not in p.read_text())


def notice(path, archive):
    relative = path.relative_to(ROOT)
    root_to_viewer = os.path.relpath(ROOT/'viewer/index.html', path.parent)
    root_to_archive = os.path.relpath(archive, path.parent)
    root_to_index = os.path.relpath(ROOT/'viewer/archive/index.html', path.parent)
    return f'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="tinfox-archived-entry" content="true"><title>Tinfox archived review</title>
<style>body{{font:17px system-ui;max-width:800px;margin:70px auto;padding:24px;line-height:1.6}}a{{color:#985327}}code{{overflow-wrap:anywhere}}</style>
<h1>This review is archived</h1><p><code>{html.escape(str(relative))}</code> describes an earlier Tinfox design.
Use the current review and its source labels for ongoing CAD work.</p>
<p><a href="http://127.0.0.1:8770/viewer/">Open current robot review</a> ·
<a href="{html.escape(root_to_viewer)}">Open viewer on this server</a> ·
<a href="{html.escape(root_to_index)}">Historical design index</a></p>
<p>The original files are preserved in a <a href="{html.escape(root_to_archive)}">hashed archive</a>.
The restore command is documented in the archive manifest and the viewer guide.</p></html>'''


def restore(archive, selected=None, overwrite=False):
    with zipfile.ZipFile(archive) as bundle:
        manifest = json.loads(bundle.read('manifest.json'))
        for record in manifest['files']:
            if selected and record['path'] != selected:
                continue
            target = ROOT / record['path']
            assert target.resolve().is_relative_to(ROOT.resolve()), target
            data = bundle.read(record['object'])
            assert digest(data) == record['sha256']
            if target.exists() and digest(target.read_bytes()) != record['sha256'] and not overwrite:
                raise FileExistsError(f'Use --overwrite to replace {target}')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    print('Restored requested archived files.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--restore', type=Path)
    parser.add_argument('--file')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    if args.restore:
        restore(args.restore, args.file, args.overwrite)
        return
    paths = candidates()
    before = sum(p.stat().st_size for p in paths)
    if not args.apply:
        print(json.dumps({'files_to_archive': len(paths), 'bytes': before,
                          'legacy_review_roots': [str(p.relative_to(ROOT)) for p in LEGACY_REVIEWS],
                          'protected': ['CAD/native geometry and snapshots', 'source generators',
                                        'current studio references', 'current print releases', 'current native review screenshot']}))
        return
    if not paths:
        print('No additional obsolete browser payloads found.')
        return
    directory = ROOT/'archive/browser'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    directory.mkdir(parents=True, exist_ok=False)
    archive = directory/'browser-history.zip'
    records = []
    objects = set()
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in paths:
            data = path.read_bytes(); stamp = digest(data); object_name = 'objects/'+stamp
            if stamp not in objects:
                bundle.writestr(object_name, data); objects.add(stamp)
            records.append({'path': str(path.relative_to(ROOT)), 'sha256': stamp,
                            'bytes': len(data), 'object': object_name})
        manifest = {'schema': 1, 'scope': 'Obsolete browser reviews, captures and historical render iterations; CAD migration evidence stays in place.',
                    'files': records, 'original_bytes': before, 'unique_objects': len(objects),
                    'restore': 'python3 tinfox/viewer/archive_artifacts.py --restore ARCHIVE --file TINFOX_RELATIVE_PATH --overwrite'}
        bundle.writestr('manifest.json', json.dumps(manifest, indent=2))
    # Verify every archived original before changing its active path.
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        for record in records:
            assert digest(bundle.read(record['object'])) == record['sha256']
            assert digest((ROOT/record['path']).read_bytes()) == record['sha256']
    stubs = 0
    for record in records:
        path = ROOT/record['path']
        if path.suffix == '.html':
            path.write_text(notice(path, archive)); stubs += 1
        else:
            path.unlink()
    # Empty legacy asset directories contain no source or live review data.
    for parent in LEGACY_REVIEWS:
        for directory_ in sorted((p for p in parent.rglob('*') if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
            if not any(directory_.iterdir()):
                directory_.rmdir()
    report = {'archive': str(archive.relative_to(ROOT)), 'archive_sha256': digest(archive.read_bytes()),
              'original_files': len(paths), 'original_bytes': before, 'unique_objects': len(objects),
              'archive_bytes': archive.stat().st_size, 'legacy_html_notices': stubs,
              'active_payload_bytes_removed': before - sum((ROOT/r['path']).stat().st_size for r in records if (ROOT/r['path']).exists())}
    (archive.parent/'manifest.json').write_text(json.dumps({**manifest, 'result': report}, indent=2))
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
