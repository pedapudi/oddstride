"""Remove the redundant envelope operation after live-solid trim verification."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,time
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);master=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_sl_thigh_master');before=master.features.count
 for name in ['Keep the final exterior inside the shared material envelope','Preserve the original whole-limb material envelope']:
  feature=next(f for f in master.features if f.name==name);assert feature.deleteMe()
 d.timeline.moveToEnd();assert d.computeAll();assert master.features.count==before-2;rows=[];paths=[]
 for key in ['thigh_inner','thigh_outer','thigh_inner_right','thigh_outer_right']:
  c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_sl_'+key);assert c.bRepBodies.count==1;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);o=next(o for o in d.rootComponent.occurrences if o.component==c);light=o.isLightBulbOn;o.isLightBulbOn=True;c.bRepBodies.item(0).isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','slim-native-'+key+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));o.isLightBulbOn=light;paths.append(path);rows.append({'part':key,'features':c.features.count,'sketches':c.sketches.count,'faces':c.bRepBodies.item(0).faces.count})
 print(json.dumps({'saved':False,'parts':rows,'paths':paths,'removed_features':2,'reason':'The disputed STEP trim witness is outside the actual native solid. A redundant intersection did not change the export anomaly and is not retained as a design feature.'}))
'''
r=rpc(s,'remove-thigh-envelope-diagnostic',timeout=300);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/remove-thigh-envelope-diagnostic.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
for path in record['paths']:fetch(path,Path(path).name)
