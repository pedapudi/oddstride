"""Flag surface samples with no straight point-ray approach; not a CAM audit."""
import hashlib,itertools,json,sys
import numpy as np
import trimesh
from kinematics import ROOT

folder=ROOT/'output/cohesive-chassis-work'
raw=(folder/'model.json').read_bytes();model=json.loads(raw)
keys=sys.argv[1:] or ['battery_cassette']
directions=np.array([p for p in itertools.product([-1,0,1],repeat=3) if any(p)],dtype=float)
directions/=np.linalg.norm(directions,axis=1)[:,None]
rng=np.random.default_rng(27);rows=[]
for key in keys:
    m=model['meshes'][key];mesh=trimesh.Trimesh(m['vertices'],m['faces'],process=True)
    mesh.fix_normals(multibody=True)
    if not mesh.is_watertight:
        rows.append({'part':key,'status':'mesh needs verification before ray screening'})
        continue
    ids=rng.choice(len(mesh.faces),min(600,len(mesh.faces)),replace=False,p=mesh.area_faces/mesh.area)
    points=mesh.triangles_center[ids];normals=mesh.face_normals[ids];visible=np.zeros(len(ids),dtype=bool)
    for direction in directions:
        indices=np.flatnonzero((normals@direction>.05)&~visible)
        if not len(indices):continue
        blocked=mesh.ray.intersects_any(points[indices]+direction*.03,np.tile(direction,(len(indices),1)))
        visible[indices[~blocked]]=True
    unseen=points[~visible]
    rows.append({'part':key,'sampled_surface_points':len(ids),'unseen_in_26_sampled_directions':len(unseen),
        'unseen_points_mm':unseen[:25].round(3).tolist(),
        'status':'needs cutter-access review' if len(unseen) else 'no obstruction found in sampled point rays'})
report={'model_sha256':hashlib.sha256(raw).hexdigest(),'checks':rows,
    'scope':'Point-ray visibility screen: 26 directions and up to600 area-weighted triangle centers per part. Occlusion flags suspect cutter access. Finite cutter/holder sizes, fixtures and continuous surface coverage are untested. A clear sample does not establish CNC compliance.'}
(folder/'cnc-access-screen.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'checks':[{k:v for k,v in r.items() if k!='unseen_points_mm'} for r in rows]}))
