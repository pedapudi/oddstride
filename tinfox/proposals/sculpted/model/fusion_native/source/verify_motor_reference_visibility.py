"""Name and verify separately hideable actuator and connector reference bodies."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context: str):
 app=core.Application.get();previous=app.activeDocument;doc=authoring_document(app,'leg');assert not doc.isModified;doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);tick=time.monotonic();rows=[];counts={'motor':0,'plug':0,'cable':0};custom=[c for c in d.allComponents if c.attributes.itemByName('Tinfox','GeometryRole') is None and c.partNumber in ['motor_carrier_1','thigh_inner','thigh_outer']];custom_signatures={c.id:(c.features.count,c.sketches.count,[b.volume for b in c.bRepBodies]) for c in custom}
 for occ in root.allOccurrences:
  name=occ.component.name
  if name.endswith(('_roll_motor','_hip_motor','_knee_motor')):role='motor'
  elif '_port_' in name and name.endswith('_plug'):role='plug'
  elif '_port_' in name and name.endswith('_cable'):role='cable'
  else:continue
  c=occ.component;assert c.bRepBodies.count==1,(name,c.bRepBodies.count);body=c.bRepBodies.item(0);before=body.volume;body.name=name+({'motor':' actuator reference','plug':' XT30 2+2 connector reference','cable':' cable routing envelope'}[role]);c.attributes.add('Tinfox','ReferenceRole',role);c.attributes.add('Tinfox','IndependentVisibility','One named body in its own component; separate from custom structure');visible=occ.isLightBulbOn;occ.isLightBulbOn=False;assert not occ.isLightBulbOn;assert body.volume==before;occ.isLightBulbOn=visible;assert occ.isLightBulbOn==visible;counts[role]+=1;rows.append({'name':name,'role':role,'path':occ.fullPathName,'body':body.name,'body_count':c.bRepBodies.count,'visibility_restored':True,'features':c.features.count})
 assert counts=={'motor':12,'plug':24,'cable':24},counts
 for c in custom:assert custom_signatures[c.id]==(c.features.count,c.sketches.count,[b.volume for b in c.bRepBodies]),c.name
 assert doc.save('Name and verify twelve motor, twenty-four connector and twenty-four cable reference bodies. Each remains in its own independently hideable component; structural native features are unchanged. Frozen migration scope and generated-CAD authority are unchanged.');record={'passed':True,'save_requested':True,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'counts':counts,'references':rows,'custom_histories_unchanged':True,'capacity':capacity,'elapsed_seconds':time.monotonic()-tick,'scope':'Independent component visibility and naming only. Vendor envelopes are unqualified references; no connector or actuator is fused into a structural custom body.'}
 previous.activate();print(json.dumps(record))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'motor-reference-visibility',timeout=240);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/motor-reference-visibility.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k not in ['references','capacity']})
