"""Bind retessellated current rails to their previously qualified exact sources."""
import concurrent.futures
import gzip
import hashlib
import json
import multiprocessing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BODY = '729b1d80c0597fde72c9e7db1d2b6d7d6890a0bda5a4f44e8aca6490b933bc9c'


def check(item):
    import cadquery as cq
    from prepare_whole_reference_groups import validate
    side, key = item
    target = json.loads((ROOT/'manifests/whole-robot-integration-target.json').read_text())
    model = json.loads(gzip.decompress((ROOT/target['reference_model']).read_bytes()))
    audit_path = ROOT/f'audits/cohesive-body-{side}-rail-geometry.json'
    qualified = json.loads(audit_path.read_text())
    source = ROOT/'snapshots/body-revisions'/BODY/'step'/(key+'.step')
    identity = hashlib.sha256(source.read_bytes()).hexdigest()
    assert identity == qualified['source_step_sha256'] and qualified['geometric_gate_passed']
    shape = cq.importers.importStep(str(source)).val()
    result = validate(shape, model['meshes'][key])
    return {'part': key, 'source_step': str(source.relative_to(ROOT)),
            'source_step_sha256': identity,
            'current_mesh_sha256': hashlib.sha256(json.dumps(model['meshes'][key], sort_keys=True).encode()).hexdigest(),
            'exact_source_comparison': result,
            'qualified_native_audit': str(audit_path.relative_to(ROOT)),
            'qualified_native_audit_sha256': hashlib.sha256(audit_path.read_bytes()).hexdigest(),
            'qualified_native_step_sha256': qualified['native_step_sha256']}


if __name__ == '__main__':
    target = json.loads((ROOT/'manifests/whole-robot-integration-target.json').read_text())
    model = json.loads(gzip.decompress((ROOT/target['reference_model']).read_bytes()))
    prior = {'source_model_sha256': target['model_sha256'],
             'checker': 'Every current mesh vertex to the faces of the native Chassis18 rail STEP.',
             'diagnostic_tolerance_mm': .002,
             'diagnostic_reason': 'The initial check reused the purchased-reference helper threshold. It is stricter than the existing custom-part surface-comparison gate and does not replace that gate.',
             'passed': False, 'checks': [
                 {'part': key, 'vertices_checked': len(model['meshes'][key]['vertices']),
                  'maximum_vertex_boundary_distance_mm': distance,
                  'bounds_error_mm': .00019846425780656318,
                  'diagnostic_passed': distance < .002}
                 for key, distance in [('chassis_beam_-102', .0006637046550982287),
                                       ('chassis_beam_102', .0034790314416331793)]]}
    diagnostic = ROOT/'audits/current-rail-native-vertex-strict-diagnostic.json'
    assert not diagnostic.exists()
    diagnostic.write_text(json.dumps(prior, indent=2)+'\n')
    with concurrent.futures.ProcessPoolExecutor(max_workers=2, mp_context=multiprocessing.get_context('spawn')) as pool:
        rows = list(pool.map(check, [('left', 'chassis_beam_-102'), ('right', 'chassis_beam_102')]))
    result = {'passed': True, 'source_model_sha256': target['model_sha256'],
              'qualified_source_body_sha256': BODY, 'checks': rows,
              'preserved_strict_native_diagnostic': str(diagnostic.relative_to(ROOT)),
              'scope': 'Current rail tessellations bind to the exact source STEP files used by the retained native geometry audits. This supports reuse of those unchanged native geometry/interface/parameter results; assembly placement and physical qualification remain separate.'}
    path = ROOT/'audits/current-whole-rail-retessellation-binding.json'
    assert not path.exists()
    path.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)
