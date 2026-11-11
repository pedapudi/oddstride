"""Publish independent named assembly datums from the existing Chassis design."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
rows={'robot_hip_x':('cover_hip_x','185 mm'),'robot_roll_y':('cover_roll_y','68 mm'),'robot_body_wall':('cover_wall','2.8 mm'),'robot_sensor_seat_z':('saddle_sensor_seat_z','80 mm'),'robot_fastener_diametral_allowance':('saddle_fastener_diametral_clearance','.4 mm')}
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');assert doc==app.activeDocument and not doc.isModified;d=fusion.Design.cast(app.activeProduct);capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);tick=time.monotonic();before={c.partNumber:[b.volume for b in c.bRepBodies] for c in d.allComponents if c.bRepBodies.count};created=[]
 for name,(dependent,expression) in ROWS.items():
  assert d.userParameters.itemByName(name) is None;p=d.userParameters.add(name,core.ValueInput.createByString(expression),'mm','Shared robot datum exported to subsystem designs. Vendor dimensions remain independent; complete robot resizing and strength are not qualified.');p.isFavorite=True;q=d.userParameters.itemByName(dependent);value=q.value;old=q.expression;q.expression=name;assert abs(q.value-value)<1e-9;created.append({'source':name,'dependent':dependent,'old_expression':old,'expression':expression})
 width=d.userParameters.add('robot_body_half_width',core.ValueInput.createByString('cover_half_width'),'mm','Shared envelope width derived from the body placement datum.');width.isFavorite=True;assert d.computeAll()
 for c in d.allComponents:
  if c.partNumber in before:assert max(abs(a-b.volume) for a,b in zip(before[c.partNumber],c.bRepBodies))<1e-6,c.name
  assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),c.name
 assert doc.save('Publish shared robot placement, body wall, sensor seat and fastener allowance parameters for native subsystem links. Geometry unchanged; cross-document edit/restore checks remain pending.');print(json.dumps({'saved':True,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'parameters':created,'favorites':[p.name for p in d.userParameters if p.isFavorite],'capacity':capacity,'geometry_unchanged':True,'elapsed_seconds':time.monotonic()-tick}))
'''.replace('KNOWN',repr(known_files())).replace('ROWS',repr(rows))
r=rpc(s,'shared-robot-datum-publication',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/shared-robot-datum-publication.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k!='capacity'})
