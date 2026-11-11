"""Author the independently reviewed reinforced closure revision using native features."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py','cohesive_limb_intent.py','paired_roll_intent.py','cohesive_crank_intent.py','cohesive_carrier_intent.py','paired_cup_intent.py','recessed_closure_intent.py'])+'''
def run(_context:str):
 import json,os,tempfile,time
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;tick=time.monotonic();rows=[]
 for key in ['hip_stator_closure_1','motor_carrier_1','motor_carrier_-1']:
  assert not any(c.partNumber=='CANDIDATE_rc_'+key for c in d.allComponents);o=root.occurrences.addNewComponent(core.Matrix3D.create());o.isLightBulbOn=False;c=o.component;c.partNumber='CANDIDATE_rc_'+key;c.name={'hip_stator_closure_1':'Reinforced closure with recessed standard buttons','motor_carrier_1':'Front cup with reinforced closure lands','motor_carrier_-1':'Rear cup with reinforced closure lands'}[key];intent=RecessedClosureIntent(IntentGeometry(d,c))
  if key.startswith('hip_'):body=intent.closure()
  else:
   parent=next(x for x in d.allComponents if x.partNumber=='CANDIDATE_pr_'+key).bRepBodies.item(0);body=intent.revise_cup(parent,1 if key.endswith('_1')else-1)
  assert c.bRepBodies.count==1 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);body.name=c.name;o.isLightBulbOn=True;body.isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','recessed-native-'+key+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>10000;o.isLightBulbOn=False;rows.append({'part':key,'component':c.partNumber,'path':path,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'volume_mm3':body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000})
 print(json.dumps({'saved_version':doc.dataFile.versionNumber,'working_modified':doc.isModified,'candidate_only':True,'exports':rows,'retained_web_mm':d.userParameters.itemByName('rc_retained_closure_web').value*10,'screw_tip_y_mm':d.userParameters.itemByName('rc_screw_tip_y').value*10,'elapsed_seconds':time.monotonic()-tick,'scope':'Native reinforced closure/cup revision; independent export fit/section checks, reference updates and native assembly checks remain required.'}))
'''
r=rpc(s,'recessed-closure-native',timeout=900);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/recessed-closure-native.json').write_text(json.dumps(record,indent=2))
for row in record['exports']:fetch(row['path'],Path(row['path']).name)
print(record)
