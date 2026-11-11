"""Author the new motor cavity and integral mounting face before later assembly history."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
files=['native_documents.py','intent_geometry.py','native_nonuniform_spline.py','cohesive_limb_intent.py','cohesive_thigh_intent.py','slim_thigh_intent.py','dfma_thigh_intent.py']
s='\n'.join((ROOT/'source'/p).read_text()for p in files)+'''
def run(_context:str):
 import json,time,os
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);d.activateRootComponent();c=next(c for c in d.allComponents if c.partNumber=='DFMA_THIGH_SEED_FL');assert c.features.count==2 and c.bRepBodies.count==2;cup=next(c for c in d.allComponents if c.partNumber=='DFMA_REAR_LOADED_CUP_FL');cup_cuts=[{'name':f.name,'is_cut':f.operation==fusion.FeatureOperations.CutFeatureOperation,'timeline_index':f.timelineObject.index}for f in list(cup.features)[-2:]];assert all(row['is_cut']for row in cup_cuts);baseline={p.name:p.expression for p in d.userParameters if not p.name.startswith('dfma_')};tick=time.monotonic();last=c.features.item(c.features.count-1);assert last.timelineObject.rollTo(False)
 try:
  body=next(b for b in c.bRepBodies if b.name=='Shared hollow thigh envelope');envelope=next(b for b in c.bRepBodies if b.name=='Shared complete exterior clipping envelope');body,envelope=DfmaThighIntent(IntentGeometry(d,c)).upper_master_core(body,envelope);assert c.bRepBodies.count==2 and body.isSolid and envelope.isSolid
  for sk in c.sketches:sk.isVisible=False
  for p in c.constructionPlanes:p.isLightBulbOn=False
 finally:d.timeline.moveToEnd()
 assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);assert all(d.userParameters.itemByName(k).expression==v for k,v in baseline.items());print(json.dumps({'part_number':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'faces':[b.faces.count for b in c.bRepBodies],'new_feature_indices':[f.timelineObject.index for f in c.features],'cup_window_native_features':cup_cuts,'baseline_parameters_unchanged':True,'saved':False,'seconds':time.monotonic()-tick,'scope':'Hidden native proximal structural master. Clamps, secondary columns, two physical halves and focused assembly checks remain.'}))
'''
if __name__=='__main__':
 r=rpc(s,'dfma-thigh-motor-core',timeout=1800);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/dfma-thigh-motor-core.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
