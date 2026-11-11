"""Reopen every prepared plate and verify quantity, scale and bed placement."""
import hashlib,json,zipfile
import numpy as np
import trimesh
from kinematics import ROOT
out=ROOT/'output';plan=json.loads((out/'manufacturing-plan.json').read_text());checks=[]
assert plan['model_sha256']==hashlib.sha256((out/'model.json').read_bytes()).hexdigest()
for plate in plan['plates']:
 path=out/plate['file']
 with zipfile.ZipFile(path) as z:assert z.testzip() is None
 scene=trimesh.load(path,force='scene')
 assert len(scene.graph.nodes_geometry)==len(plate['parts']),plate['id']
 bounds=scene.bounds
 assert np.all(bounds[0]>=np.array([10,10,0])-.002),(plate['id'],bounds)
 assert np.all(bounds[1]<=np.array([315,310,315])+.002),(plate['id'],bounds)
 expected=sum(np.prod([1])*trimesh.load_mesh(out/next(p['oriented_stl'] for p in plan['parts'] if p['id']==item['id'])).volume for item in plate['parts'])
 actual=sum(scene.geometry[scene.graph[node][1]].volume for node in scene.graph.nodes_geometry)
 assert abs(actual-expected)/max(expected,1)<1e-5,(plate['id'],actual,expected)
 checks.append({'plate':plate['id'],'instances':len(plate['parts']),'bounds_mm':bounds.tolist(),'relative_volume_error':abs(actual-expected)/max(expected,1),'file_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
report={'model_sha256':plan['model_sha256'],'plates':checks,'scope':'3MF reopened as scenes with expected instance counts, millimetre scale, mesh volume and conservative bed bounds. Does not slice supports or generate G-code.'}
(out/'manufacturing-verification.json').write_text(json.dumps(report,indent=2));print(f'{len(checks)} 3MF plates reopened with correct quantity, scale and placement.')
