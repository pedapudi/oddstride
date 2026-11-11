"""Derive two native structural halves and their linked handed counterparts."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py','native_nonuniform_spline.py','cohesive_limb_intent.py','cohesive_thigh_intent.py','slim_thigh_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile,time
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;master=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_sl_thigh_master');assert master.bRepBodies.count==2;source=next(b for b in master.bRepBodies if b.name=='Closed thigh shared finished master');mask=next(b for b in master.bRepBodies if b.name=='Construction shared thigh split');tick=time.monotonic();made=[]
 for outer in [False,True]:
  key='thigh_'+('outer'if outer else'inner');assert not any(c.partNumber=='CANDIDATE_sl_'+key for c in d.allComponents);o=root.occurrences.addNewComponent(core.Matrix3D.create());c=o.component;c.name=('Outer'if outer else'Inner')+' closed structural thigh';c.partNumber='CANDIDATE_sl_'+key;g=IntentGeometry(d,c);n=SlimThighIntent(g);objects=core.ObjectCollection.create();objects.add(source);objects.add(mask);copy=c.features.copyPasteBodies.add(objects);copy.name='Linked shared limb and manufacturing split';assert copy.isParametric and copy.bodies.count==2;body=min(copy.bodies,key=lambda b:abs(b.volume-source.volume));tool=next(b for b in copy.bodies if b!=body);body=g.combine(body,[tool],fusion.FeatureOperations.CutFeatureOperation if outer else fusion.FeatureOperations.IntersectFeatureOperation,'Keep the '+('outer'if outer else'inner')+' structural half');body=n.bearing_stop(body,outer);body=n.shell_hardware(body,outer);assert c.bRepBodies.count==1;body.name=c.name;o.isLightBulbOn=False;made.append((key,o))
 for key,o in list(made):
  no=root.occurrences.addNewComponent(core.Matrix3D.create());c=no.component;c.name='Right '+o.component.name.lower();c.partNumber='CANDIDATE_sl_'+key+'_right';objects=core.ObjectCollection.create();objects.add(o.component.bRepBodies.item(0));copy=c.features.copyPasteBodies.add(objects);copy.name='Linked structural shell family';body=copy.bodies.item(0);objects=core.ObjectCollection.create();objects.add(body);inp=c.features.mirrorFeatures.createInput(objects,c.xZConstructionPlane);inp.isCombine=False;f=c.features.mirrorFeatures.add(inp);f.name='Right-hand structural shell';c.features.removeFeatures.add(body).name='Keep the right-hand manufacturing part';assert c.bRepBodies.count==1;no.isLightBulbOn=False;made.append((key+'_right',no))
 rows=[];paths=[]
 for key,o in made:
  c=o.component;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);o.isLightBulbOn=True;c.bRepBodies.item(0).isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','slim-native-'+key+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>5000;paths.append(path);o.isLightBulbOn=False;b=c.bRepBodies.item(0);rows.append({'part':key,'features':c.features.count,'sketches':c.sketches.count,'faces':b.faces.count,'edges':b.edges.count,'volume_mm3':b.volume*1000})
 print(json.dumps({'saved':False,'parts':rows,'paths':paths,'elapsed_seconds':time.monotonic()-tick,'scope':'Four native latest thigh halves, including M4 washer floors and M5 knee retention. Shape, family edit and service checks remain before assembly migration.'}))
'''
r=rpc(s,'slim-thigh-native-halves',timeout=900);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/slim-thigh-native-halves.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
for path in record['paths']:fetch(path,Path(path).name)
