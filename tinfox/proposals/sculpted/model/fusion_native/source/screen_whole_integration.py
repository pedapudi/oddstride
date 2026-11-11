"""Screen the whole-robot migration reference against its frozen source poses."""
import gzip
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

NATIVE=Path(__file__).resolve().parents[1]
MODEL=NATIVE.parent
sys.path.insert(0,str(MODEL))
spec=importlib.util.spec_from_file_location('integration_review',MODEL.parents[2]/'viewer/serve.py')
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)


def fixed_body_contacts(engine):
    _,pairs=engine.manager.in_collision_internal(return_names=True)
    hits=[]
    for a,b in pairs:
        p,q=engine.parts[a],engine.parts[b]
        if q.get('leg'):a,b,p,q=b,a,q,p
        if p.get('leg') and not q.get('leg') and (p['group']=='mount' or a.endswith('_motor_carrier')):
            hits.append(tuple(sorted([a,b])))
    return set(hits)


def main():
    manifest=json.loads((NATIVE/'manifests/whole-robot-integration-target.json').read_text())
    raw=gzip.decompress((NATIVE/manifest['reference_model']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==manifest['model_sha256']
    source_path=MODEL/'output/paired-roll-work/model.json'
    assert hashlib.sha256(source_path.read_bytes()).hexdigest()==manifest['generated_whole_reference_sha256']
    source_data=json.loads(source_path.read_text())
    poses={key:value for key,value in source_data['poses'].items()}
    for i,angles in enumerate([[-60,-30,-60],[0,-60,-60],[0,90,-60],[60,-30,-60]]):
        poses['combined_'+str(i)]={leg:angles for leg in ['FL','FR','RL','RR']}
    rows=[]
    with tempfile.TemporaryDirectory(prefix='tinfox-whole-reference-') as folder:
        candidate=Path(folder)/'model.json';candidate.write_bytes(raw)
        new=review.Engine(candidate);old=review.Engine(source_path)
        for name,q in poses.items():
            new_hits={tuple(pair) for pair in new.check(q)['pairs']};new_fixed=fixed_body_contacts(new)
            old_hits={tuple(pair) for pair in old.check(q)['pairs']};old_fixed=fixed_body_contacts(old)
            rows.append({'pose':name,'angles':q,'source_pairs':sorted(old_hits),'composite_pairs':sorted(new_hits),
                'added_pairs':sorted(new_hits-old_hits),'removed_pairs':sorted(old_hits-new_hits),
                'source_fixed_body_contacts':sorted(old_fixed),'composite_fixed_body_contacts':sorted(new_fixed),
                'added_fixed_body_contacts':sorted(new_fixed-old_fixed),'removed_fixed_body_contacts':sorted(old_fixed-new_fixed)})
            print(name,'source',len(old_hits),'composite',len(new_hits),'new',len(new_hits-old_hits),flush=True)
    report={'model_sha256':manifest['model_sha256'],'source_model_sha256':manifest['generated_whole_reference_sha256'],
        'checker':'FCL rigid triangle meshes; current local kinematics; source inspection poses plus four combined limits.',
        'scope':'Migration reference screen. Fixed body contacts are retained unfiltered and require solid classification. Listed mating interfaces and same rigid groups are excluded only from the motion-pair list. Flexible cables, physical tolerances, loaded deflection and continuous motion remain unverified.',
        'whole_robot_canonical':False,'samples':rows,
        'previously_clear_samples_with_new_pairs':[r['pose'] for r in rows if not r['source_pairs'] and r['composite_pairs']],
        'sampled_poses_with_added_fixed_contacts':[r['pose'] for r in rows if r['added_fixed_body_contacts']]}
    destination=NATIVE/'audits'/('whole-robot-integration-motion-screen-'+manifest['model_sha256']+'.json')
    assert not destination.exists(), 'Preserve an existing model-specific audit.'
    destination.write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2))


if __name__=='__main__':main()
