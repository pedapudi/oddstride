"""Screen existing native exports against both current frozen robot variants.

This report measures coverage and geometry only. It cannot certify feature
history, current cloud document contents, family edits or assembly readiness.
"""
import concurrent.futures
import hashlib
import json
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]


def export_for(key):
    stem = key.removesuffix('_right')
    suffix = '-right' if key.endswith('_right') else ''
    if stem in ['thigh_inner', 'thigh_outer', 'shin_inner', 'shin_outer']:
        return NATIVE / 'exports' / ('cohesive-' + stem.replace('_', '-') + suffix + '-final.step')
    if stem == 'knee_inner_spacer':
        return NATIVE / 'exports' / ('cohesive-knee-inner-spacer' + suffix + '.step')
    return NATIVE / 'exports' / (key + '.step')


def check(task):
    import cadquery as cq
    import numpy as np
    from audit_part import volume, cylinders, datum_comparison
    variant, row = task
    key = row['key']
    result = {'variant': variant, 'key': key, 'scope': 'Local native export coverage screen only',
              'native_file': str(export_for(key).relative_to(NATIVE))}
    source_record = row['files']['step']
    native_file = export_for(key)
    if source_record.get('missing_source_export'):
        return result | {'state': 'source_export_missing', 'passed': False}
    if not native_file.exists():
        return result | {'state': 'native_export_missing', 'passed': False}
    source_file = NATIVE / source_record['path']
    try:
        source = cq.importers.importStep(str(source_file)).val()
        native = cq.importers.importStep(str(native_file)).val()
        result.update(source_sha256=hashlib.sha256(source_file.read_bytes()).hexdigest(),
                      native_sha256=hashlib.sha256(native_file.read_bytes()).hexdigest())
        valid = source.isValid() and native.isValid()
        sv, nv = volume(source)[0], volume(native)[0]
        detail = NATIVE / 'audits' / (native_file.stem + '-geometry.json')
        evidence = {}
        if detail.exists():
            evidence = json.loads(detail.read_text())
            if (evidence.get('source_step_sha256') == result['source_sha256'] and
                    evidence.get('native_step_sha256') == result['native_sha256'] and
                    evidence.get('volume_integration', {}).get('method', '').startswith('Adaptive Gauss-Kronrod')):
                sv, nv = evidence['source_volume_mm3'], evidence['native_volume_mm3']
                result['volume_method_evidence'] = str(detail.relative_to(NATIVE))
        error = abs(sv - nv) / max(abs(sv), 1e-9)
        result.update(valid=valid, source_solids=len(source.Solids()),
                      native_solids=len(native.Solids()), source_volume_mm3=sv,
                      native_volume_mm3=nv, relative_volume_error=error)
        errors = {}
        # Gross mismatches are sufficient to reject old or missing revisions;
        # reserve more expensive boundary probes for plausible matches.
        if valid and error < .01:
            for name, a, b in [('source_to_native', source, native), ('native_to_source', native, source)]:
                vertices, _ = a.tessellate(.03, .06)
                indices = np.random.default_rng(29).choice(len(vertices), min(240, len(vertices)), replace=False)
                boundary = cq.Compound.makeCompound(b.Faces())
                distances = [boundary.distance(cq.Vertex.makeVertex(*vertices[i].toTuple())) for i in indices]
                worst = max(range(len(distances)), key=lambda i: distances[i])
                errors[name] = {'samples': len(indices), 'maximum_mm': max(distances),
                                'worst_point_mm': list(vertices[indices[worst]].toTuple())}
            result['surface_deviation'] = errors
            matches_detail = (evidence.get('source_step_sha256') == result['source_sha256'] and
                              evidence.get('native_step_sha256') == result['native_sha256'])
            declared = evidence.get('declared_functional_clearance_cylinders') if matches_detail else None
            pos, axis, passed, extra, unknown = datum_comparison(cylinders(source), cylinders(native), key, declared)
            result.update(critical_cylinders_passed=bool(passed), cylinder_error_mm=pos,
                          cylinder_axis_error=axis, unexplained_cylinders=unknown)
        else:
            passed = False
        result['passed'] = bool(valid and error < .001 and passed and
                            len(source.Solids()) == len(native.Solids()) and
                            all(v['maximum_mm'] < .05 for v in errors.values()))
        result['state'] = 'geometry_screen_passed' if result['passed'] else 'geometry_differs'
    except Exception as exc:
        result.update(state='screen_error', error=str(exc), passed=False)
    return result


def main():
    targets = json.loads((NATIVE / 'manifests/current-targets.json').read_text())
    tasks = [(variant, row) for variant, target in targets['targets'].items()
             for row in target['custom_parts']]
    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        for row in pool.map(check, tasks):
            rows.append(row)
            print(row['variant'], row['key'], row['state'], flush=True)
    report = {'source_model_sha256': {v: t['source_model_sha256'] for v, t in targets['targets'].items()},
              'parts': rows, 'geometry_screen_passed': all(r['passed'] for r in rows),
              'migration_gate_passed': False,
              'scope': 'Finite local STEP boundary, volume and cylindrical datum screen. '
                       'Passing rows still require native history, sections, edits, saved-state, '
                       'assembly, motion and service qualification.'}
    (NATIVE / 'audits/current-target-geometry-screen.json').write_text(json.dumps(report, indent=2))
    print('Passed', sum(r['passed'] for r in rows), 'of', len(rows), flush=True)


if __name__ == '__main__':
    main()
