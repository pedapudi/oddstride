"""Record stationary body contacts separately from the bench-limb motion review."""
import hashlib,importlib.util,json
from kinematics import ROOT,uniform
OUT=ROOT/'output/paired-roll-work';BASE=ROOT/'output/clamp-seat-work'
spec=importlib.util.spec_from_file_location('review',ROOT.parents[2]/'viewer/serve.py')
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
def contacts(path):
    e=review.Engine(path);e.check(uniform([0,30,-60]))
    _,pairs=e.manager.in_collision_internal(return_names=True);hits=set()
    for a,b in pairs:
        p,q=e.parts[a],e.parts[b]
        if q['leg']=='FL':a,b,p,q=b,a,q,p
        if p['leg']=='FL' and not q['leg'] and (p['group']=='mount' or a.startswith('FL_motor_carrier')):hits.add((a,b))
    return hits
a,z=contacts(OUT/'model.json'),contacts(BASE/'model.json')
report=dict(model_sha256=hashlib.sha256((OUT/'model.json').read_bytes()).hexdigest(),
    checker='FCL rigid surface meshes at standing pose; front-left stationary module versus body',
    pairs=sorted(a),added_pairs=sorted(a-z),existing_pairs=sorted(a&z),removed_pairs=sorted(z-a),
    whole_robot_integration_qualified=False,
    scope='Unfiltered mesh contacts include mating hardware. Added contacts need separate solid classification and chassis redesign before installation. Bench limb print preparation does not validate the complete robot.')
(OUT/'body-integration.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'all':len(a),'added':len(a-z),'existing':len(a&z),'added_pairs':sorted(a-z)}),flush=True)
