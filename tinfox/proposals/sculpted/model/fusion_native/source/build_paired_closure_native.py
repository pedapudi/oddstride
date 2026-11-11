"""Author the frozen detached bearing cartridge and removable stator plate."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py','cohesive_limb_intent.py','paired_roll_intent.py','cohesive_crank_intent.py','cohesive_carrier_intent.py','paired_cup_intent.py'])+'''
def run(_context:str):
 import json,os,tempfile,time
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;tick=time.monotonic();rows=[];paths=[]
 for key,method,title in [('hip_stator_closure_1','closure','Removable hip motor stator closure')]:
  assert not any(c.partNumber=='CANDIDATE_pr_'+key for c in d.allComponents);o=root.occurrences.addNewComponent(core.Matrix3D.create());c=o.component;c.name=title;c.partNumber='CANDIDATE_pr_'+key;builder=PairedCupIntent(IntentGeometry(d,c));body=getattr(builder,method)();assert c.bRepBodies.count==1,(key,c.bRepBodies.count);issues=[(f.name,int(f.healthState),f.errorOrWarningMessage)for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,(key,issues);body.name=title;c.attributes.add('Tinfox','ManufacturingStatus','Detached motor-fit prototype; polymer strength and chassis integration are not qualified.');path=os.path.join(tempfile.gettempdir(),'tinfox-native','paired-native-'+key+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>5000;paths.append(path);rows.append({'part':key,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count});o.isLightBulbOn=False
 print(json.dumps({'saved':False,'parts':rows,'paths':paths,'elapsed_seconds':time.monotonic()-tick,'scope':'Frozen b968 detached bearing housing native histories. Shape, fit, service, parameter and complete motor-complex checks remain separate.'}))
'''
r=rpc(s,'paired-closure-native',timeout=600);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/paired-closure-native.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
for path in record['paths']:fetch(path,Path(path).name)
