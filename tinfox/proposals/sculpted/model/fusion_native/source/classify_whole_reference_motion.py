"""Reconcile a frozen motion screen with individually verified reference contacts."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target = json.loads((ROOT / 'manifests/whole-robot-integration-target.json').read_text())
    path = ROOT / 'audits' / ('whole-robot-integration-motion-screen-' + target['model_sha256'] + '.json')
    screen = json.loads(path.read_text())
    bench_path = ROOT.parents[3] / 'analysis/dfma/knee-stator-seats/native-bench-static-classification.json'
    bench = json.loads(bench_path.read_text())
    assert bench['passed'] and bench['unexpected_pairs'] == []
    groups_path = ROOT / 'manifests/whole-purchased-reference-groups.json'
    groups = json.loads(groups_path.read_text())
    assert groups['source_model_sha256'] == target['model_sha256']
    identities = {p['name']: p for p in groups['parts']}
    bench_threads = {tuple(sorted(r['pair'])): r for r in bench['each_positive_pair'] if r['classification'] == 'manufacturer_mounting_thread_volume_in_unthreaded_motor_reference'}
    records = []
    for leg in ('FL', 'FR', 'RL', 'RR'):
        for motor, prefix, bench_prefix, motor_name, radius, engagement in [
            ('hip', 'hip_output_bolt', 'Hip output M4x8', 'Hip pitch motor', 2, 4.3),
            ('knee', 'input_bolt', 'Knee output M4x12', 'Knee pitch motor', 2, 5.4),
        ]:
            for angle in range(0, 360, 60):
                pair = tuple(sorted([f'{leg}_{motor}_motor', f'{leg}_{prefix}_{angle}']))
                bolt = identities[f'{leg}_{prefix}_{angle}']
                expected = f'{bench_prefix} {angle}'
                assert bolt['source']['bench_instance'] == expected
                assert identities[f'{leg}_{motor}_motor']['source']['bench_instance'] == f'mc_{motor}_motor'
                source_pair = tuple(sorted([motor_name, expected]))
                evidence = bench_threads[source_pair]
                assert evidence['accepted'] and evidence['shaft_radius_mm'] == radius and evidence['penetration_mm'] == engagement
                records.append({'pair': list(pair), 'classification': 'verified_motor_output_thread_envelope',
                                'bench_pair': list(source_pair), 'shaft_radius_mm': radius,
                                'penetration_mm': engagement,
                                'basis': 'Exact named output screw and motor from the audited bench, propagated by the recorded handed transform. The motor reference omits its threaded holes. Relative joint motion rotates this output pattern around the same motor Y axis; it preserves the shaft radius and axial penetration. This classifies the reference-envelope contact, not physical thread fit.'})
    expected = {tuple(r['pair']) for r in records}
    assert len(expected) == 48
    samples = []
    for row in screen['samples']:
        added = {tuple(p) for p in row['added_pairs']}
        unresolved = added - expected
        missing = expected - added
        samples.append({'pose': row['pose'], 'classified_added_pairs': [list(p) for p in sorted(added & expected)],
                        'unresolved_added_motion_pairs': [list(p) for p in sorted(unresolved)],
                        'unexpectedly_missing_reference_contacts': [list(p) for p in sorted(missing)],
                        'inherited_motion_pairs': row['source_pairs'],
                        'raw_fixed_body_contacts': row['composite_fixed_body_contacts'],
                        'added_fixed_body_flags_requiring_solid_review': row['added_fixed_body_contacts']})
    out = {'source_model_sha256': target['model_sha256'], 'screen_sha256': digest(path),
           'bench_static_classification_sha256': digest(bench_path), 'reference_groups_sha256': digest(groups_path),
           'sampled_motion_pair_parity_after_explicit_reference_classification': all(not s['unresolved_added_motion_pairs'] and not s['unexpectedly_missing_reference_contacts'] for s in samples),
           'thread_reference_pairs': records, 'samples': samples,
           'whole_robot_canonical': False,
           'scope': 'Reconciliation of 12 recorded inspection poses only. The unchanged raw mesh screen remains available. Fixed body flags require separate exact solid classification. Existing source contacts, continuous motion, cable behavior, manufacturing tolerance and strength remain outside this result.'}
    destination = ROOT / 'audits' / ('whole-reference-motion-classification-' + target['model_sha256'] + '.json')
    assert not destination.exists()
    destination.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({'sampled_motion_pair_parity': out['sampled_motion_pair_parity_after_explicit_reference_classification'], 'classified_pair_count': len(records), 'poses': len(samples), 'path': str(destination)}))


if __name__ == '__main__':
    main()
