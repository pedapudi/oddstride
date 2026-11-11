"""Verify variant solid files, printed meshes, nominal motion and hardware fits."""
import hashlib,json
import numpy as np
import cadquery as cq
import trimesh
from kinematics import ROOT,POSES
from collision import Checker
OUT=ROOT/'output';DEST=OUT/'limb-variants';main=json.loads((OUT/'model.json').read_text());manifest=json.loads((DEST/'manifest.json').read_text());assert manifest['parent_model_sha256']==hashlib.sha256((OUT/'model.json').read_bytes()).hexdigest()
reports=[]
for variant in manifest['variants']:
 code=variant['id'];folder=DEST/code;data=json.loads((folder/'model.json').read_text());records=json.loads((folder/'parts.json').read_text())['parts'];checks=[]
 for p in records:
  path=folder/p['step'];assert hashlib.sha256(path.read_bytes()).hexdigest()==p['step_sha256']
  if 'print_stl' in p:
   mesh=trimesh.load_mesh(folder/p['print_stl']);mesh.merge_vertices(digits_vertex=4);mesh.update_faces(mesh.nondegenerate_faces());mesh.update_faces(mesh.unique_faces());mesh.remove_unreferenced_vertices()
   assert mesh.is_watertight and mesh.volume>0,(code,p['id'],'print mesh')
   assert len([v for v in mesh.split() if v.volume>1e-4])==1,(code,p['id'],'split')
   assert np.all(mesh.extents<=[305,300,315]) and abs(mesh.bounds[0,2])<.01,(code,p['id'],'bed')
   mesh.export(folder/p['print_stl']);checks.append(p['id'])
 c=Checker.__new__(Checker);c.data=data;c.data['meshes'].update({k:v for k,v in main['meshes'].items() if k not in c.data['meshes']});c.data['parts']+=[p for p in main['parts'] if not p.get('leg')];c.parts={p['name']:p for p in c.data['parts'] if p['check']};c.manager=trimesh.collision.CollisionManager()
 for name,p in c.parts.items():
  m=c.data['meshes'][p['mesh']];c.manager.add_object(name,trimesh.Trimesh(vertices=m['vertices'],faces=m['faces'],process=False))
 poses={}
 for name,q in POSES.items():
  result=c.check(q);poses[name]=result;print(code,name,result['pairs'],flush=True)
  assert not result['collision'],(code,name,result['pairs'])
 # Printed changes must fit the unchanged mating parts, not just pass moving checks.
 fits=[]
 if code=='printed':
  def solid(n):return cq.importers.importStep(str(folder/'step'/f'{n}.step')).val()
  for a,b in [('shin_inner','shin_outer'),('motor_carrier_1_trunnion','roll_cartridge_1'),('motor_carrier_1_flange','hip_hub'),('motor_carrier_1_trunnion','motor_carrier_1_flange')]:
   overlap=max(0,solid(a).intersect(solid(b)).Volume());fits.append({'parts':[a,b],'overlap_mm3':overlap});assert overlap<1e-4,(code,a,b,overlap)
  # Check the keyed carrier can separate along the motor axis on the bench.
  for hand in ['1','-1']:
   tr=solid('motor_carrier_'+hand+'_trunnion');fl=solid('motor_carrier_'+hand+'_flange')
   for d in [0,.2,1,2,4,8,15,30,60]:
    v=max(0,tr.intersect(fl.translate((0,d,0))).Volume())
    assert v<1e-4,(code,hand,'carrier separation',d,v)
   fits.append({'parts':['motor_carrier_'+hand+'_trunnion','motor_carrier_'+hand+'_flange'],'removal_axis':[0,1,0],'checked_travel_mm':60})
 reports.append({'variant':code,'printable_meshes_checked':checks,'presets':poses,'fits':fits,'scope':'Eight rigid reference poses and selected static fits. No powered test, fatigue result or manufacturing acceptance.'})
(DEST/'verification.json').write_text(json.dumps({'parent_model_sha256':manifest['parent_model_sha256'],'variants':reports},indent=2))
print('All variant print meshes, bed bounds and reference poses passed.')
