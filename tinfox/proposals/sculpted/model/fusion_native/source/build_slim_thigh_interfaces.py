"""Add integral structural lands and the shared motor/linkage interfaces."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text() for p in ['native_documents.py','intent_geometry.py','native_nonuniform_spline.py','cohesive_limb_intent.py','cohesive_thigh_intent.py','slim_thigh_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile,time
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_sl_thigh_master');assert c.bRepBodies.count==3;body=next(b for b in c.bRepBodies if b.name=='Closed thigh structural stock');lands=next(b for b in c.bRepBodies if b.name=='Construction land clipping stock');outline=next(b for b in c.bRepBodies if b.name=='Construction continuous exterior stock');tick=time.monotonic();builder=SlimThighIntent(IntentGeometry(d,c));body=builder.structural_lands(body,lands,outline);body=builder.motor_and_linkage_interfaces(body);body.name='Closed thigh with integral motor and knee interfaces';assert c.bRepBodies.count==2;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features)
 o=next(o for o in root.occurrences if o.component==c);light=o.isLightBulbOn;o.isLightBulbOn=True
 for b in c.bRepBodies:b.isLightBulbOn=b==body
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','slim-thigh-functional-stock.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>5000;o.isLightBulbOn=light
 print(json.dumps({'saved':False,'path':path,'features':c.features.count,'sketches':c.sketches.count,'body_volume_mm3':body.volume*1000,'elapsed_seconds':time.monotonic()-tick,'scope':'Native integral lands, motor pockets and linkage clearance; connectors, shell splits and final bearing/clamp seats follow.'}))
'''
r=rpc(s,'slim-thigh-functional-stock',timeout=900);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/slim-thigh-functional-stock.json').write_text(json.dumps(record,indent=2));print(record,flush=True);fetch(record['path'],Path(record['path']).name)
