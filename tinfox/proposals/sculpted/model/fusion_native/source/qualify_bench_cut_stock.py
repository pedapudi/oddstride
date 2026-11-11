"""Check native cut-stock dimensions and their functional datum dependencies."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py'])+'''
def run(_context: str):
 import json,time
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();tick=time.monotonic();comps={c.partNumber:c for c in d.allComponents if c.partNumber.startswith('CANDIDATE_bt_')};assert len(comps)==12
 def state():
  rows={}
  for key,c in comps.items():
   assert c.bRepBodies.count==(2 if 'pod_sleeve' in key else 1);issues=[(f.name,f.errorOrWarningMessage)for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues
   rows[key]=[{'bounds_mm':[v*10 for v in b.boundingBox.minPoint.asArray()+b.boundingBox.maxPoint.asArray()],'volume_mm3':b.volume*1000}for b in c.bRepBodies]
  return rows
 baseline=state();tests=[];nominal={p:d.userParameters.itemByName(p).expression for p in ['bt_knee_axle_od','bt_pod_od','bt_clamp_od','lc_bearing_od','lc_bearing_width']}
 for name,value in [('bt_knee_axle_id','5.6 mm'),('bt_clamp_id','4.4 mm'),('bt_pod_short_length','6.5 mm')]:
  p=d.userParameters.itemByName(name);old=p.expression
  try:
   p.expression=value;assert d.computeAll();changed=state();affected=[k for k in comps if any(abs(a['volume_mm3']-b['volume_mm3'])>1e-5 for a,b in zip(changed[k],baseline[k]))];expected=[k for k in comps if ('knee_axle' in k if name=='bt_knee_axle_id' else ('sleeve_' in k and 'pod_' not in k) if name=='bt_clamp_id' else 'pod_sleeve' in k)];assert sorted(affected)==sorted(expected),(affected,expected);assert all(d.userParameters.itemByName(n).expression==v for n,v in nominal.items());tests.append({'parameter':name,'edited_value':value,'affected_definitions':affected,'healthy':True,'nominal_hardware_unchanged':True})
  finally:p.expression=old;assert d.computeAll()
  restored=state();errors={k:max([abs(a['volume_mm3']-b['volume_mm3'])for a,b in zip(restored[k],baseline[k])]+[abs(x-y)for a,b in zip(restored[k],baseline[k])for x,y in zip(a['bounds_mm'],b['bounds_mm'])])for k in comps};assert max(errors.values())<1e-4,errors;tests[-1]['restore_max_errors']=errors
 print(json.dumps({'passed':True,'saved':False,'tests':tests,'definitions':len(comps),'elapsed_seconds':time.monotonic()-tick,'scope':'Independent stock dimensions and handed propagation. Clamp preload, material strength and manufacturing tolerances remain unqualified.'}))
'''
r=rpc(s,'bench-cut-stock-family-edits',timeout=600);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/bench-cut-stock-family-edits.json').write_text(json.dumps(record,indent=2));print(record)
