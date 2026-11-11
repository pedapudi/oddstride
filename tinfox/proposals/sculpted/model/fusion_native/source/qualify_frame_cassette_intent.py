"""Exercise cassette width, independent hole compensation and accessible nut fits."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
assert json.loads((ROOT/'audits/frame-intent-battery-cassette-geometry.json').read_text())['geometric_gate_passed']
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_battery_cassette');tick=time.monotonic()
 def measure():
  assert c.bRepBodies.count==1;b=c.bRepBodies.item(0);box=b.boundingBox;row={'bounds':[v*10 for v in [box.minPoint.x,box.minPoint.y,box.minPoint.z,box.maxPoint.x,box.maxPoint.y,box.maxPoint.z]],'volume_mm3':b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000,'y_cylinders':[]}
  for face in b.faces:
   cylinder=core.Cylinder.cast(face.geometry)
   if cylinder and abs(cylinder.axis.y)>.999999:row['y_cylinders'].append({'x':cylinder.origin.x*10,'z':cylinder.origin.z*10,'radius':cylinder.radius*10})
  assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);return row
 def hole(row,x,z,r):assert any(abs(p['x']-x)<.0001 and abs(p['z']-z)<.0001 and abs(p['radius']-r)<.0001 for p in row['y_cylinders']),(x,z,r,row['y_cylinders'])
 def contains(x,y,z):return c.bRepBodies.item(0).pointContainment(core.Point3D.create(x/10,y/10,z/10))==fusion.PointContainment.PointInsidePointContainment
 def value(name):return d.userParameters.itemByName(name).value*10
 baseline=measure();edits=[]
 cases=[('robot_roll_y','73 mm'),('robot_fastener_diametral_allowance','.6 mm'),('cassette_hole_process_compensation','.2 mm'),('cassette_pilot_process_compensation','.1 mm'),('cassette_nut_af_process_compensation','.2 mm'),('cassette_nut_axial_process_compensation','.2 mm')]
 for name,expr in cases:
  p=d.userParameters.itemByName(name);old=p.expression;af_probe=(55.0,93.8,-6);axial_probe=(54.5,95.25,-6)
  if name=='cassette_nut_af_process_compensation':af_probe=(54.95,93.8,-6);assert contains(*af_probe)
  if name=='cassette_nut_axial_process_compensation':assert contains(*axial_probe)
  try:
   p.expression=expr;assert d.computeAll();edited=measure();target=list(baseline['bounds'])
   if name=='robot_roll_y':target[1]-=5;target[4]+=5
   assert max(abs(a-b) for a,b in zip(edited['bounds'],target))<.001,(name,edited['bounds'],target)
   for sx in [-1,1]:hole(edited,sx*52,-6,value('cassette_m3_clearance')/2);hole(edited,sx*50,-59,value('cassette_access_pilot_diameter')/2)
   if name=='cassette_nut_af_process_compensation':assert not contains(*af_probe)
   if name=='cassette_nut_axial_process_compensation':assert not contains(*axial_probe)
   edits.append({'parameter':name,'edited_expression':expr,'measurements':edited,'passed':True})
  finally:p.expression=old;assert d.computeAll()
  restored=measure();error=max(abs(a-b) for a,b in zip(restored['bounds'],baseline['bounds']));assert error<.001,(name,'bounds_restore',error);delta=abs(restored['volume_mm3']-baseline['volume_mm3']);assert delta<max(.001,1e-7*baseline['volume_mm3']),(name,'volume_restore',restored['volume_mm3'],baseline['volume_mm3']);edits[-1]['restore_max_bounds_error_mm']=error;edits[-1]['high_accuracy_volume_restore_difference_mm3']=delta
 occurrence=next(o for o in root.occurrences if o.component==c);visible=occurrence.isLightBulbOn;occurrence.isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','frame-intent-battery-cassette-restored.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));occurrence.isLightBulbOn=visible;assert os.path.getsize(path)>10000
 print(json.dumps({'passed':True,'saved':False,'baseline':baseline,'edits':edits,'paths':[path],'elapsed_seconds':time.monotonic()-tick,'scope':'Native cassette feature propagation and restoration; zero process compensation reproduces frozen geometry. This does not qualify printed fit, selected batteries, frame width hardware placement or physical load capability.'}))
'''
r=rpc(s,'frame-cassette-family-edit-restore',timeout=360);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/frame-cassette-family-edit-restore.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'cases':len(record['edits']),'seconds':record['elapsed_seconds']},flush=True)
for path in record['paths']:fetch(path,Path(path).name)
