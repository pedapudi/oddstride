"""Finish the shared native thigh's mounting columns, clamp lands and split."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
files=['native_documents.py','intent_geometry.py','native_nonuniform_spline.py','cohesive_limb_intent.py','cohesive_thigh_intent.py','slim_thigh_intent.py','dfma_thigh_intent.py']
s='\n'.join((ROOT/'source'/p).read_text()for p in files)+'''
def run(_context:str):
 import json,time
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);d.activateRootComponent();c=next(c for c in d.allComponents if c.partNumber=='DFMA_THIGH_SEED_FL');assert c.bRepBodies.count==2;body=next(b for b in c.bRepBodies if b.name=='DFMA motor core and structural envelope');envelope=next(b for b in c.bRepBodies if b.name=='DFMA exterior clipping envelope');tick=time.monotonic();last=c.features.item(c.features.count-1);assert last.timelineObject.rollTo(False)
 try:
  builder=DfmaThighIntent(IntentGeometry(d,c));builder.dfma_parameters()
  for name,expression in {'dfma_thigh_upper_end_z':'-(90/170)*lc_thigh_length','dfma_thigh_lower_join_z':'-(85/170)*lc_thigh_length','dfma_thigh_split_bottom_z':'-(70/170)*lc_thigh_length'}.items():
   p=d.userParameters.itemByName(name);old=p.value
   if p.expression!=expression:p.expression=expression
   assert abs(p.value-old)<1e-8
  for name,expression in {'dfma_thigh_column_radius':'8 mm','dfma_thigh_tube_length':'34 mm','dfma_thigh_long_head_floor_y':'dfma_thigh_washer_floor_y+dfma_thigh_washer_thickness'}.items():
   p=d.userParameters.itemByName(name)
   if p.expression!=expression:p.expression=expression
  body=builder.finish_upper(body,envelope);assert c.bRepBodies.count==1 and body.isSolid
  for sk in c.sketches:sk.isVisible=False
  for p in c.constructionPlanes:p.isLightBulbOn=False
 finally:d.timeline.moveToEnd()
 assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);print(json.dumps({'part_number':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'bodies':[{'name':b.name,'faces':b.faces.count}for b in c.bRepBodies],'saved':False,'seconds':time.monotonic()-tick,'scope':'Hidden shared native stock and split; these are construction bodies, not fabricated pieces.'}))
'''
if __name__=='__main__':
 r=rpc(s,'dfma-thigh-master-finished',timeout=1800);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/dfma-thigh-master-finished.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
 s2='\n'.join((ROOT/'source'/p).read_text()for p in files)+'''
def run(_context:str):
 import json,time
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);d.activateRootComponent();d.activateRootComponent();c=next(c for c in d.allComponents if c.partNumber=='DFMA_THIGH_SEED_FL');assert c.bRepBodies.count==1;assert c.bRepBodies.item(0).name=='DFMA shared proximal structural limb';tick=time.monotonic();assert c.features.item(c.features.count-1).timelineObject.rollTo(False)
 try:
  mask=DfmaThighIntent(IntentGeometry(d,c)).split_mask();assert c.bRepBodies.count==2 and mask.isSolid
  for sk in c.sketches:sk.isVisible=False
  for p in c.constructionPlanes:p.isLightBulbOn=False
 finally:d.timeline.moveToEnd()
 assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);print(json.dumps({'part_number':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'bodies':[{'name':b.name,'faces':b.faces.count}for b in c.bRepBodies],'saved':False,'seconds':time.monotonic()-tick}))
'''
 r=rpc(s2,'dfma-thigh-shared-split',timeout=1800);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/dfma-thigh-shared-split.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
