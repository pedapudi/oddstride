"""Test shared enclosure dimensions and the independent shell seam allowance."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json,time,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:R7U8KNNBSA6o3YwVNF2ZQQ';d=fusion.Design.cast(app.activeProduct);lower=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_compact_belly_center_0');upper=next(c for c in d.allComponents if c.partNumber=='body_center_0');tick=time.monotonic()
 def inspect(c):
  assert c.bRepBodies.count==1;issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues;b=c.bRepBodies.item(0);pts=[v.geometry for v in b.vertices];bounds=[min(getattr(p,a) for p in pts)*10 for a in ['x','y','z']]+[max(getattr(p,a) for p in pts)*10 for a in ['x','y','z']];return {'bounds_mm':bounds,'volume_mm3':b.volume*1000,'features':c.features.count,'faces':b.faces.count}
 def state():return {'lower':inspect(lower),'upper':inspect(upper),'motor_radius_mm':d.userParameters.itemByName('body_roll_case_radius').value*10,'motor_setback_mm':d.userParameters.itemByName('body_roll_output_setback').value*10}
 baseline=state();rows=[]
 for name,expr,axis,delta in [('cover_hip_x','195 mm',0,10),('cover_roll_y','73 mm',1,5),('cover_wall','3.2 mm',None,None),('body_shell_seam_gap','.5 mm',None,None)]:
  t=time.monotonic();p=d.userParameters.itemByName(name);old=p.expression;p.expression=expr;automatic=state()
  if not rows:
   assert d.computeAll();edited=state();error=max(abs(a-b) for role in ['lower','upper'] for a,b in zip(automatic[role]['bounds_mm'],edited[role]['bounds_mm']));assert error<1e-5;automatic_volume_error=abs(automatic['lower']['volume_mm3']-edited['lower']['volume_mm3']);assert automatic_volume_error<.01
  else:edited=automatic
  if axis is not None:
   for role in ['lower','upper']:
    assert abs(edited[role]['bounds_mm'][axis]-baseline[role]['bounds_mm'][axis]+delta)<.01,(name,role,edited,baseline);assert abs(edited[role]['bounds_mm'][axis+3]-baseline[role]['bounds_mm'][axis+3]-delta)<.01
  elif name=='cover_wall':assert edited['lower']['volume_mm3']>baseline['lower']['volume_mm3']+1000;assert max(abs(a-b) for a,b in zip(edited['lower']['bounds_mm'],baseline['lower']['bounds_mm']))<1e-5
  else:
   assert abs(edited['lower']['bounds_mm'][5]-baseline['lower']['bounds_mm'][5]+.2)<1e-5;assert max(abs(a-b) for a,b in zip(edited['upper']['bounds_mm'],baseline['upper']['bounds_mm']))<1e-5
  assert edited['motor_radius_mm']==baseline['motor_radius_mm'] and edited['motor_setback_mm']==baseline['motor_setback_mm'];p.expression=old;restored=state();assert max(abs(a-b) for role in ['lower','upper'] for a,b in zip(restored[role]['bounds_mm'],baseline[role]['bounds_mm']))<1e-5;assert abs(restored['lower']['volume_mm3']-baseline['lower']['volume_mm3'])<.01;rows.append({'parameter':name,'expression':expr,'edited':edited,'restored':True,'elapsed_seconds':time.monotonic()-t})
 assert d.computeAll();restored=state();assert abs(restored['lower']['volume_mm3']-baseline['lower']['volume_mm3'])<.01;occ=next(o for o in d.rootComponent.occurrences if o.component==lower);visible=occ.isLightBulbOn;occ.isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','compact-lower-shell-restored.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,lower));occ.isLightBulbOn=visible;assert os.path.getsize(path)>50000
 print(json.dumps({'passed':True,'saved':False,'baseline':baseline,'edits':rows,'automatic_recompute_verified_against_computeAll':True,'automatic_lower_volume_error_mm3':automatic_volume_error,'path':path,'elapsed_seconds':time.monotonic()-tick,'scope':'Shared upper/lower enclosure hip spacing, width, wall and seam edits; selected motor interface dimensions stay independent. No whole-chassis size or structural load qualification.'}))
'''
r=rpc(s,'compact-lower-shell-family-qualification',timeout=900);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/compact-lower-shell-family-qualification.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'edits':len(record['edits']),'seconds':record['elapsed_seconds']});fetch(record['path'],Path(record['path']).name)
