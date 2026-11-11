"""Connect the current low sensor assembly to the existing Head hip datum."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
bindings={'saddle_x':'body_hip_x-64 mm','hood_sensor_x':'saddle_x','saddle_face_join_x':'head_face_reference_x+.6 mm'}
for i,x in enumerate([76,92,121,150,185,216,240,248],1):bindings[f'hood_station_{i}_x']='head_face_reference_x'+('+' if x>=245.4 else '-')+str(round(abs(x-245.4),3))+' mm'
s='''import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);tick=time.monotonic();rows=[]
 for name,expression in BINDINGS.items():
  p=d.userParameters.itemByName(name);old=p.expression;value=p.value;p.expression=expression;assert abs(p.value-value)<1e-8;rows.append({'parameter':name,'before':old,'expression':expression})
 assert d.computeAll();parts={}
 for c in d.allComponents:
  if c.partNumber.startswith('CANDIDATE_current_'):
   assert c.bRepBodies.count==1 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);parts[c.partNumber]={'features':c.features.count,'sketches':c.sketches.count}
 print(json.dumps({'passed':True,'saved':False,'bindings':rows,'parts':parts,'elapsed_seconds':time.monotonic()-tick,'scope':'Shared longitudinal hip/frame datum across native cradle, face and hood. Whole robot external-document synchronization remains a separate assembly gate.'}))
'''.replace('BINDINGS',repr(bindings))
r=rpc(s,'current-head-family-bindings',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-head-family-bindings.json').write_text(json.dumps(record,indent=2));print(record)
