"""Check the head installation against fixed frame, cover and equipment geometry."""
import hashlib,json,sys
from functools import cache
import cadquery as cq
import numpy as np
import trimesh
from kinematics import ROOT,P,matrix

OUT=ROOT/'output'/(sys.argv[1] if len(sys.argv)>1 else 'shoulder-head-prototype')
raw=(OUT/'model.json').read_bytes();model=json.loads(raw);P.update(model['parameters'])
parts={p['name']:p for p in model['parts']}
new=trimesh.collision.CollisionManager();fixed=trimesh.collision.CollisionManager()
for name,p in parts.items():
    is_new=name.startswith(('neck_','head_bridge','equipment_head'))
    is_fixed=name.startswith(('body_','belly_','chassis_','electronics_')) or p.get('leg') and p['group']=='mount'
    if p.get('service_role')=='withdrawal' or not (is_new or is_fixed):continue
    mesh=model['meshes'][p['mesh']]
    shape=trimesh.Trimesh(vertices=mesh['vertices'],faces=mesh['faces'],process=False)
    (new if is_new else fixed).add_object(name,shape,transform=matrix(p,model['poses']['stand']))

@cache
def solid(name):
    p=parts[name];key=p['mesh']
    for folder in [OUT/'step',ROOT/'output/integrated-candidate/step',ROOT/'output/v0-rounded-body/step',ROOT/'output/service-design/step',ROOT/'output/step-parts']:
        path=folder/(key+'.step')
        if path.exists():
            shape=cq.importers.importStep(str(path)).val()
            transform=matrix(p,model['poses']['stand'])
            assert np.allclose(transform[:3,:3],np.eye(3)),name
            return shape.translate(tuple(transform[:3,3]))
    return None

_,pairs=new.in_collision_other(fixed,return_names=True)
rows=[]
for a,b in sorted(pairs):
    aa,bb=solid(a),solid(b)
    volume=aa.intersect(bb).Volume() if aa is not None and bb is not None else None
    rows.append({'parts':[a,b],'exact_overlap_mm3':volume,'requires_review':volume is None or volume>.05})
    print(a,b,volume,flush=True)
report={'model_sha256':hashlib.sha256(raw).hexdigest(),'pairs':rows,
        'unresolved_pairs':[r for r in rows if r['requires_review']],
        'scope':'Mesh broad phase followed by exact STEP volume checks where available. Contacts below 0.05 cubic mm are reported as contact, not penetration. Fixed mounting hardware, cover and equipment envelope check only; insertion paths and loaded strength are not certified.'}
(OUT/'installation-fit.json').write_text(json.dumps(report,indent=2))
print('Unresolved installation pairs:',len(report['unresolved_pairs']),flush=True)
