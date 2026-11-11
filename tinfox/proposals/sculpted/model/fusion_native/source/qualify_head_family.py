"""Connect and exercise meaningful native Head family dimensions."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
script=(ROOT/'source/intent_geometry.py').read_text()+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent
 components={o.component.partNumber:o.component for o in root.occurrences};assert set(components)=={'sensor_bezel','CANDIDATE_front_fascia','CANDIDATE_body_nose_surround'};nose=components['CANDIDATE_body_nose_surround'];g=IntentGeometry(d,nose)
 for name,value in {'nose_mount_setback':64,'nose_profile_start_setback':53,'nose_extension':60.4,'nose_rounding_length':31.4,'nose_end_start_setback':4.4}.items():g.parameter(name,value,comment='Head placement relative to the hip station; independent of motor fits')
 bindings={'nose_mount_x':'body_hip_x - nose_mount_setback','nose_loft_start_x':'body_hip_x - nose_profile_start_setback','nose_end_x':'body_hip_x + nose_extension','nose_rounding_start_x':'nose_end_x - nose_rounding_length','nose_end_start_x':'nose_end_x - nose_end_start_setback','head_face_reference_x':'nose_end_x','head_face_tool_back_x':'head_face_reference_x - 65.4 mm','head_face_tool_half_width':'body_envelope_width / 2 - 1.2 mm','head_face_tool_half_height':'head_face_half_height + 13 mm','bezel_tool_start_x':'head_face_reference_x - 6.4 mm'}
 for name,expr in bindings.items():d.userParameters.itemByName(name).expression=expr
 for plane in nose.constructionPlanes:
  if plane.name=='Sensor access aperture datum':plane.definition.offset.expression='head_face_reference_x - 19.4 mm'
  if plane.name=='Fascia screw pilots datum':plane.definition.offset.expression='head_face_reference_x - 6.9 mm'
 assert d.computeAll()
 def state():
  result={}
  for key,c in components.items():
   assert c.bRepBodies.count==1;body=c.bRepBodies.item(0);box=body.boundingBox;issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]
   result[key]={'volume_mm3':body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000,'bounds_mm':[v*10 for v in box.minPoint.asArray()+box.maxPoint.asArray()],'faces':body.faces.count,'edges':body.edges.count,'issues':issues}
  return result
 baseline=state();assert not any(row['issues'] for row in baseline.values());tests=[]
 def points(body):
  calc=body.meshManager.createMeshCalculator();calc.surfaceTolerance=.002;calc.maxNormalDeviation=.1;nodes=calc.calculate().nodeCoordinates;return [nodes[round(i*(len(nodes)-1)/79)] for i in range(80)]
 reference_bodies={key:fusion.TemporaryBRepManager.get().copy(c.bRepBodies.item(0)) for key,c in components.items()};reference_points={key:points(c.bRepBodies.item(0)) for key,c in components.items()}
 def restore_geometry():
  rows={}
  for key,c in components.items():
   current_native=c.bRepBodies.item(0);occ=next(o for o in root.occurrences if o.component==c);current=current_native.createForAssemblyContext(occ);errors=[abs(app.measureManager.measureMinimumDistance(current,p).value-app.measureManager.measureMinimumDistance(reference_bodies[key],p).value)*10 for p in reference_points[key]]+[abs(app.measureManager.measureMinimumDistance(reference_bodies[key],p).value-app.measureManager.measureMinimumDistance(current,p).value)*10 for p in points(current_native)];rows[key]={'samples':len(errors),'maximum_mm':max(errors),'method':'Paired distance to restored and frozen native boundary at the same mesh sample; subtracts tessellation residual.'}
  return rows
 for name,value,expected in [('body_hip_x','190 mm',list(components)),('body_envelope_width','224.4 mm',['CANDIDATE_body_nose_surround','CANDIDATE_front_fascia']),('nose_bridge_depth','39 mm',['CANDIDATE_body_nose_surround']),('nose_wall','3.8 mm',['CANDIDATE_body_nose_surround']),('nose_fascia_fit_gap','.45 mm',['CANDIDATE_body_nose_surround'])]:
  p=d.userParameters.itemByName(name);old=p.expression;before=state()
  try:p.expression=value;assert d.computeAll();changed=state()
  finally:p.expression=old;d.computeAll()
  restored=state();restore_errors={key:{'volume_mm3':abs(restored[key]['volume_mm3']-before[key]['volume_mm3']),'bounds_mm':max(abs(a-b) for a,b in zip(restored[key]['bounds_mm'],before[key]['bounds_mm']))} for key in components}
  if name=='body_hip_x':response=all(max(abs((b-a)-(5 if i in [0,3] else 0)) for i,(a,b) in enumerate(zip(before[key]['bounds_mm'],changed[key]['bounds_mm'])))<.002 for key in expected)
  else:response=all(abs(changed[key]['volume_mm3']-before[key]['volume_mm3'])>1 for key in expected)
  geometry=restore_geometry()
  passed=response and not any(row['issues'] for row in changed.values()) and not any(row['issues'] for row in restored.values()) and all(row['volume_mm3']<2e-4*before[key]['volume_mm3'] and row['bounds_mm']<.002 and geometry[key]['maximum_mm']<.002 for key,row in restore_errors.items())
  record={'parameter':name,'test_expression':value,'restored_expression':old,'expected_response_parts':expected,'before':before,'changed':changed,'restore_errors':restore_errors,'restored_surface_probes':geometry,'mass_property_note':'Fusion VeryHighCalculationAccuracy is documented as +/-0.01%; paired volume measurements are checked against that uncertainty. Actual restoration also requires bidirectional surface probes within 0.002 mm.','passed':passed};tests.append(record);assert passed,record
 folder=os.path.join(tempfile.gettempdir(),'tinfox-native');paths=[]
 for occ in root.occurrences:
  c=occ.component;key=c.partNumber.replace('CANDIDATE_','');occ.isLightBulbOn=True;c.bRepBodies.item(0).isLightBulbOn=True;path=os.path.join(folder,key+'-restored.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));paths.append(path);occ.isLightBulbOn=False
 print(json.dumps({'bindings':bindings,'tests':tests,'baseline':baseline,'restored':state(),'passed':True,'paths':paths,'scope':'Head subsystem only. The complete robot assembly, motor-family variants and 20 kg load capability remain unqualified.','saved':False}))
'''
r=rpc(script,'head-family-edit-restore',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/head-family-edit-restore.json').write_text(json.dumps(record,indent=2))
for path in record['paths']:fetch(path,Path(path).name)
print(json.dumps({'passed':record['passed'],'tests':[(r['parameter'],r['passed']) for r in record['tests']],'paths':record['paths']}))
