"""Round only the new cup's connector openings; no baseline parameter edits."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
files=['native_documents.py','intent_geometry.py','cohesive_limb_intent.py','paired_roll_intent.py','cohesive_crank_intent.py','cohesive_carrier_intent.py','paired_cup_intent.py','dfma_rear_loaded_cup_intent.py']
script='\n'.join((ROOT/'source'/p).read_text()for p in files)+'''
def run(_context:str):
 import os,json,time,hashlib
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);d.activateRootComponent();c=next(c for c in d.allComponents if c.partNumber=='DFMA_REAR_LOADED_CUP_FL');assert c.features.count==24;baseline={p.name:p.expression for p in d.userParameters if not p.name.startswith('dfma_')};allowance=d.userParameters.itemByName('dfma_roll_cap_screw_diametral_clearance');assert allowance;allowance.expression='0.8 mm';tick=time.monotonic();body=DfmaRearLoadedCupIntent(IntentGeometry(d,c)).refine_connector_windows(c.bRepBodies.item(0));assert c.bRepBodies.count==1 and body.isSolid;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);assert all(d.userParameters.itemByName(k).expression==v for k,v in baseline.items())
 for p in c.constructionPlanes:p.isLightBulbOn=False
 for sk in c.sketches:sk.isVisible=False
 print(json.dumps({'part_number':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'cap_screw_passage_mm':3.8,'baseline_parameter_expressions_unchanged':True,'saved':False,'elapsed_seconds':time.monotonic()-tick,'scope':'Native feature edits only. Export is deliberately a separate transaction.'}))
'''
if __name__=='__main__':
 r=rpc(script,'dfma-rounded-cup-windows',timeout=1200);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/dfma-rounded-cup-windows.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
