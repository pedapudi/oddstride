"""Link handed thigh shells and exclude the construction master from final mass."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;paths=[];rows=[]
 for side in ['inner','outer']:
  left=next(o.component for o in root.occurrences if o.component.partNumber=='CANDIDATE_cohesive_thigh_'+side);key=left.partNumber+'_right';assert not any(o.component.partNumber==key for o in root.occurrences);occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.partNumber=key;c.name='Right thigh '+side+' shell';objects=core.ObjectCollection.create();objects.add(left.bRepBodies.item(0));copy=c.features.copyPasteBodies.add(objects);copy.name='Linked left-hand manufacturing shell';assert copy.isParametric;original=copy.bodies.item(0);objects=core.ObjectCollection.create();objects.add(original);inp=c.features.mirrorFeatures.createInput(objects,c.xZConstructionPlane);inp.isCombine=False;f=c.features.mirrorFeatures.add(inp);f.name='Right-hand reflection';c.features.removeFeatures.add(original).name='Keep right-hand manufacturing shell';assert c.bRepBodies.count==1
 master=next(o.component for o in root.occurrences if o.component.partNumber=='CANDIDATE_cohesive_thigh_master');assert master.bRepBodies.count==1;master.features.removeFeatures.add(master.bRepBodies.item(0)).name='Exclude construction solid from assembled mass';assert master.bRepBodies.count==0;master.attributes.add('Tinfox','Role','Construction master: native source before final Remove feature; not a manufacturing part')
 targets=[o for o in root.occurrences if o.component.partNumber.startswith('CANDIDATE_cohesive_thigh_') and o.component!=master];baseline={o.component.partNumber:o.component.bRepBodies.item(0).boundingBox.minPoint.z*10 for o in targets};p=d.userParameters.itemByName('lc_thigh_length');old=p.expression
 try:
  p.expression='171 mm';assert d.computeAll();response={o.component.partNumber:o.component.bRepBodies.item(0).boundingBox.minPoint.z*10 for o in targets};assert all(abs(v-baseline[key]+1)<.002 for key,v in response.items()),response
 finally:p.expression=old;assert d.computeAll()
 for occ in targets:
  c=occ.component;assert c.bRepBodies.count==1 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);assert abs(c.bRepBodies.item(0).boundingBox.minPoint.z*10-baseline[c.partNumber])<.002;occ.isLightBulbOn=True;c.bRepBodies.item(0).isLightBulbOn=True;label=c.partNumber.replace('CANDIDATE_cohesive_thigh_','cohesive-thigh-').replace('_','-')+'-final';path=os.path.join(tempfile.gettempdir(),'tinfox-native',label+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));paths.append(path);rows.append({'part':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'faces':c.bRepBodies.item(0).faces.count,'edges':c.bRepBodies.item(0).edges.count,'file':label+'.step'})
 assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in master.features)
 print(json.dumps({'parts':rows,'construction_master_final_bodies':0,'construction_master_features':master.features.count,'one_mm_length_response':response,'edit_restored':True,'paths':paths,'saved':False}))
'''
r=rpc(s,'cohesive-thigh-handed-final-geometry',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-thigh-handed-final-geometry.json').write_text(json.dumps(record,indent=2));print(record)
for path in record['paths']:fetch(path,Path(path).name)
