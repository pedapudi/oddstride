"""Check that native parametric mirror links survive assembly organization."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
file_id=json.loads((ROOT/'manifests/subsystems.json').read_text())['subsystems']['leg']['file_id']
script=script_header()+'''import adsk.core as core,adsk.fusion as fusion,json,tempfile,os

def run(_context: str):
 app=core.Application.get();leg=next(d for d in app.documents if d.isSaved and d.dataFile.id==LEG_FILE);leg.activate();assert not leg.isModified
 capacity=require_personal_capacity(app,leg,KNOWN,new_cloud_files=0,reserve_slots=1);design=fusion.Design.cast(app.activeProduct);path=os.path.join(tempfile.gettempdir(),'tinfox-native','Leg-reparenting-audit.f3d');assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(path))
 scratch=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(path));d=fusion.Design.cast(app.activeProduct);root=d.rootComponent
 def perform():
  keys=['thigh_outer','thigh_outer_right'];occurrences={o.component.partNumber:o for o in root.occurrences if o.component.partNumber in keys}
  def state(c):
   bounds=[]
   for b in c.bRepBodies:
    box=b.boundingBox;bounds.append([box.minPoint.x,box.minPoint.y,box.minPoint.z,box.maxPoint.x,box.maxPoint.y,box.maxPoint.z])
   return {'features':c.features.count,'sketches':c.sketches.count,'volume_mm3':sum(b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume for b in c.bRepBodies)*1000,'bounds_cm':bounds,'issues':[f.name+': '+f.errorOrWarningMessage for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]}
  before={k:state(o.component) for k,o in occurrences.items()};moved={}
  for i,key in enumerate(keys):
   frame=root.occurrences.addNewComponent(core.Matrix3D.create());frame.component.name='Reparenting audit '+key
   matrix=core.Matrix3D.create();matrix.translation=core.Vector3D.create(12,(1 if i==0 else -1)*18,3);frame.transform2=matrix
   result=occurrences[key].moveToComponent(frame);assert result is not None
   proxy=result if result.assemblyContext else result.createForAssemblyContext(frame);proxy.transform2=frame.transform2;moved[key]=result.component
  assert d.computeAll();after={k:state(c) for k,c in moved.items()}
  for key in keys:
   a=before[key];b=after[key];assert a['features']==b['features'] and a['sketches']==b['sketches'] and not b['issues'],(key,a,b)
   assert abs(a['volume_mm3']-b['volume_mm3'])<.001 and max(abs(x-y) for aa,bb in zip(a['bounds_cm'],b['bounds_cm']) for x,y in zip(aa,bb))<1e-6,(key,a,b)
  parameter=d.userParameters.itemByName('lc_thigh_length');assert parameter is not None;original=parameter.expression
  try:
   parameter.expression='('+original+') + 5 mm';assert d.computeAll();changed={k:state(c) for k,c in moved.items()}
  finally:parameter.expression=original;d.computeAll()
  restored={k:state(c) for k,c in moved.items()}
  for key in keys:assert abs(changed[key]['volume_mm3']-before[key]['volume_mm3'])>.001 and abs(restored[key]['volume_mm3']-before[key]['volume_mm3'])<.001 and not changed[key]['issues'] and not restored[key]['issues'],key
  return {'before':before,'after_reparenting':after,'after_parameter_change':changed,'after_restore':restored,'parameter':parameter.name,'native_reparenting_qualified':True,'source_leg_modified':leg.isModified,'scope':'Discarded native scratch copy; no working subsystem changed.'}
 try:result=perform()
 finally:scratch.close(False);leg.activate()
 print(json.dumps(result))
'''.replace('LEG_FILE',repr(file_id)).replace('KNOWN',repr(known_files()))
r=rpc(script,'native-reparenting-test',timeout=300);assert r[0].get('success'),r
record=json.loads(r[0]['message']);(ROOT/'audits/native-reparenting-test.json').write_text(json.dumps(record,indent=2));print(json.dumps({'passed':record['native_reparenting_qualified'],'source_leg_modified':record['source_leg_modified']},indent=2))
