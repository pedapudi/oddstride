"""Compare the paired-bearing robot against the corrected shell-clamp reference."""
import hashlib,importlib.util,json
from kinematics import ROOT,uniform
OUT=ROOT/'output/paired-roll-work';BASE=ROOT/'output/clamp-seat-work'
spec=importlib.util.spec_from_file_location('review',ROOT.parents[2]/'viewer/serve.py')
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
new,old=review.Engine(OUT/'model.json'),review.Engine(BASE/'model.json')
raw=(OUT/'model.json').read_bytes();stamp=hashlib.sha256(raw).hexdigest()
def compare(q):
    a={tuple(x) for x in new.check(q)['pairs']};z={tuple(x) for x in old.check(q)['pairs']}
    return sorted(a),sorted(a-z),sorted(z-a),len(z)
poses=[]
for row in json.loads((BASE/'audit.json').read_text())['motion_samples']:
    hits,added,removed,count=compare(row['angles'])
    poses.append(dict(pose=row['pose'],angles=row['angles'],hits=hits,added_pairs=added,removed_pairs=removed,source_hit_count=count,passed=not hits))
    print('Pose',row['pose'],'hits',len(hits),'added',len(added),flush=True)
(OUT/'audit.json').write_text(json.dumps(dict(model_sha256=stamp,motion_samples=poses,
    scope='Sampled nominal rigid parts. Same rigid groups and listed mating interfaces excluded. Printed fits, flexible cable motion and loaded deflection remain unqualified.'),indent=2))
fold=[]
for k in range(-156,-47):
    hits,added,removed,count=compare(uniform([0,30,k]))
    fold.append(dict(knee_pitch_deg=k,pairs=hits,added_pairs=added,removed_pairs=removed))
(OUT/'limb-folding.json').write_text(json.dumps(dict(model_sha256=stamp,knee_samples=fold,clear_samples=sum(not r['pairs'] for r in fold)),indent=2))
report=dict(model_sha256=stamp,previously_clear_poses_lost=[r['pose'] for r in poses if not r['source_hit_count'] and r['hits']],
    added_motion_pairs=[dict(pose=r['pose'],pairs=r['added_pairs']) for r in poses if r['added_pairs']],
    knee_clear_samples=sum(not r['pairs'] for r in fold))
(OUT/'paired-roll-motion.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
