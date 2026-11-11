"""Exercise shared bearing spacing and independent retention fit dimensions."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py'])+'''
def run(_context: str):
 import json,time
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();tick=time.monotonic();comps={c.partNumber:c for c in d.allComponents if c.partNumber.startswith('CANDIDATE_pr_')};assert len(comps)==16
 def state():
  rows={}
  for key,c in comps.items():
   assert c.bRepBodies.count==1;issues=[(f.name,f.errorOrWarningMessage)for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues;b=c.bRepBodies.item(0);rows[key]={'bounds_mm':[v*10 for v in b.boundingBox.minPoint.asArray()+b.boundingBox.maxPoint.asArray()],'volume_mm3':b.volume*1000}
  return rows
 def radius(key,expected):
  c=comps['CANDIDATE_pr_'+key];values=[]
  for face in c.bRepBodies.item(0).faces:
   cylinder=core.Cylinder.cast(face.geometry)
   if cylinder and abs(cylinder.axis.x)>.999:values.append(cylinder.radius*10)
  assert any(abs(v-expected)<1e-5 for v in values),(key,values,expected)
 baseline=state();tests=[];nominal={p:d.userParameters.itemByName(p).expression for p in ['pr_bearing_id','pr_bearing_od','pr_bearing_width']}
 for name,value in [('pr_bearing_center_span','15 mm'),('pr_spacer_diametral_clearance','0.2 mm'),('pr_retainer_thickness','2.5 mm')]:
  p=d.userParameters.itemByName(name);old=p.expression
  try:
   p.expression=value;assert d.computeAll();changed=state()
   if name=='pr_bearing_center_span':
    for part in ['roll_inner_spacer_1','roll_outer_spacer_1']:
     b=changed['CANDIDATE_pr_'+part]['bounds_mm'];assert abs(b[3]-b[0]-8)<1e-5
    b=changed['CANDIDATE_pr_roll_outer_retainer_1']['bounds_mm'];assert abs(b[0]+49.5)<1e-5
   elif name=='pr_spacer_diametral_clearance':radius('roll_inner_spacer_1',25.1);radius('roll_outer_spacer_1',32.4)
   else:
    b=changed['CANDIDATE_pr_roll_outer_retainer_1']['bounds_mm'];assert abs(b[3]-b[0]-2.5)<1e-5
   assert all(d.userParameters.itemByName(n).expression==v for n,v in nominal.items());tests.append({'parameter':name,'edited_value':value,'healthy':True,'nominal_hardware_unchanged':True})
  finally:p.expression=old;assert d.computeAll()
  restored=state();errors={k:{'bounds_mm':max(abs(a-b)for a,b in zip(r['bounds_mm'],baseline[k]['bounds_mm'])),'volume_mm3':abs(r['volume_mm3']-baseline[k]['volume_mm3'])}for k,r in restored.items()};assert all(v['bounds_mm']<1e-5 and v['volume_mm3']<1e-4 for v in errors.values()),errors;tests[-1]['restore_errors']=errors
 print(json.dumps({'passed':True,'saved':False,'tests':tests,'definitions':len(comps),'elapsed_seconds':time.monotonic()-tick,'scope':'Bearing race spacer/retention family edits only. Housing stack, preload, process fits and strength require separate checks.'}))
'''
r=rpc(s,'paired-retention-family-edits',timeout=600);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/paired-retention-family-edits.json').write_text(json.dumps(record,indent=2));print(record)
