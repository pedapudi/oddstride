"""Verify frame, split-height and shared fastener-clearance edits in native geometry."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json,time,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_current_body_nose_surround');tick=time.monotonic()
 def check():
  assert c.bRepBodies.count==1 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);b=c.bRepBodies.item(0);return {'volume_cm3':b.volume,'bounds_mm':[v*10 for v in b.boundingBox.minPoint.asArray()+b.boundingBox.maxPoint.asArray()],'M3_wall_probe':int(b.pointContainment(core.Point3D.create(9.375,-2.5,5.7))),'M4_wall_probe':int(b.pointContainment(core.Point3D.create(12.325,2.4,4.5)))}
 baseline=check();rows=[]
 for name,expr in [('saddle_x','126 mm'),('saddle_split_z','62 mm'),('saddle_fastener_diametral_clearance','.6 mm')]:
  p=d.userParameters.itemByName(name);old=p.expression;p.expression=expr;assert d.computeAll();edited=check()
  if name=='saddle_x':assert abs(edited['bounds_mm'][0]-baseline['bounds_mm'][0]-5)<1e-6 and abs(edited['bounds_mm'][3]-baseline['bounds_mm'][3]-5)<1e-6
  elif name=='saddle_split_z':assert abs(edited['bounds_mm'][5]-baseline['bounds_mm'][5]-2)<1e-6 and abs(edited['bounds_mm'][2]-baseline['bounds_mm'][2])<1e-6
  else:assert baseline['M3_wall_probe']==0 and baseline['M4_wall_probe']==0 and edited['M3_wall_probe']==2 and edited['M4_wall_probe']==2,(baseline,edited)
  p.expression=old;assert d.computeAll();restored=check();assert max(abs(a-b) for a,b in zip(restored['bounds_mm'],baseline['bounds_mm']))<1e-6;assert abs(restored['volume_cm3']-baseline['volume_cm3'])<1e-7;rows.append({'parameter':name,'expression':expr,'edited':edited,'restored':True})
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','current-sensor-cradle-restored.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));print(json.dumps({'passed':True,'saved':False,'baseline':baseline,'edits':rows,'path':path,'elapsed_seconds':time.monotonic()-tick,'scope':'Sensor cradle geometry and two shared fastener interfaces. Manufactured process fits and complete Head assembly remain unqualified.'}))
'''
r=rpc(s,'current-sensor-cradle-family-qualification',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-sensor-cradle-family-qualification.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'edits':len(record['edits']),'elapsed_seconds':record['elapsed_seconds']});fetch(record['path'],Path(record['path']).name)
