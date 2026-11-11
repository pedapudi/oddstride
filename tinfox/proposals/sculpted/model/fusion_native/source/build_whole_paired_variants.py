"""Derive handed native support families while preserving vendor clocking and the released bench."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
plan=[]
for key in ['roll_cartridge','roll_stator_backplate']:
 for rear,right in [(True,False),(False,True),(True,True)]:plan.append({'key':key+('_-1'if rear else'_1')+('_right'if right else''),'parent':'CANDIDATE_pr_'+key+'_1','rear':rear,'right':right,'rear_method':'mirror'})
for rear,right in [(True,False),(False,True),(True,True)]:plan.append({'key':'hip_stator_closure'+('_-1'if rear else'_1')+('_right'if right else''),'parent':'CANDIDATE_rc_hip_stator_closure_1','rear':rear,'right':right,'rear_method':'translate'})
for front in [1,-1]:plan.append({'key':'motor_carrier_'+str(front)+'_right','parent':'CANDIDATE_rc_motor_carrier_'+str(front),'rear':False,'right':True,'rear_method':'none'})
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py'])+'''
def run(_context:str):
 import json,os,tempfile,hashlib,time
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();assert doc.dataFile.versionNumber>=24;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert d.activateRootComponent();tick=time.monotonic();rows=[];paths=[];bench=next(o for o in root.occurrences if o.component.partNumber=='BENCH_MOTOR_COMPLEX')
 def fingerprint():
  return {o.attributes.itemByName('Tinfox','BenchPart').value:{'bounds':[v*10 for v in [*o.component.bRepBodies.item(0).boundingBox.minPoint.asArray(),*o.component.bRepBodies.item(0).boundingBox.maxPoint.asArray()]],'faces':o.component.bRepBodies.item(0).faces.count,'matrix':list(o.createForAssemblyContext(bench).transform2.asArray())}for o in bench.component.occurrences if o.attributes.itemByName('Tinfox','BenchPart')}
 before=fingerprint()
 for spec in PLAN:
  key=spec['key'];number='CANDIDATE_wf_'+key;assert not any(c.partNumber==number for c in d.allComponents),number;parent=next(c for c in d.allComponents if c.partNumber==spec['parent']);o=root.occurrences.addNewComponent(core.Matrix3D.create());o.isLightBulbOn=False;c=o.component;c.partNumber=number;c.name=('Rear 'if '_-1'in key else'Front ')+('right 'if spec['right']else'left ')+key.split('_1')[0].split('_-1')[0].replace('_',' ');g=IntentGeometry(d,c);items=core.ObjectCollection.create();items.add(parent.bRepBodies.item(0));copy=c.features.copyPasteBodies.add(items);copy.name='Linked qualified native master';body=copy.bodies.item(0)
  if spec['rear'] and spec['rear_method']=='translate':
   items=core.ObjectCollection.create();items.add(body);mi=c.features.moveFeatures.createInput2(items);assert mi.defineAsTranslateXYZ(g.value('-2*pr_pitch_x_offset'),g.value('0 mm'),g.value('0 mm'),True);f=c.features.moveFeatures.add(mi);f.name='Rear motor center; preserve nine-hole clock and port orientation';body=c.bRepBodies.item(0)
  planes=([(c.yZConstructionPlane,'Rear axial reflection')]if spec['rear'] and spec['rear_method']=='mirror'else[])+([(c.xZConstructionPlane,'Right-hand lateral reflection')]if spec['right']else[])
  for plane,title in planes:
   items=core.ObjectCollection.create();items.add(body);mi=c.features.mirrorFeatures.createInput(items,plane);mi.isCombine=False;f=c.features.mirrorFeatures.add(mi);f.name=title;new=next(b for b in c.bRepBodies if b!=body);c.features.removeFeatures.add(body).name='Retain handed manufacturing solid';body=new
  assert c.bRepBodies.count==1 and body.isSolid;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);body.name=c.name;body.appearance=parent.bRepBodies.item(0).appearance;body.material=parent.bRepBodies.item(0).material;o.isLightBulbOn=True;body.isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','whole-family-'+key+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>5000;o.isLightBulbOn=False;bb=body.boundingBox;rows.append({**spec,'part_number':number,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'bounds_mm':[v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]],'path':path,'sha256':hashlib.sha256(open(path,'rb').read()).hexdigest()});paths.append(path)
 assert fingerprint()==before;assert [o for o in root.occurrences if o.isLightBulbOn]==[bench];print(json.dumps({'saved':False,'parts':rows,'paths':paths,'canonical_bench_unchanged':True,'elapsed_seconds':time.monotonic()-tick,'scope':'Native linked family candidates for full-robot integration; not installed or whole-robot canonical.'}))
'''.replace('PLAN',repr(plan))
r=rpc(s,'whole-paired-native-variants',timeout=900);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/whole-paired-native-variants.json').write_text(json.dumps(record,indent=2));print({'parts':len(record['parts']),'seconds':record['elapsed_seconds']},flush=True)
for x in record['parts']:fetch(x['path'],Path(x['path']).name)
