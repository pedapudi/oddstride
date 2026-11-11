"""Test native tie placement, shared holes and countersink geometry through edits."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,math,time,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');assert doc==app.activeDocument;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;parts={side:next(c for c in d.allComponents if c.partNumber=='CANDIDATE_chassis_crossmember_'+str(sign*121)) for side,sign in [('front',1),('rear',-1)]};tick=time.monotonic()
 def measure():
  rows={}
  for side,c in parts.items():
   b=c.bRepBodies.item(0);box=b.boundingBox;row={'bounds':[v*10 for v in [box.minPoint.x,box.minPoint.y,box.minPoint.z,box.maxPoint.x,box.maxPoint.y,box.maxPoint.z]],'volume_mm3':b.volume*1000,'cylinders':[],'cones':[]}
   for f in b.faces:
    cylinder=core.Cylinder.cast(f.geometry);cone=core.Cone.cast(f.geometry)
    if cylinder and abs(cylinder.axis.z)>.999999:row['cylinders'].append({'x':cylinder.origin.x*10,'y':cylinder.origin.y*10,'radius':cylinder.radius*10})
    if cone:row['cones'].append({'half_angle_rad':cone.halfAngle})
   assert len(row['cones'])==4,(side,row['cones']);assert all(abs(abs(cone['half_angle_rad'])-math.pi/4)<1e-7 for cone in row['cones']);assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);rows[side]=row
  return rows
 def hole(row,x,y,r):assert any(abs(p['x']-x)<.0001 and abs(p['y']-y)<.0001 and abs(p['radius']-r)<.0001 for p in row['cylinders']),(x,y,r,row['cylinders'])
 baseline=measure();edits=[]
 for name,expr in [('robot_roll_y','73 mm'),('robot_hip_x','190 mm'),('robot_fastener_diametral_allowance','.6 mm')]:
  p=d.userParameters.itemByName(name);old=p.expression
  try:
   p.expression=expr;assert d.computeAll();edited=measure();half=d.userParameters.itemByName('frame_half_y').value*10;x=d.userParameters.itemByName('rail_crossmember_x').value*10;r=d.userParameters.itemByName('frame_m3_clearance').value*5;root_r=d.userParameters.itemByName('saddle_root_hole_radius').value*10
   for side,sign in [('front',1),('rear',-1)]:
    target=list(baseline[side]['bounds'])
    if name=='robot_roll_y':target[1]-=5;target[4]+=5
    if name=='robot_hip_x':target[0]+=sign*5;target[3]+=sign*5
    assert max(abs(a-b) for a,b in zip(edited[side]['bounds'],target))<.001,(side,edited[side]['bounds'],target)
    for dx in [-3,3]:
     for sy in [-1,1]:hole(edited[side],sign*x+dx,sy*(half-3),r)
   for sy in [-1,1]:hole(edited['front'],x,sy*24,root_r)
   assert not any(abs(p['radius']-root_r)<.0001 for p in edited['rear']['cylinders']);edits.append({'parameter':name,'edited_expression':expr,'measurements':edited,'passed':True})
  finally:p.expression=old;assert d.computeAll()
  restored=measure();error=max(abs(a-b) for side in parts for a,b in zip(restored[side]['bounds'],baseline[side]['bounds']));assert error<.001;assert all(abs(restored[side]['volume_mm3']-baseline[side]['volume_mm3'])<.001 for side in parts);edits[-1]['restore_max_bounds_error_mm']=error
 paths=[]
 for side,c in parts.items():
  occ=next(o for o in root.occurrences if o.component==c);visible=occ.isLightBulbOn;occ.isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','frame-intent-'+side+'-tie-restored.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));occ.isLightBulbOn=visible;assert os.path.getsize(path)>10000;paths.append(path)
 print(json.dumps({'passed':True,'saved':False,'baseline':baseline,'edits':edits,'paths':paths,'elapsed_seconds':time.monotonic()-tick,'scope':'Both transverse ties follow the rail pattern; the front retains two sensor holes and the rear stays free of them. A native four-position countersink Hole feature preserves the ninety-degree seating angle during clearance edits. Frozen fastener envelope and physical clamp-stack limitations are separate.'}))
'''
r=rpc(s,'frame-tie-family-edit-restore',timeout=360);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/frame-tie-family-edit-restore.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'cases':len(record['edits']),'seconds':record['elapsed_seconds']},flush=True)
for path in record['paths']:fetch(path,Path(path).name)
