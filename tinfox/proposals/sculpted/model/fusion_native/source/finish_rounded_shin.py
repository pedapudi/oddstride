"""Finish the shared rounded shin with serviceable bearing and washer seats."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
fit=json.loads((ROOT/'snapshots/cohesive-limb/intent/shin-cubic-design-skeleton.json').read_text())
weights=json.loads((ROOT/'snapshots/latest-leg/rounded-shin-guide-interpolation.json').read_text())['inner']['span_station_coefficients']
s='\n'.join((ROOT/'source'/n).read_text()for n in ['native_documents.py','intent_geometry.py','cohesive_limb_intent.py','rounded_shin_intent.py'])+'''
def run(_context: str):
 import json,time,tempfile,os
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert d.activateRootComponent();c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_round_shin_master');assert c.features.count==1 and c.features.loftFeatures.item(0).centerLineOrRails.count==12;g=IntentGeometry(d,c);n=RoundedShinIntent(g);tick=time.monotonic();body=n.round_housing(c.bRepBodies.item(0),FIT,WEIGHTS);body=n.bearing_seats(body);body=n.rod_clearances(body);body=n.open_clamp_hardware(body);assert c.bRepBodies.count==1;body.name='Shared rounded shin with open bearing and clamp interfaces';issues=[(f.name,f.errorOrWarningMessage)for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues
 rows=[];paths=[]
 def export(comp,key):
  body=comp.bRepBodies.item(0);visible=[(o,o.isLightBulbOn)for o in root.occurrences if o.component==comp]
  for o,_ in visible:o.isLightBulbOn=True
  body.isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','rounded-native-'+key+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,comp));assert os.path.getsize(path)>5000
  for o,light in visible:o.isLightBulbOn=light
  paths.append(path);rows.append({'key':key,'features':comp.features.count,'sketches':comp.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'volume_mm3':body.volume*1000,'bounds_mm':[v*10 for v in body.boundingBox.minPoint.asArray()+body.boundingBox.maxPoint.asArray()]})
 export(c,'shin_master')
 for outer in [False,True]:
  key='shin_'+('outer'if outer else'inner');assert not any(x.partNumber=='CANDIDATE_round_'+key for x in d.allComponents);occ=root.occurrences.addNewComponent(core.Matrix3D.create());half=occ.component;half.name='Rounded '+('outer'if outer else'inner')+' shin shell';half.partNumber='CANDIDATE_round_'+key;hg=IntentGeometry(d,half);objs=core.ObjectCollection.create();objs.add(body);copy=half.features.copyPasteBodies.add(objs);copy.name='Shared native rounded shin';assert copy.isParametric;hb=copy.bodies.item(0);plane=hg.plane(half.xZConstructionPlane,'lc_shin_split_y','Structural clamshell split');inp=half.features.splitBodyFeatures.createInput(hb,plane,True);half.features.splitBodyFeatures.add(inp).name='Separate the two manufacturing halves';assert half.bRepBodies.count==2;remove=next(b for b in half.bRepBodies if (b.boundingBox.maxPoint.y<hg.mm('lc_shin_split_y')/10+1e-6)==outer);half.features.removeFeatures.add(remove).name='Keep this manufacturing half';assert half.bRepBodies.count==1;plane.isLightBulbOn=False;occ.isLightBulbOn=False;export(half,key)
  ro=root.occurrences.addNewComponent(core.Matrix3D.create());rc=ro.component;rc.name='Right '+half.name.lower();rc.partNumber='CANDIDATE_round_'+key+'_right';objs=core.ObjectCollection.create();objs.add(half.bRepBodies.item(0));copy=rc.features.copyPasteBodies.add(objs);copy.name='Shared handed shin';original=copy.bodies.item(0);objs=core.ObjectCollection.create();objs.add(original);inp=rc.features.mirrorFeatures.createInput(objs,rc.xZConstructionPlane);inp.isCombine=False;rc.features.mirrorFeatures.add(inp).name='Opposite limb reflection';rc.features.removeFeatures.add(original).name='Keep right-hand manufacturing shell';assert rc.bRepBodies.count==1;ro.isLightBulbOn=False;export(rc,key+'_right')
 assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);print(json.dumps({'saved':False,'paths':paths,'parts':rows,'elapsed_seconds':time.monotonic()-tick,'scope':'Current washer-seat shin candidate; shape, parameter and assembly gates pending.'}))
'''.replace('FIT',repr(fit)).replace('WEIGHTS',repr(weights))
r=rpc(s,'rounded-shin-finished-native',timeout=1500);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/rounded-shin-finished-native.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
for path in record['paths']:fetch(path,Path(path).name)
