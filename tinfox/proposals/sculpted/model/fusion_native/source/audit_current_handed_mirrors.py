"""Bind current handed exports to exact mirrors of qualified native parents."""
import concurrent.futures
import hashlib
import json
import multiprocessing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(key):
    import cadquery as cq
    from audit_part import audit
    from audit_sections import audit as sections
    mapping = json.loads((ROOT/'manifests/whole-native-component-map-candidate.json').read_text())['parts']
    parent_key = key.removesuffix('_right')
    parent, native = mapping[parent_key], mapping[key]
    parent_path, native_path = ROOT/parent['native_step'], ROOT/native['native_step']
    assert hashlib.sha256(parent_path.read_bytes()).hexdigest() == parent['native_step_sha256']
    assert hashlib.sha256(native_path.read_bytes()).hexdigest() == native['native_step_sha256']
    folder = ROOT/'snapshots/current-handed-native-mirrors'/key
    folder.mkdir(parents=True, exist_ok=False)
    reference = folder/'mirrored-qualified-parent.step'
    cq.exporters.export(cq.importers.importStep(str(parent_path)).val().mirror('XZ'), str(reference))
    label = 'whole-mirror-check-'+key
    alias = ROOT/'exports'/(label+'.step')
    assert not alias.exists()
    alias.symlink_to(native_path.resolve())
    definition = {'id': key, 'source_step': str(reference),
                  'source_reference_note': 'Exact XZ-plane reflection of the current qualified native left part; comparison geometry only. Never imported into the native CAD.',
                  'volume_method': 'gauss_kronrod_spans',
                  'volume_method_reason': 'Preserve the established span-aware custom-solid integration method.',
                  'skip_legacy_probes': True, 'exact_face_sampling': True}
    geometry = audit(key, label, definition)
    sectional = sections(key, label, definition)
    return {'part': key, 'native_step_sha256': native['native_step_sha256'],
            'qualified_parent': parent_key, 'qualified_parent_native_sha256': parent['native_step_sha256'],
            'reflection_plane': 'XZ', 'reflection_origin_mm': [0,0,0],
            'comparison_reference_sha256': hashlib.sha256(reference.read_bytes()).hexdigest(),
            'geometry_report': 'audits/'+label+'-geometry.json',
            'section_report': 'audits/'+label+'-sections.json',
            'geometry_passed': geometry['geometric_gate_passed'],
            'sections_passed': sectional['section_gate_passed']}


if __name__ == '__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=3, mp_context=multiprocessing.get_context('spawn')) as pool:
        rows = list(pool.map(check, ['input_crank_right','thigh_outer_right','thigh_inner_right']))
    result = {'passed': all(r['geometry_passed'] and r['sections_passed'] for r in rows),
              'parts': rows,
              'scope': 'Current right-hand native exports compared with exact reflections of their qualified native left parents. Existing left-part numerical exceptions and their independent resolutions remain part of the evidence chain. Placement, dynamic loading and CNC access are separate.'}
    destination = ROOT/'audits/current-handed-native-mirror-comparison.json'
    assert not destination.exists()
    destination.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)
