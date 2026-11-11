"""Exercise physical cover dimensions and restore the frozen geometry."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json,time,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:R7U8KNNBSA6o3YwVNF2ZQQ';d=fusion.Design.cast(app.activeProduct);c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_current_body_center_0');tick=time.monotonic()
 def inspect():
  assert c.bRepBodies.count==1;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];b=c.bRepBodies.item(0);points=[v.geometry for v in b.vertices];bounds=[min(getattr(p,a) for p in points)*10 for a in ['x','y','z']]+[max(getattr(p,a) for p in points)*10 for a in ['x','y','z']];return {'vertex_bounds_mm':bounds,'volume_cm3':b.getPhysicalProperties(fusion.CalculationAccuracy.HighCalculationAccuracy).volume,'wall_probe_state':int(b.pointContainment(core.Point3D.create(0,10.825,2))),'features':c.features.count,'faces':b.faces.count}
 baseline=inspect();rows=[]
 for name,expr,axis,delta in [('cover_hip_x','195 mm',0,10),('cover_roll_y','73 mm',1,5),('cover_wall','3.2 mm',None,None)]:
  p=d.userParameters.itemByName(name);old=p.expression;p.expression=expr;assert d.computeAll();edited=inspect()
  if axis is not None:
   assert abs(edited['vertex_bounds_mm'][axis]-baseline['vertex_bounds_mm'][axis]+delta)<.01,(name,edited,baseline);assert abs(edited['vertex_bounds_mm'][axis+3]-baseline['vertex_bounds_mm'][axis+3]-delta)<.01
  else:assert baseline['wall_probe_state']==2 and edited['wall_probe_state']==0,(baseline,edited)
  p.expression=old;assert d.computeAll();restored=inspect();assert max(abs(a-b) for a,b in zip(restored['vertex_bounds_mm'],baseline['vertex_bounds_mm']))<1e-5;rows.append({'parameter':name,'expression':expr,'edited':edited,'restored':True,'restored_vertex_bounds_error_mm':max(abs(a-b) for a,b in zip(restored['vertex_bounds_mm'],baseline['vertex_bounds_mm'])),'native_reported_volume_delta_cm3':restored['volume_cm3']-baseline['volume_cm3']})
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','current-body-cover-restored.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c))
 print(json.dumps({'path':path,'native_volume_note':'Native physical-property quadrature is unstable for this roof. Restored STEP full-surface and adaptive integral audit is required.','passed':True,'saved':False,'baseline':baseline,'edits':rows,'elapsed_seconds':time.monotonic()-tick,'scope':'Three meaningful cover-family edits and exact baseline restoration. Whole chassis/vendor placement and manufactured strength remain separate.'}))
'''
r=rpc(s,'current-cover-family-qualification',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-cover-family-qualification.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'edits':len(record['edits']),'elapsed_seconds':record['elapsed_seconds']})

fetch(record['path'],Path(record['path']).name)
