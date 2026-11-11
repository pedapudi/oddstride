"""Check the current body candidates using native solid interference and real edits."""
import datetime,json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
keys=['body_center_0','chassis_beam_102','chassis_beam_-102','chassis_crossmember_121','chassis_crossmember_-121']
pairs=[['body_center_0',k] for k in keys[1:]]+[[rail,tie] for rail in keys[1:3] for tie in keys[3:]]+[['chassis_lower_brace',rail] for rail in keys[1:3]]+[['battery_cassette',rail] for rail in keys[1:3]]+[['belly_center_0','battery_cassette'],['electronics_shelf','chassis_lower_brace']]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time
def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;tick=time.monotonic();parts={}
 for key in {k for pair in PAIRS for k in pair}:
  wanted='CANDIDATE_cc_'+key if key in CANDIDATES else key;parts[key]=next(o for o in root.occurrences if o.component.partNumber==wanted)
 def check():
  rows=[]
  for pair in PAIRS:
   entities=core.ObjectCollection.create()
   for key in pair:
    occ=parts[key];assert occ.component.bRepBodies.count==1;entities.add(occ.component.bRepBodies.item(0).createForAssemblyContext(occ))
   inp=d.createInterferenceInput(entities);inp.areCoincidentFacesIncluded=False;result=d.analyzeInterference(inp);assert result is not None;volume=sum(abs(r.interferenceBody.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume)*1000 for r in result);rows.append({'pair':pair,'volume_mm3':volume,'passed':volume<1e-6})
  return rows
 def snapshot():
  result={}
  for key,occ in parts.items():
   body=occ.component.bRepBodies.item(0);bb=body.boundingBox;result[key]={'volume_mm3':body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000,'bounds_mm':[getattr(p,a)*10 for p in [bb.minPoint,bb.maxPoint] for a in ['x','y','z']]}
  return result
 nominal=check();before=snapshot();edits=[]
 for name,value in [('cc_cover_mount_x','62 mm'),('cc_cover_process_hole_compensation','0.1 mm')]:
  p=d.userParameters.itemByName(name);old=p.expression
  try:
   p.expression=value;assert d.computeAll();rows=check();health=[(c.partNumber,f.name,f.errorOrWarningMessage) for c in d.allComponents for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not health,health;edits.append({'parameter':name,'value':value,'checks':rows,'passed':all(r['passed'] for r in rows)})
  finally:p.expression=old;assert d.computeAll()
 after=snapshot();restored=[]
 for key,a in before.items():
  b=after[key];v=abs(a['volume_mm3']-b['volume_mm3']);distance=max(abs(x-y) for x,y in zip(a['bounds_mm'],b['bounds_mm']));restored.append({'part':key,'volume_difference_mm3':v,'bounds_max_difference_mm':distance,'passed':v<max(.001,1e-7*a['volume_mm3']) and distance<.0001})
 print(json.dumps({'passed':all(r['passed'] for r in nominal+restored) and all(r['passed'] for r in edits),'saved':False,'saved_chassis_base_version':doc.dataFile.versionNumber,'checks':nominal,'edits':edits,'restoration':restored,'elapsed_seconds':time.monotonic()-tick,'checker':'Fusion native solid interference with coincident faces excluded; very-high accuracy volume and bounds on restoration','scope':'Changed body, frame, battery and deck interfaces. Two meaningful native edits restored. This is not a whole-robot motion, thread strength or CNC tool-access release.'}))
'''.replace('PAIRS',repr(pairs)).replace('CANDIDATES',repr(keys))
r=rpc(s,'cohesive-body-native-interfaces',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);record['updated_utc']=datetime.datetime.now(datetime.UTC).isoformat();record['source_model_sha256']=json.loads((ROOT/'manifests/current-body-target.json').read_text())['source_model_sha256'];(ROOT/'audits/cohesive-body-native-interfaces.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k not in ['checks','edits','restoration']});print('Failed nominal:',[r for r in record['checks'] if not r['passed']])
