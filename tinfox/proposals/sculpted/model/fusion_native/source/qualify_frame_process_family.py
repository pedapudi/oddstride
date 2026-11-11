"""Verify coupled frame support, battery access width and separate process offsets."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;tick=time.monotonic();keys={'rail':'chassis_beam_102','brace':'chassis_lower_brace','deck':'electronics_shelf','cassette':'CANDIDATE_battery_cassette','skid':'CANDIDATE_battery_skid','belly':'belly_center_0'};parts={role:next(c for c in d.allComponents if c.partNumber==key) for role,key in keys.items()}
 def value(name):return d.userParameters.itemByName(name).value*10
 def measure():
  out={}
  for role,c in parts.items():
   assert c.bRepBodies.count==1;b=c.bRepBodies.item(0);box=b.boundingBox;row={'bounds':[v*10 for v in list(box.minPoint.asArray())+list(box.maxPoint.asArray())],'volume_mm3':b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000,'cylinders':[]}
   for face in b.faces:
    cylinder=core.Cylinder.cast(face.geometry)
    if cylinder:row['cylinders'].append({'origin':[v*10 for v in cylinder.origin.asArray()],'axis':list(cylinder.axis.asArray()),'radius':cylinder.radius*10})
   assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),(role,[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]);out[role]=row
  return out
 def near(a,b):assert abs(a-b)<.001,(a,b)
 def hole(row,axis,point,r):assert any(abs(c['axis'][axis])>.999999 and abs(c['radius']-r)<.0001 and all(abs(c['origin'][i]-point[i])<.0001 for i in range(3) if i!=axis) for c in row['cylinders']),(axis,point,r)
 baseline=measure();edits=[]
 for name,expr in [('frame_brace_thickness','4 mm'),('robot_roll_y','73 mm'),('frame_hole_process_compensation','.2 mm'),('deck_hole_process_compensation','.2 mm'),('frame_tap_hole_process_compensation','.1 mm')]:
  p=d.userParameters.itemByName(name);old=p.expression
  try:
   p.expression=expr;assert d.computeAll();edited=measure();half=value('frame_half_y');top=value('frame_brace_bottom_z')+value('frame_brace_thickness');near(edited['brace']['bounds'][2],.5);near(edited['brace']['bounds'][5],top);near(edited['deck']['bounds'][2],top);near(edited['deck']['bounds'][5],top+4)
   for sx in [-1,1]:
    hole(edited['rail'],2,[sx*63,half-5,0],value('frame_m3_tap_drill')/2)
    for sy in [-1,1]:hole(edited['brace'],2,[sx*63,sy*(half-5),0],value('frame_m3_clearance')/2);hole(edited['brace'],2,[sx*52,sy*(half-14),0],value('frame_m3_tap_drill')/2);hole(edited['deck'],2,[sx*52,sy*(half-14),0],value('deck_m3_clearance')/2)
    hole(edited['cassette'],1,[sx*52,0,-6],value('cassette_m3_clearance')/2);hole(edited['cassette'],1,[sx*50,0,-59],value('cassette_access_pilot_diameter')/2)
   near(value('belly_battery_aperture_depth'),2*half-2);near(edited['skid']['bounds'][1],-(half-7));near(edited['skid']['bounds'][4],half-7);near(value('belly_battery_aperture_depth')/2-value('cassette_half_y'),4)
   if name=='frame_brace_thickness':near(edited['rail']['volume_mm3'],baseline['rail']['volume_mm3']);near(edited['cassette']['volume_mm3'],baseline['cassette']['volume_mm3'])
   edits.append({'parameter':name,'expression':expr,'measurements':edited,'passed':True})
  finally:p.expression=old;assert d.computeAll()
  restored=measure();error=max(abs(a-b) for role in parts for a,b in zip(restored[role]['bounds'],baseline[role]['bounds']));assert error<.001;assert all(abs(restored[role]['volume_mm3']-baseline[role]['volume_mm3'])<max(.002,1e-7*baseline[role]['volume_mm3']) for role in parts);edits[-1]['restore_max_bounds_error_mm']=error
 paths=[]
 for role in ['brace','deck','belly','skid']:
  c=parts[role];occ=next(o for o in root.occurrences if o.component==c);visible=occ.isLightBulbOn;occ.isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','frame-process-'+keys[role].removeprefix('CANDIDATE_')+'-restored.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));occ.isLightBulbOn=visible;assert os.path.getsize(path)>10000;paths.append(path)
 print(json.dumps({'passed':True,'saved':False,'baseline':baseline,'edits':edits,'paths':paths,'elapsed_seconds':time.monotonic()-tick,'scope':'Bottom-anchored brace thickness, deck support, shared frame/battery access width and independent metal/deck hole compensation. Source screws remain nominal fixed-length references; thickness changes require checking engagement and choosing matching standard screws. Zero process offsets preserve source geometry and are not manufacturing recommendations.'}))
'''
r=rpc(s,'frame-process-family-edit-restore',timeout=420);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/frame-process-family-edit-restore.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'cases':len(record['edits']),'seconds':record['elapsed_seconds']},flush=True)
for path in record['paths']:fetch(path,Path(path).name)
