"""Edit and restore a functional parameter in a scratch native archive.

The master document is never edited. Supply an exact parameter name after
reviewing its meaning; this test must change the selected part's final volume.
"""
import sys,json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
def test(part,parameter,expression,part_archive=False):
 script='''import adsk.core as core,adsk.fusion as fusion,json,tempfile,os
def run(_context: str):
 app=core.Application.get();master=app.activeDocument
 assert master.name.startswith('Tinfox - Native Master Assembly')
 path=os.path.join(tempfile.gettempdir(),'tinfox-native',PART+'.f3d' if PART_ARCHIVE else 'Tinfox-Native-Master.f3d')
 scratch=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(path))
 d=fusion.Design.cast(app.activeProduct)
 def perform():
  component=d.rootComponent if PART_ARCHIVE else next(occ.component for group in d.rootComponent.occurrences for occ in group.component.occurrences if occ.component.partNumber==PART)
  assert component.partNumber==PART
  parameter=d.userParameters.itemByName(PARAMETER);assert parameter is not None
  original=parameter.expression
  def volume():return sum(b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume for b in component.bRepBodies)*1000
  def errors():return [{'name':feature.name,'message':feature.errorOrWarningMessage} for feature in component.features if feature.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]
  assert d.computeAll()
  before=volume();baseline_errors=errors();assert not baseline_errors,baseline_errors
  parameter.expression=EXPRESSION;assert d.computeAll()
  changed=volume();changed_errors=errors()
  assert not changed_errors,changed_errors
  assert abs(changed-before)>max(.001,abs(before)*1e-8),'Parameter did not affect manufactured geometry'
  parameter.expression=original;assert d.computeAll()
  restored=volume();restored_errors=errors()
  assert not restored_errors,restored_errors
  assert abs(restored-before)<max(.001,abs(before)*1e-8),('Restore changed geometry',before,restored)
  result={'part':PART,'parameter':PARAMETER,'original_expression':original,'test_expression':EXPRESSION,'before_volume_mm3':before,'changed_volume_mm3':changed,'restored_volume_mm3':restored,'feature_count':component.features.count,'sketch_count':component.sketches.count,'changed_feature_errors':changed_errors,'restored_feature_errors':restored_errors,'scratch_document_closed_without_save':True,'passed':True}
  return result
 try:result=perform()
 finally:
  scratch.close(False);master.activate()
 print(json.dumps(result))
'''
 for token,value in [('PART_ARCHIVE',part_archive),('PART',part),('PARAMETER',parameter),('EXPRESSION',expression)]:script=script.replace(token,repr(value))
 result=rpc(script,part+'-editability',timeout=900)
 if not result[0].get('success',True):return False
 (ROOT/'audits'/f'{part}-editability.json').write_text(json.dumps(json.loads(result[0]['message']),indent=2));return True
if __name__=='__main__':sys.exit(0 if test(*sys.argv[1:4],part_archive='--part-archive' in sys.argv) else 1)
