"""Add the approved open screw-head channels to the native crank family."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py','cohesive_limb_intent.py','cohesive_crank_intent.py'])+'''
def run(_context:str):
 import json,os,tempfile,time
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;assert not any(c.partNumber=='CANDIDATE_mc_input_crank'for c in d.allComponents);o=root.occurrences.addNewComponent(core.Matrix3D.create());c=o.component;c.name='Input crank - open mounting screw access';c.partNumber='CANDIDATE_mc_input_crank';g=IntentGeometry(d,c);n=CohesiveCrankIntent(g);body=n.blank();body=n.interfaces(body,open_heads=True);assert c.bRepBodies.count==1;c.bRepBodies.item(0).name='Input crank with open driver approach';o.isLightBulbOn=False;made=[('input_crank',o)]
 no=root.occurrences.addNewComponent(core.Matrix3D.create());right=no.component;right.name='Right input crank - open mounting screw access';right.partNumber='CANDIDATE_mc_input_crank_right';objects=core.ObjectCollection.create();objects.add(c.bRepBodies.item(0));f=right.features.copyPasteBodies.add(objects);f.name='Shared corrected native crank';body=f.bodies.item(0);objects=core.ObjectCollection.create();objects.add(body);inp=right.features.mirrorFeatures.createInput(objects,right.xZConstructionPlane);inp.isCombine=False;right.features.mirrorFeatures.add(inp).name='Right-hand reflection';right.features.removeFeatures.add(body).name='Keep the right-hand manufacturing part';no.isLightBulbOn=False;made.append(('input_crank_right',no));rows=[];paths=[]
 for key,o in made:
  c=o.component;assert c.bRepBodies.count==1,(key,c.bRepBodies.count);issues=[(f.name,int(f.healthState),f.errorOrWarningMessage)for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,(key,issues);o.isLightBulbOn=True;c.bRepBodies.item(0).isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','motor-complex-native-'+key+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));o.isLightBulbOn=False;paths.append(path);rows.append({'part':key,'features':c.features.count,'sketches':c.sketches.count,'faces':c.bRepBodies.item(0).faces.count})
 print(json.dumps({'saved':False,'parts':rows,'paths':paths,'scope':'Explicit open counterbore source revision. Native comparison, access and assembled motor-complex audits remain separate.'}))
'''
r=rpc(s,'motor-complex-crank-access-native',timeout=300);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/motor-complex-crank-access-native.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
for path in record['paths']:fetch(path,Path(path).name)
