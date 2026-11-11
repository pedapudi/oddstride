"""Keep current metadata small and load reference part libraries on demand."""
import gzip
import hashlib
import html
import json
import re
from pathlib import Path


def encoded(value):
    return json.dumps(value, separators=(',', ':'), ensure_ascii=False).encode()


def write_catalog(viewer, catalog):
    viewer = Path(viewer)
    archive = viewer / 'archive/designs'
    archive.mkdir(parents=True, exist_ok=True)
    result = {**catalog, 'schema': 2, 'designs': []}
    for design in catalog['designs']:
        if not design.get('archived') and not design.get('defer_details'):
            result['designs'].append(design)
            continue
        assert re.fullmatch(r'[A-Za-z0-9_-]+', design['id'])
        raw = encoded(design)
        file = archive / (design['id'] + '.json.gz')
        file.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
        assert json.loads(gzip.decompress(file.read_bytes())) == design
        summary = {key: value for key, value in design.items()
                   if key not in ['parts', 'reports', 'comparison_parts']}
        summary.update(detail_url='archive/designs/' + file.name,
                       detail_sha256=hashlib.sha256(raw).hexdigest())
        result['designs'].append(summary)
    data = encoded(result)
    temporary = viewer / 'catalog.json.tmp'
    temporary.write_bytes(data)
    temporary.replace(viewer / 'catalog.json')
    rows = '\n'.join(
        f'<li><a href="../?design={html.escape(design["id"])}">{html.escape(design["title"])}</a></li>'
        for design in reversed(catalog['designs']) if design.get('archived'))
    bundles = []
    for path in sorted((viewer.parent/'archive/browser').glob('*/manifest.json'), reverse=True):
        report = json.loads(path.read_text()).get('result', {})
        if report.get('archive'):
            bundles.append(f'<li><a href="../../{html.escape(report["archive"])}">Archived review files</a>: '
                           f'{report["original_files"]} files, SHA-256 <code>{report["archive_sha256"]}</code>.</li>')
    (viewer / 'archive/index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8">
<title>Tinfox historical design reviews</title><style>body{font:17px system-ui;max-width:850px;margin:60px auto;padding:20px;line-height:1.6}a{color:#985327}</style>
<h1>Historical design reviews</h1><p>These proposals preserve earlier geometry and checks.
Use the current review and its release notes for ongoing work. Historical print
files are not current assembly instructions.</p><p><a href="../">Open current review</a></p><ol>'''
        + rows + '</ol><h2>Original pages, captures and render iterations</h2><ul>'
        + ''.join(bundles) + '</ul><p>The viewer guide contains the restore command. CAD/native snapshots and active print releases remain in their original locations.</p></html>')
    return result


def read_catalog(viewer):
    """Restore full entries for metadata-only maintenance without touching CAD."""
    viewer = Path(viewer)
    catalog = json.loads((viewer / 'catalog.json').read_text())
    for index, design in enumerate(catalog['designs']):
        if design.get('detail_url'):
            raw = gzip.decompress((viewer / design['detail_url']).read_bytes())
            assert hashlib.sha256(raw).hexdigest() == design['detail_sha256']
            catalog['designs'][index] = json.loads(raw)
    return catalog
