"""Save the four changed DFMA parts without rerunning baseline migration gates."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);parts=[]
 for pn in ['DFMA_SHARED_ROLL_CAP_FL','DFMA_ROLL_HOUSING_FL','DFMA_ROLL_BACKPLATE_FL','DFMA_REAR_LOADED_CUP_FL']:
  c=next(c for c in d.allComponents if c.partNumber==pn);assert c.bRepBodies.count==1 and c.bRepBodies.item(0).isSolid;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);parts.append({'part_number':pn,'features':c.features.count,'sketches':c.sketches.count})
 before=doc.dataFile.versionNumber;assert before==31;assert doc.save('DFMA bearing support and integral rear-loaded cup. Shared three-millimeter race cap uses nine common M3x35 screws; housing and rear plate omit separate retainer fasteners. Rounded connector openings preserve the original axial extent. Isolated proposal, not a loaded or manufacturing release; Master63/Leg30 baseline preserved.');print(json.dumps({'previous_version':before,'version_at_return':doc.dataFile.versionNumber,'complete_at_return':doc.dataFile.isComplete,'modified_at_return':doc.isModified,'parts':parts,'capacity':capacity,'scope':'Four changed native parts only; no baseline source or Master reference update.'}))
'''.replace('KNOWN',repr(known_files()))
if __name__=='__main__':
 r=rpc(s,'dfma-bearing-stage-checkpoint',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/dfma-bearing-stage-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k!='capacity'})
