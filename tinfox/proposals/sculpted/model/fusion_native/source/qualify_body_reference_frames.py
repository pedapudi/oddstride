"""Exercise native fixed-body reference placement without resizing purchased parts."""
import json
from pathlib import Path
from run_native import rpc
from body_reference_plan import plan
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;tick=time.monotonic();instances={}
 for name in PLAN['assignments']:
  matches=[o for o in root.allOccurrences if o.attributes.itemByName('Tinfox','SourceInstance') and o.attributes.itemByName('Tinfox','SourceInstance').value==name];assert len(matches)==1,(name,len(matches));instances[name]=matches[0]
 def state():
  rows={}
  for name,occ in instances.items():
   assert occ.component.bRepBodies.count>=1;native=list(occ.component.bRepBodies);bodies=[b.createForAssemblyContext(occ) for b in native];bounds=[min(getattr(b.boundingBox.minPoint,axis) for b in bodies)*10 for axis in ['x','y','z']]+[max(getattr(b.boundingBox.maxPoint,axis) for b in bodies)*10 for axis in ['x','y','z']];rows[name]={'bounds_mm':bounds,'volume_mm3':sum(b.volume for b in native)*1000,'features':occ.component.features.count,'sketches':occ.component.sketches.count}
  assert all(j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for j in root.joints);return rows
 baseline=state();cases=[]
 for name,expression in [('robot_hip_x','190 mm'),('robot_roll_y','73 mm'),('frame_brace_thickness','4 mm'),('deck_thickness','5 mm'),('robot_sensor_seat_z','85 mm'),('cover_roof_z','50.5 mm')]:
  p=d.userParameters.itemByName(name);old=p.expression
  try:
   p.expression=expression;assert d.computeAll();edited=state();errors=[];offsets={group:[d.unitsManager.evaluateExpression(rule[axis],'mm')*10 for axis in ['x','y','z']] for group,rule in PLAN['groups'].items()}
   for key,row in edited.items():
    original=baseline[key];offset=offsets[PLAN['assignments'][key]];expected=[v+offset[i%3] for i,v in enumerate(original['bounds_mm'])];error=max(abs(a-b) for a,b in zip(row['bounds_mm'],expected));assert error<.001,(name,key,error,row['bounds_mm'],expected);assert abs(row['volume_mm3']-original['volume_mm3'])<max(.001,1e-7*original['volume_mm3']),(name,key,'changed reference geometry');assert (row['features'],row['sketches'])==(original['features'],original['sketches']);errors.append(error)
   cases.append({'parameter':name,'expression':expression,'frame_offsets_mm':offsets,'instances_checked':len(edited),'maximum_world_bounds_error_mm':max(errors),'passed':True})
  finally:p.expression=old;assert d.computeAll()
  restored=state();error=max(abs(a-b) for key in instances for a,b in zip(restored[key]['bounds_mm'],baseline[key]['bounds_mm']));assert error<.001,(name,'restore',error);cases[-1]['restore_max_world_bounds_error_mm']=error
 for c in d.allComponents:assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),c.name
 print(json.dumps({'passed':True,'saved':False,'baseline':baseline,'edits':cases,'physical_or_reference_instances':len(instances),'elapsed_seconds':time.monotonic()-tick,'scope':'Ninety fixed-body items follow fourteen native placement datums. Purchased geometry does not scale. Electronics keepout remains a nonphysical reference. Screw-length selection, button retention and battery adapter selection remain separate engineering work.'}))
'''.replace('PLAN',repr(plan()))
r=rpc(s,'body-reference-family-edit-restore',timeout=480);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/body-reference-family-edit-restore.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'cases':len(record['edits']),'instances':record['physical_or_reference_instances'],'seconds':record['elapsed_seconds']})
