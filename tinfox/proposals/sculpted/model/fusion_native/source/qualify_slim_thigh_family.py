"""Exercise thigh size, wall, washer clearance and axle fit independently."""
import json,sys
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]

s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py'])+'''
def run(_context: str):
 import json,time,tempfile,os
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert d.activateRootComponent();comps={c.partNumber:c for c in d.allComponents if c.partNumber.startswith('CANDIDATE_sl_thigh_')};assert len(comps)==5;master=comps['CANDIDATE_sl_thigh_master'];tick=time.monotonic()
 def state():
  result={}
  for key,c in comps.items():
   assert c.bRepBodies.count==(2 if key.endswith('master') else 1);body=next((b for b in c.bRepBodies if b.name=='Closed thigh shared finished master'),c.bRepBodies.item(0));issues=[(f.name,f.errorOrWarningMessage)for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues;result[key]={'bounds_mm':[v*10 for v in body.boundingBox.minPoint.asArray()+body.boundingBox.maxPoint.asArray()],'volume_mm3':body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000}
  return result
 def cylinders():
  result=[]
  for f in comps['CANDIDATE_sl_thigh_outer'].bRepBodies.item(0).faces:
   cy=core.Cylinder.cast(f.geometry)
   if cy and abs(cy.axis.y)>.999:result.append({'radius_mm':cy.radius*10,'x_mm':cy.origin.x*10,'z_mm':cy.origin.z*10})
  return result
 baseline=state();tests=[]
 for name,value in [('lc_thigh_length','175 mm'),('st_wall','8.5 mm'),('st_clamp_washer_diametral_allowance','0.6 mm'),('st_axle_diametral_allowance','0.3 mm')]:
  p=d.userParameters.itemByName(name);old=p.expression;before=state()
  try:
   p.expression=value;assert d.computeAll();changed=state();cy=cylinders();seats=[x for x in cy if abs(x['x_mm'])<1e-5 and abs(x['z_mm']+d.userParameters.itemByName('lc_thigh_length').value*10)<1e-5 and 6<x['radius_mm']<6.2];expected=6.15 if name=='st_axle_diametral_allowance'else 6.1;assert len(seats)>=1 and all(abs(x['radius_mm']-expected)<1e-5 for x in seats)
   if name=='lc_thigh_length':assert all(r['bounds_mm'][2]<before[k]['bounds_mm'][2]-4.9 for k,r in changed.items())
   elif name=='st_wall':assert changed['CANDIDATE_sl_thigh_master']['volume_mm3']>before['CANDIDATE_sl_thigh_master']['volume_mm3']+50
   elif name=='st_clamp_washer_diametral_allowance':assert len([x for x in cy if abs(x['radius_mm']-6.3)<1e-5])>=2
   tests.append({'parameter':name,'value':value,'healthy':True,'axle_clearance_radius_mm':expected,'geometry':changed})
  finally:p.expression=old;assert d.computeAll()
  restored=state();errors={k:{'bounds_mm':max(abs(a-b)for a,b in zip(r['bounds_mm'],before[k]['bounds_mm'])),'volume_mm3':abs(r['volume_mm3']-before[k]['volume_mm3'])}for k,r in restored.items()};assert all(r['bounds_mm']<.002 and r['volume_mm3']<.0002*before[k]['volume_mm3']for k,r in errors.items());tests[-1]['restore_errors']=errors
 paths=[]
 print(json.dumps({'passed':True,'saved':False,'tests':tests,'paths':paths,'elapsed_seconds':time.monotonic()-tick,'scope':'Four meaningful edit/restore tests in the five-component thigh family. Hardware remains nominal; the diametral axle allowance is intentionally separate from nominal shaft OD. Process fits, preload, strength and CNC access are not qualified by this test.'}))
'''
tag='slim-thigh-family-edits'
r=rpc(s,tag,timeout=900);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits'/f'{tag}.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'tests':[q['parameter']for q in record['tests']]},flush=True)
for path in record['paths']:fetch(path,Path(path).name)
