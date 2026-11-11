"""Build shared native carrier stock and handed functional interfaces."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text() for p in ['intent_geometry.py','cohesive_limb_intent.py','cohesive_crank_intent.py','cohesive_carrier_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert not any(o.component.partNumber=='CANDIDATE_carrier_master' for o in root.occurrences);occ=root.occurrences.addNewComponent(core.Matrix3D.create());master=occ.component;master.partNumber='CANDIDATE_carrier_master';master.name='Common perpendicular carrier stock';body=CohesiveCarrierIntent(IntentGeometry(d,master)).stock();rows=[];paths=[]
 for front in [1,-1]:
  occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.partNumber='CANDIDATE_motor_carrier_'+str(front);c.name=('Front' if front>0 else 'Rear')+' perpendicular motor carrier';objects=core.ObjectCollection.create();objects.add(body);copy=c.features.copyPasteBodies.add(objects);copy.name='Shared carrier stock';b=copy.bodies.item(0)
  if front<0:
   originals=list(c.bRepBodies);objects=core.ObjectCollection.create();objects.add(b);inp=c.features.mirrorFeatures.createInput(objects,c.yZConstructionPlane);inp.isCombine=False;c.features.mirrorFeatures.add(inp).name='Rear-facing roll journal';c.features.removeFeatures.add(b).name='Keep rear-facing carrier';b=c.bRepBodies.item(0)
  b=CohesiveCarrierIntent(IntentGeometry(d,c)).interfaces(b,front);assert c.bRepBodies.count==1;health=[{'name':f.name,'state':int(f.healthState),'message':f.errorOrWarningMessage} for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-motor-carrier-'+str(front)+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));paths.append(path);rows.append({'part':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'faces':b.faces.count,'edges':b.edges.count,'unhealthy':health})
 print(json.dumps({'master_features':master.features.count,'master_sketches':master.sketches.count,'master_unhealthy':[{'name':f.name,'state':int(f.healthState),'message':f.errorOrWarningMessage} for f in master.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState],'parts':rows,'paths':paths,'saved':False}))
'''
r=rpc(s,'cohesive-carrier-build',timeout=360);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-carrier-build.json').write_text(json.dumps(record,indent=2));print(record)
for path in record['paths']:fetch(path,Path(path).name)
