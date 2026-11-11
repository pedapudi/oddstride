"""Exercise native low-head placement, wall and shared hardware interfaces."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json,time,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);components={c.partNumber:c for c in d.allComponents if c.partNumber.startswith('CANDIDATE_current_')};assert len(components)==3;tick=time.monotonic()
 def state():
  result={}
  for key,c in components.items():
   assert c.bRepBodies.count==1;issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,(key,issues);body=c.bRepBodies.item(0);result[key]={'bounds_mm':[min(getattr(v.geometry,a) for v in body.vertices)*10 for a in ['x','y','z']]+[max(getattr(v.geometry,a) for v in body.vertices)*10 for a in ['x','y','z']],'vertices':body.vertices.count,'features':c.features.count}
  hood=components['CANDIDATE_current_front_fascia'].bRepBodies.item(0);cradle=components['CANDIDATE_current_body_nose_surround'].bRepBodies.item(0);result['probes']={'wall':int(hood.pointContainment(core.Point3D.create(15,0,7.39))),'hood_m3':int(hood.pointContainment(core.Point3D.create(9.375,-2.5,7))),'cradle_m3':int(cradle.pointContainment(core.Point3D.create(9.375,-2.5,5.7))),'cradle_m4':int(cradle.pointContainment(core.Point3D.create(12.325,2.4,4.5)))};return result
 baseline=state();rows=[]
 for name,value in [('body_hip_x','190 mm'),('hood_wall','4.2 mm'),('saddle_fastener_diametral_clearance','.6 mm'),('head_face_vertical_crown','11 mm')]:
  p=d.userParameters.itemByName(name);old=p.expression;p.expression=value;assert d.computeAll();edited=state()
  if name=='body_hip_x':
   for key in components:assert max(abs((b-a)-(5 if i in [0,3] else0)) for i,(a,b) in enumerate(zip(baseline[key]['bounds_mm'],edited[key]['bounds_mm'])))<.005,(name,key,baseline[key],edited[key])
  elif name=='hood_wall':assert baseline['probes']['wall']==2 and edited['probes']['wall']==0,(baseline['probes'],edited['probes'])
  elif name=='saddle_fastener_diametral_clearance':assert all(baseline['probes'][k]==0 and edited['probes'][k]==2 for k in ['hood_m3','cradle_m3','cradle_m4']),(baseline['probes'],edited['probes'])
  else:assert edited['CANDIDATE_current_front_fascia']['bounds_mm'][3]-baseline['CANDIDATE_current_front_fascia']['bounds_mm'][3]>.5
  p.expression=old;assert d.computeAll();restored=state();errors={key:max(abs(a-b) for a,b in zip(restored[key]['bounds_mm'],baseline[key]['bounds_mm'])) for key in components};assert max(errors.values())<.005,(name,errors);rows.append({'parameter':name,'value':value,'restored_expression':old,'edited':edited,'restored_vertex_bounds_error_mm':errors,'passed':True})
 paths=[]
 for key,label in [('CANDIDATE_current_front_fascia','current-sensor-hood-restored'),('CANDIDATE_current_body_nose_surround','current-sensor-cradle-restored')]:
  path=os.path.join(tempfile.gettempdir(),'tinfox-native',label+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,components[key]));paths.append(path)
 print(json.dumps({'passed':True,'saved':False,'baseline':baseline,'tests':rows,'paths':paths,'elapsed_seconds':time.monotonic()-tick,'scope':'Current Head geometry family only. Restored exports still require full surface/section/silhouette audits. External subsystem and selected hardware variation qualification remain separate.'}))
'''.replace('else0','else 0')
r=rpc(s,'current-head-family-qualification',timeout=900);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-head-family-qualification.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'tests':len(record['tests']),'elapsed_seconds':record['elapsed_seconds']})
for path in record['paths']:fetch(path,Path(path).name)
