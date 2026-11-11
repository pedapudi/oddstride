"""Use a revolved crown and retain the original whole-limb material envelope."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py','native_nonuniform_spline.py','cohesive_limb_intent.py','cohesive_thigh_intent.py','slim_thigh_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile,time
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;tick=time.monotonic();master=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_sl_thigh_master');g=IntentGeometry(d,master)
 cut=next(f for f in master.features if f.name=='Continuous exterior stock above the waist');join=next(f for f in master.features if f.name=='Continuous thigh exterior without a roof depression');cut.timelineObject.rollTo(True);assert master.bRepBodies.count==3;envelope=next(b for b in master.bRepBodies if b.name=='Construction continuous exterior stock');objects=core.ObjectCollection.create();objects.add(envelope);copy=master.features.copyPasteBodies.add(objects);copy.name='Preserve the original whole-limb material envelope';limit=copy.bodies.item(0);limit.name='Construction material envelope';join.timelineObject.rollTo(False);body=next(b for b in master.bRepBodies if b!=limit);body=g.combine(body,[limit],fusion.FeatureOperations.IntersectFeatureOperation,'Keep the final exterior inside the shared material envelope');d.timeline.moveToEnd();assert d.computeAll()
 c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_sl_thigh_outer');old=next(f for f in c.features.loftFeatures if f.name=='Three-section integral knee crown');old.timelineObject.rollTo(True);assert c.bRepBodies.count==1;n=SlimThighIntent(IntentGeometry(d,c));n.crown_revolve(c.bRepBodies.item(0));assert old.deleteMe();d.timeline.moveToEnd();assert d.computeAll()
 for name in ['Knee crown root','Knee crown middle','Knee crown end']:
  sk=next(sk for sk in c.sketches if sk.name==name);assert sk.deleteMe()
 for name in ['Knee crown root datum','Knee crown middle datum','Knee crown end datum']:
  plane=next(p for p in c.constructionPlanes if p.name==name);assert plane.deleteMe()
 assert d.computeAll();rows=[];paths=[]
 for key in ['thigh_inner','thigh_outer','thigh_inner_right','thigh_outer_right']:
  c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_sl_'+key);assert c.bRepBodies.count==1;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);o=next(o for o in root.occurrences if o.component==c);light=o.isLightBulbOn;o.isLightBulbOn=True;c.bRepBodies.item(0).isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','slim-native-'+key+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));o.isLightBulbOn=light;assert os.path.getsize(path)>5000;paths.append(path);rows.append({'part':key,'features':c.features.count,'sketches':c.sketches.count,'faces':c.bRepBodies.item(0).faces.count})
 print(json.dumps({'saved':False,'parts':rows,'paths':paths,'elapsed_seconds':time.monotonic()-tick,'scope':'Parsimonious crown interpolation and a shared-envelope constraint; original shape thresholds remain unchanged. The separately approved outer-knee stub cleanup is the comparison overlay.'}))
'''
r=rpc(s,'slim-thigh-surface-refinement',timeout=900);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/slim-thigh-surface-refinement.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
for path in record['paths']:fetch(path,Path(path).name)
