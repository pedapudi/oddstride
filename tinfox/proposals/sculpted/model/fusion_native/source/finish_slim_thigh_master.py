"""Finish the common thigh and create its shared manufacturing split."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py','native_nonuniform_spline.py','cohesive_limb_intent.py','cohesive_thigh_intent.py','slim_thigh_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile,time
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_sl_thigh_master');assert c.bRepBodies.count==2;body=next(b for b in c.bRepBodies if b.name=='Closed thigh with integral motor and knee interfaces');fill=next(b for b in c.bRepBodies if b.name=='Construction continuous exterior stock');tick=time.monotonic();n=SlimThighIntent(IntentGeometry(d,c));body=n.continuous_exterior(body,fill);body=n.connector_access(body);body.name='Closed thigh shared finished master';mask=n.split_mask();assert c.bRepBodies.count==2;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features)
 o=next(o for o in root.occurrences if o.component==c);light=o.isLightBulbOn;o.isLightBulbOn=True;paths=[]
 for selected,label in [(body,'slim-thigh-master'),(mask,'slim-thigh-split-mask')]:
  for b in c.bRepBodies:b.isLightBulbOn=b==selected
  path=os.path.join(tempfile.gettempdir(),'tinfox-native',label+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>5000;paths.append(path)
 mask.isLightBulbOn=False;body.isLightBulbOn=True;o.isLightBulbOn=light
 print(json.dumps({'saved':False,'paths':paths,'features':c.features.count,'sketches':c.sketches.count,'volume_mm3':body.volume*1000,'elapsed_seconds':time.monotonic()-tick,'scope':'Shared completed thigh and manufacturing split; final half-specific bearing and washer seats remain.'}))
'''
r=rpc(s,'slim-thigh-finished-master',timeout=900);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/slim-thigh-finished-master.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
for path in record['paths']:fetch(path,Path(path).name)
