"""Test link localization in an unsaved scratch design, never in the master."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
proof=json.loads((ROOT/'audits/native-part-document-proof.json').read_text())
script=script_header()+'''import adsk.core as core,adsk.fusion as fusion,json,tempfile,os

def run(_context: str):
 app=core.Application.get();master=next(d for d in app.documents if d.name.startswith('Tinfox - Native Master Assembly'))
 capacity=require_personal_capacity(app,master,KNOWN,new_cloud_files=0,reserve_slots=1)
 source=app.data.findFileById(SOURCE_FILE);assert source.isComplete
 scratch=app.documents.add(core.DocumentTypes.FusionDesignDocumentType);scratch.name='Tinfox native consolidation audit';design=fusion.Design.cast(app.activeProduct);design.designType=fusion.DesignTypes.ParametricDesignType;design.attributes.add('Tinfox','ScratchAudit','Native history localization')
 def perform():
  occurrence=design.rootComponent.occurrences.addByInsert(source,core.Matrix3D.create(),True);before=occurrence.component
  before_features=[{'name':f.name,'type':f.objectType} for f in before.features];before_sketches=before.sketches.count
  def volume(c):return sum(b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume for b in c.bRepBodies)*1000
  v0=volume(before);assert occurrence.breakLink();component=occurrence.component
  after_features=[{'name':f.name,'type':f.objectType} for f in component.features];after_sketches=component.sketches.count;v1=volume(component)
  retained=(after_sketches==before_sketches and len(after_features)>=len(before_features) and not any('BaseFeature' in f['type'] for f in after_features))
  edits=None
  candidates=[p for p in design.userParameters if 'stator_thickness' in p.name]
  if retained and len(candidates)==1:
   p=candidates[0];old=p.expression;p.expression='('+old+') * 1.1';design.computeAll();v2=volume(component);p.expression=old;design.computeAll();v3=volume(component)
   errors=[f.name+': '+f.errorOrWarningMessage for f in component.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]
   edits={'parameter':p.name,'before':v1,'changed':v2,'restored':v3,'feature_issues':errors,'passed':abs(v2/v1-1.1)<1e-7 and abs(v3-v1)<.001 and not errors}
  return {'source_file_id':SOURCE_FILE,'source_read_only':source.isReadOnly,'before_features':before_features,'after_features':after_features,'before_sketch_count':before_sketches,'after_sketch_count':after_sketches,'before_volume_mm3':v0,'after_volume_mm3':v1,'user_parameter_names':[p.name for p in design.userParameters],'history_inventory_preserved':retained,'parameter_edit_restore':edits,'native_localization_qualified':retained and edits is not None and edits['passed'],'master_modified':master.isModified,'capacity':capacity,'scope':'One native stator test in a discarded scratch design. No authoritative component links were changed.'}
 try:result=perform()
 finally:scratch.close(False);master.activate()
 print(json.dumps(result))
'''
for token,value in [('KNOWN',known_files()),('SOURCE_FILE',proof['file_id'])]:script=script.replace(token,repr(value))
response=rpc(script,'native-localization-test',timeout=120);assert response[0].get('success'),response
result=json.loads(response[0]['message']);(ROOT/'audits/native-localization-test.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
