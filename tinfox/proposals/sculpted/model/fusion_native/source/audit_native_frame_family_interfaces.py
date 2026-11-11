"""Check native frame, deck and battery interfaces during family edits."""
import json,datetime
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
pairs=[['body_center_0','chassis_beam_102'],['body_center_0','chassis_beam_-102'],['chassis_lower_brace','chassis_beam_102'],['chassis_lower_brace','chassis_beam_-102'],['electronics_shelf','chassis_lower_brace'],['belly_center_0','battery_cassette'],['battery_cassette','chassis_beam_102'],['battery_cassette','chassis_beam_-102'],['battery_cassette','chassis_lower_brace']]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;parts={key:next(o for o in root.allOccurrences if o.component.partNumber==key) for key in {k for pair in PAIRS for k in pair}};tick=time.monotonic();rows=[]
 def check(label):
  results0=[]
  for pair in PAIRS:
   objects=core.ObjectCollection.create()
   for name in pair:
    occ=parts[name];assert occ.component.bRepBodies.count==1;objects.add(occ.component.bRepBodies.item(0).createForAssemblyContext(occ))
   inputs=d.createInterferenceInput(objects);inputs.areCoincidentFacesIncluded=False;results=d.analyzeInterference(inputs);assert results is not None;volume=sum(abs(r.interferenceBody.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume)*1000 for r in results);results0.append({'pair':pair,'volume_mm3':volume,'passed':volume<1e-6})
  return {'condition':label,'checks':results0,'passed':all(r['passed'] for r in results0)}
 rows.append(check('Frozen nominal geometry'))
 for name,expression in [('robot_roll_y','73 mm'),('frame_brace_thickness','4 mm')]:
  p=d.userParameters.itemByName(name);old=p.expression
  try:p.expression=expression;assert d.computeAll();rows.append(check(name+'='+expression))
  finally:p.expression=old;assert d.computeAll()
 rows.append(check('Nominal geometry restored'))
 assert all(j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for j in root.joints);print(json.dumps({'passed':all(r['passed'] for r in rows),'saved':False,'chassis_saved_version':doc.dataFile.versionNumber,'working_document_modified':doc.isModified,'checker':'Fusion Design.analyzeInterference, native root-context bodies, coincident faces excluded','volume_tolerance_mm3':1e-6,'conditions':rows,'elapsed_seconds':time.monotonic()-tick,'scope':'Nine chassis interfaces in nominal, wider-frame, thicker-brace and restored conditions. This does not validate screw engagement, a whole-robot resized variant, CNC access, strength or newer browser geometry.'}))
'''.replace('PAIRS',repr(pairs))
r=rpc(s,'native-frame-family-solid-interfaces',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);record['updated_utc']=datetime.datetime.now(datetime.UTC).isoformat();record['source_model_sha256']='929c06ab624ed80192157e99ce43165c1416db414902cb0a36c19d6d2ad50da6';record['native_inputs']={key:row for key,row in json.loads((ROOT/'manifests/current-native-exports.json').read_text())['parts'].items() if key in {k for pair in pairs for k in pair}};(ROOT/'audits/native-frame-family-solid-interfaces.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'checks':sum(len(r['checks']) for r in record['conditions']),'seconds':record['elapsed_seconds'],'failed':[r for c in record['conditions'] for r in c['checks'] if not r['passed']]})
