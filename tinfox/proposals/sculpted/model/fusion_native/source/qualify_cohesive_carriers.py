"""Verify native carrier family edits and both handed bearing interfaces."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;rows=[];paths=[]
 for front in [1,-1]:
  key='CANDIDATE_motor_carrier_'+str(front);source=next(o.component for o in root.occurrences if o.component.partNumber==key);assert not any(o.component.partNumber==key+'_right' for o in root.occurrences);occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.partNumber=key+'_right';c.name=('Front' if front>0 else 'Rear')+' right motor carrier';objects=core.ObjectCollection.create();objects.add(source.bRepBodies.item(0));f=c.features.copyPasteBodies.add(objects);f.name='Linked native motor carrier';original=f.bodies.item(0);objects=core.ObjectCollection.create();objects.add(original);inp=c.features.mirrorFeatures.createInput(objects,c.xZConstructionPlane);inp.isCombine=False;c.features.mirrorFeatures.add(inp).name='Right hip reflection';c.features.removeFeatures.add(original).name='Keep handed carrier';assert c.bRepBodies.count==1;path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-motor-carrier-'+str(front)+'-right.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));paths.append(path)
 master=next(o.component for o in root.occurrences if o.component.partNumber=='CANDIDATE_carrier_master');master.features.removeFeatures.add(master.bRepBodies.item(0)).name='Construction stock consumed by native carrier variants';assert master.bRepBodies.count==0
 parts=[o.component for o in root.occurrences if o.component.partNumber.startswith('CANDIDATE_motor_carrier_')]
 def signatures():
  result={}
  for c in parts:
   assert c.bRepBodies.count==1;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);b=c.bRepBodies.item(0);result[c.partNumber]={'volume':b.volume,'faces':b.faces.count,'edges':b.edges.count}
  return result
 baseline=signatures();edits=[]
 for key,value in [('lc_carrier_shell_outer','43.8 mm'),('lc_carrier_journal_radius','25.1 mm'),('lc_carrier_port_tangent_width','19 mm')]:
  p=d.userParameters.itemByName(key);old=p.expression
  try:
   p.expression=value;assert d.computeAll(),('recompute',key,value);changed=signatures();assert all(abs(changed[k]['volume']-baseline[k]['volume'])>1e-6 for k in baseline),('no change',key,changed,baseline)
  finally:p.expression=old;assert d.computeAll()
  restored=signatures();assert all(abs(restored[k]['volume']-baseline[k]['volume'])<1e-7 for k in baseline);edits.append({'parameter':key,'changed_expression':value,'restored_expression':old,'changed':changed,'restored':restored})
 for c in parts:rows.append({'part':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'faces':c.bRepBodies.item(0).faces.count,'edges':c.bRepBodies.item(0).edges.count})
 print(json.dumps({'passed':True,'parts':rows,'edits':edits,'construction_master_bodies':master.bRepBodies.count,'master_features':master.features.count,'paths':paths,'saved':False}))
'''
r=rpc(s,'cohesive-carrier-family',timeout=360);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-carrier-family.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k!='edits'})
for path in record['paths']:fetch(path,Path(path).name)
