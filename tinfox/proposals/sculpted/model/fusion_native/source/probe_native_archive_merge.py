"""Verify native F3D history can join a subsystem without a cloud part file."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
script=script_header()+'''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
 app=core.Application.get();master=next(d for d in app.documents if d.name.startswith('Tinfox - Native Master Assembly'));capacity=require_personal_capacity(app,master,KNOWN,new_cloud_files=0,reserve_slots=1)
 scratch=app.documents.add(core.DocumentTypes.FusionDesignDocumentType);scratch.name='Tinfox native archive merge audit';d=fusion.Design.cast(app.activeProduct);d.designType=fusion.DesignTypes.ParametricDesignType;d.attributes.add('Tinfox','ScratchAudit','Native archive history merge')
 def perform():
  path=os.path.join(tempfile.gettempdir(),'tinfox-native','thigh_outer.f3d');result=app.importManager.importToTarget2(app.importManager.createFusionArchiveImportOptions(path),d.rootComponent);assert result is not None
  component=next(c for c in d.allComponents if c.partNumber=='thigh_outer')
  features=[{'name':f.name,'type':f.objectType} for f in component.features]
  d.computeAll();baseline=[f.name+': '+f.errorOrWarningMessage for f in component.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]
  def volume():return sum(b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume for b in component.bRepBodies)*1000
  before=volume();changes=[]
  for p in d.userParameters:
   if not p.name.endswith('_makeCylinder_diameter') or abs(p.value-1.22)>1e-8:continue
   expression=p.expression;p.expression='('+expression+') + 0.1 mm';d.computeAll();changed=volume();p.expression=expression;d.computeAll();restored=volume()
   errors=[f.name+': '+f.errorOrWarningMessage for f in component.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]
   changes.append({'parameter':p.name,'before':before,'changed':changed,'restored':restored,'feature_issues':errors,'passed':abs(changed-before)>.001 and abs(restored-before)<.001 and not errors})
   if changes[-1]['passed']:break
  passed=component.features.count==137 and component.sketches.count==64 and not baseline and not any('BaseFeature' in f['type'] for f in features) and any(c['passed'] for c in changes)
  return {'archive':'thigh_outer.f3d','feature_count':component.features.count,'sketch_count':component.sketches.count,'parameter_count':d.userParameters.count,'baseline_volume_mm3':before,'baseline_feature_issues':baseline,'parameter_edits':changes,'native_archive_merge_qualified':passed,'imported_mesh_count':sum(c.meshBodies.count for c in d.allComponents),'base_feature_count':sum('BaseFeature' in f['type'] for f in features),'master_modified':master.isModified,'capacity':capacity,'scope':'Previously authored native F3D history merged into a discarded scratch design. No STEP/BRep geometry import; no master edits.'}
 try:result=perform()
 finally:scratch.close(False);master.activate()
 print(json.dumps(result))
'''.replace('KNOWN',repr(known_files()))
response=rpc(script,'native-archive-merge-test',timeout=120);assert response[0].get('success'),response
result=json.loads(response[0]['message']);(ROOT/'audits/native-archive-merge-test.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
