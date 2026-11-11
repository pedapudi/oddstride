"""Exercise the shared rear-lug depth and retain exact restored exports for comparison."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,time
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;keys=['hip_stator_closure_1','motor_carrier_1','motor_carrier_-1'];parts={key:next(c for c in d.allComponents if c.partNumber=='CANDIDATE_rc_'+key)for key in keys};p=d.userParameters.itemByName('rc_lug_back_extension');old=p.expression;tick=time.monotonic()
 def capture():
  rows={}
  for key,c in parts.items():
   assert c.bRepBodies.count==1 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);b=c.bRepBodies.item(0);bb=b.boundingBox;seats=[];radius=4.95 if key.startswith('hip_')else 4.8
   for f in b.faces:
    cylinder=core.Cylinder.cast(f.geometry)
    if cylinder and abs(cylinder.radius*10-radius)<1e-6 and abs(abs(cylinder.axis.y)-1)<1e-6:seats.append([f.boundingBox.minPoint.y*10,f.boundingBox.maxPoint.y*10])
   assert len(seats)==3,(key,seats);rows[key]={'bounds_mm':[v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]],'seat_y_mm':sorted(seats),'volume_mm3':b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000,'vertices_mm':sorted([list(v.geometry.asArray())for v in b.vertices]),'faces':b.faces.count,'features':c.features.count}
  return rows
 before=capture()
 try:
  p.expression='1.2 mm';assert d.computeAll();changed=capture()
  for key in keys:
   for initial,current in zip(before[key]['seat_y_mm'],changed[key]['seat_y_mm']):assert all(abs(b-a+.1)<1e-5 for a,b in zip(initial,current)),(key,initial,current)
 finally:p.expression=old;assert d.computeAll()
 restored=capture();exports=[]
 for key,c in parts.items():
  assert before[key]['faces']==restored[key]['faces'] and before[key]['features']==restored[key]['features'];assert max(abs(a-b)for a,b in zip(before[key]['bounds_mm'],restored[key]['bounds_mm']))<1e-5;assert len(before[key]['vertices_mm'])==len(restored[key]['vertices_mm']);assert max(abs(a-b)*10 for x,y in zip(before[key]['vertices_mm'],restored[key]['vertices_mm'])for a,b in zip(x,y))<1e-5
  o=next(o for o in root.occurrences if o.component==c);visibility=o.isLightBulbOn;o.isLightBulbOn=True;c.bRepBodies.item(0).isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','recessed-restored-'+key+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>10000;o.isLightBulbOn=visibility;exports.append({'part':key,'path':path,'native_volume_drift_mm3':restored[key]['volume_mm3']-before[key]['volume_mm3']})
 print(json.dumps({'passed':False,'native_edit_restore_passed':True,'pending':'Independent restored STEP volume and surface comparison','parameter':'rc_lug_back_extension','edit_mm':[1.1,1.2,1.1],'original_expression':old,'saved_version':doc.dataFile.versionNumber,'working_modified':doc.isModified,'before':before,'changed':changed,'restored':restored,'exports':exports,'elapsed_seconds':time.monotonic()-tick}))
'''
compile(s,'recessed_closure_family.py','exec');r=rpc(s,'recessed-closure-family-edit-restore',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/recessed-closure-family-edit-restore.json').write_text(json.dumps(record,indent=2))
for row in record['exports']:fetch(row['path'],Path(row['path']).name)
print({'native_edit_restore_passed':True,'native_volume_drifts_mm3':[r['native_volume_drift_mm3']for r in record['exports']]})
