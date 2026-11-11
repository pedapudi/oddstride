"""Index existing, hash-bound definition evidence without promoting the robot."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TINFOX = ROOT.parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def proof(path, **extra):
    path = path.resolve()
    return {'path': str(path.relative_to(TINFOX)), 'sha256': sha(path), **extra}


def contains_name(value, names):
    if isinstance(value, dict):
        return any(key in names or contains_name(child, names) for key, child in value.items())
    if isinstance(value, list):
        return any(contains_name(child, names) for child in value)
    return isinstance(value, str) and value in names


def main():
    mapping_path = ROOT/'manifests/whole-native-component-map-candidate.json'
    mapping = json.loads(mapping_path.read_text())['parts']
    canonical_path = ROOT/'manifests/motor-complex-native-exports.json'
    canonical = json.loads(canonical_path.read_text())
    assert canonical['native_source_of_truth'] is True
    reports = []
    for path in (ROOT/'audits').glob('*.json'):
        if path.name.endswith(('-rpc.json','-timing.json')):
            continue
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            reports.append((path, data))
    equivalent = {}
    equivalence_path = ROOT/'audits/recessed-closure-family-export-restore.json'
    equivalence = json.loads(equivalence_path.read_text())
    assert equivalence['passed']
    for row in equivalence['parts']:
        assert row['identical_step_data_section']
        equivalent.setdefault(row['pre_sha256'], set()).add(row['post_sha256'])
        equivalent.setdefault(row['post_sha256'], set()).add(row['pre_sha256'])
    revision_paths = [TINFOX/'analysis/dfma/knee-stator-seats'/name for name in
                      ['native-seat-validation.json','native-hub-relief-validation.json','native-closure-validation.json']]
    revisions = [(path, json.loads(path.read_text())) for path in revision_paths]
    rows = []
    for key, native in mapping.items():
        file = ROOT/native['native_step']
        identity = sha(file)
        assert identity == native['native_step_sha256'], key
        identities = {identity} | equivalent.get(identity, set())
        geometry, sectional, family, retained_failures, routes = [], [], [], [], []
        for path, report in reports:
            if report.get('native_step_sha256') == identity:
                if report.get('geometric_gate_passed') is True:
                    geometry.append(proof(path, binding='exact native STEP hash'))
                if report.get('section_gate_passed') is True:
                    sectional.append(proof(path, binding='exact native STEP hash'))
                if report.get('passed') is True and all(report.get(k) is True for k in
                       ['surface_gate_passed','volume_gate_passed','cylinder_gate_passed','area_gate_passed','section_gate_passed']):
                    geometry.append(proof(path, binding='explicit numerical-recovery aggregate for exact native STEP'))
                    sectional.append(proof(path, binding='explicit native-section resolution for exact native STEP'))
                for flag in ['geometric_gate_passed','section_gate_passed']:
                    if report.get(flag) is False:
                        retained_failures.append(proof(path, failed_gate=flag))
            if report.get('passed') is True and isinstance(report.get('parts'), list):
                for index, row in enumerate(report['parts']):
                    if not isinstance(row, dict) or row.get('part') != key:
                        continue
                    if row.get('native_sha256', row.get('native_step_sha256')) == identity and row.get('geometry_passed') is True and row.get('sections_passed') is True:
                        p = proof(path, row=index, binding='exact current derived native STEP hash', qualified_parent_native_sha256=row.get('parent_sha256',row.get('qualified_parent_native_sha256')))
                        geometry.append(p);sectional.append(p)
            # Name-bound family records are indexed separately. Their relation
            # to the current native history must also survive the live inventory
            # and final edit/restore audit; a matching name is not a hash proof.
            if report.get('passed') is True and any(word in path.name for word in ['family','edit-restore','family-edits']):
                if contains_name(report, {key, native['component_part_number']}):
                    family.append(proof(path, binding='named parameter/family evidence; current native history verification remains separate'))
        scoped = canonical['parts'].get(key)
        if scoped and scoped['native_step_sha256'] == identity:
            evidence = []
            for ref in scoped.get('geometry_comparison_evidence', []):
                p = Path(ref['path'])
                if not p.is_absolute():
                    p = ROOT/p
                assert sha(p) == ref['sha256'], (key, p)
                evidence.append(proof(p))
            routes.append({'kind': 'already_canonical_native_scope', 'manifest': proof(canonical_path),
                           'part': key, 'native_step_sha256': identity, 'evidence': evidence,
                           'note': 'Reuses the explicitly approved motor-complex geometry scope, including its retained numerical exceptions and independent resolutions.'})
        for path, report in revisions:
            assert report['passed']
            matches = []
            if path.name == 'native-seat-validation.json':
                matches = [r for r in report['results'] if r.get('sha256') in identities and r.get('passed') is True]
            elif path.name == 'native-hub-relief-validation.json':
                matches = [r for r in report['rows'] if r.get('sha256') in identities and r.get('passed') is True]
            else:
                names = [name for name, r in report['inputs'].items() if r['sha256'] in identities]
                matches = [r for r in report['comparisons'] if r['part'] in names and r.get('passed') is True]
            if matches:
                routes.append({'kind': 'explicit_native_design_revision_validation', 'report': proof(path),
                               'binding_native_hashes': sorted(identities),
                               'step_data_equivalence': proof(equivalence_path) if len(identities)>1 else None,
                               'note': 'Exact exported revised solids compared with the independent intended revision. Replaces comparison against superseded unmodified surfaces; does not claim that the old planar-section report validates a changed pocket.'})
        if geometry and sectional:
            routes.append({'kind': 'direct_or_derived_geometry_and_section_evidence'})
        covered = bool(routes)
        rows.append({'part': key, **native, 'export_hash_verified': True,
                     'geometry_reports': geometry, 'section_reports': sectional,
                     'coverage_routes': routes, 'geometry_lineage_covered': covered,
                     'named_family_parameter_evidence': family,
                     'preserved_raw_comparison_failures': retained_failures})
    gaps = [r['part'] for r in rows if not r['geometry_lineage_covered']]
    result = {'definition_map_sha256': sha(mapping_path), 'definitions': len(rows),
              'geometry_lineage_covered_count': len(rows)-len(gaps), 'geometry_lineage_gaps': gaps,
              'geometry_lineage_complete': not gaps, 'parts': rows,
              'whole_robot_canonical': False,
              'scope': 'Per-definition export integrity and retained geometry/section/revision lineage only. Named family records are indexed as supporting evidence, not promoted into current-history proof. Actual assembly placement, current feature health, edit/restore, saved reopening, motion and service gates are owned by the native assembly audit. CNC access and physical strength remain separate.'}
    path = ROOT/'audits/current-definition-evidence-index.json'
    path.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['parts','scope']},indent=2))


if __name__ == '__main__':
    main()
