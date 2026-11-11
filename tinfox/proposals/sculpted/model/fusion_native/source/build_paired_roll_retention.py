"""Build native race spacers and removable retention around the paired bearings."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py','paired_roll_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile,time
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert d.activateRootComponent();tick=time.monotonic();made=[]
 for key,name,method,arg in [('roll_inner_spacer_1','Inner bearing race spacer','spacer',False),('roll_outer_spacer_1','Outer bearing race spacer','spacer',True),('roll_inner_backplate_1','Motor-side inner race support','inner_backplate',None),('roll_outer_retainer_1','Removable passive outer-race retainer','outer_retainer',None)]:
  assert not any(c.partNumber=='CANDIDATE_pr_'+key for c in d.allComponents);o=root.occurrences.addNewComponent(core.Matrix3D.create());c=o.component;c.name=name;c.partNumber='CANDIDATE_pr_'+key;builder=PairedRollIntent(IntentGeometry(d,c));body=getattr(builder,method)()if arg is None else getattr(builder,method)(arg);assert c.bRepBodies.count==1;body.name=name;made.append((key,o));o.isLightBulbOn=False
 for key,o in list(made):
  source=o.component
  for rear,right in [(True,False),(False,True),(True,True)]:
   newkey=key[:-1]+('-1'if rear else'1')+('_right'if right else'');assert not any(c.partNumber=='CANDIDATE_pr_'+newkey for c in d.allComponents);no=root.occurrences.addNewComponent(core.Matrix3D.create());c=no.component;c.name=('Rear 'if rear else'Front ')+('right 'if right else'left ')+source.name.lower();c.partNumber='CANDIDATE_pr_'+newkey;objs=core.ObjectCollection.create();objs.add(source.bRepBodies.item(0));copy=c.features.copyPasteBodies.add(objs);copy.name='Shared native bearing stack';body=copy.bodies.item(0)
   for plane,label in ([(c.yZConstructionPlane,'Rear reflection')]if rear else[])+([(c.xZConstructionPlane,'Right-hand reflection')]if right else[]):
    objs=core.ObjectCollection.create();objs.add(body);inp=c.features.mirrorFeatures.createInput(objs,plane);inp.isCombine=False;f=c.features.mirrorFeatures.add(inp);f.name=label;newbody=next(b for b in c.bRepBodies if b!=body);c.features.removeFeatures.add(body).name='Keep the reflected manufacturing part';body=newbody
   assert c.bRepBodies.count==1;made.append((newkey,no));no.isLightBulbOn=False
 rows=[];paths=[]
 for key,o in made:
  c=o.component;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);o.isLightBulbOn=True;c.bRepBodies.item(0).isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','paired-native-'+key+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));o.isLightBulbOn=False;assert os.path.getsize(path)>5000;paths.append(path);b=c.bRepBodies.item(0);rows.append({'part':key,'features':c.features.count,'sketches':c.sketches.count,'faces':b.faces.count,'edges':b.edges.count,'volume_mm3':b.volume*1000})
 print(json.dumps({'saved':False,'parts':rows,'paths':paths,'elapsed_seconds':time.monotonic()-tick,'scope':'Paired-6810 race spacers and retention candidates. Source comparisons, meaningful edits, bearing stack fits and final bench assembly remain pending.'}))
'''
r=rpc(s,'paired-roll-retention-native',timeout=600);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/paired-roll-retention-native.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
for path in record['paths']:fetch(path,Path(path).name)
