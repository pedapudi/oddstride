"""Exercise six independent design/fit dimensions and restore the native bench parts."""
import json,sys
from pathlib import Path
from run_native import rpc
from motor_complex_exports import COMPONENTS
ROOT=Path(__file__).resolve().parents[1];remaining='--remaining'in sys.argv
s=(ROOT/'source/native_documents.py').read_text()+'''\nimport adsk.core as core,adsk.fusion as fusion,json,time,os,tempfile

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);parts={key:next(c for c in d.allComponents if c.partNumber==number)for key,number in PARTS.items()};tick=time.monotonic();rows=[]
 def measure():
  result={}
  for key,c in parts.items():
   assert c.bRepBodies.count==1,(key,c.bRepBodies.count);b=c.bRepBodies.item(0);bb=b.boundingBox;result[key]={'bounds_mm':[v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]],'volume_mm3':b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000,'default_volume_mm3':b.volume*1000};assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),key
  return result
 def cylinder(key,radius):
  radii=[core.Cylinder.cast(f.geometry).radius*10 for f in parts[key].bRepBodies.item(0).faces if core.Cylinder.cast(f.geometry)]
  assert min(abs(r-radius)for r in radii)<1e-5,(key,radius,radii)
 baseline=measure();tests=[('lc_thigh_length','175 mm'),('pc_case_diametral_allowance','3.2 mm'),('pc_pilot_diametral_allowance','.4 mm'),('pr_seat_diametral_allowance','.25 mm'),('pr_bearing_center_span','15 mm'),('fit_m4_hole_diametral_clearance','.5 mm')]
 if REMAINING:tests=tests[4:]
 for name,value in tests:
  test_started=time.monotonic();parameter=d.userParameters.itemByName(name);old=parameter.expression
  try:
   parameter.expression=value;assert d.computeAll();current=measure()
   if name=='lc_thigh_length':
    for key in ['thigh_inner','thigh_outer']:assert abs(current[key]['bounds_mm'][2]-baseline[key]['bounds_mm'][2]+5)<.01
   elif name=='pc_case_diametral_allowance':cylinder('motor_carrier_1',40.85);cylinder('motor_carrier_1',24.95)
   elif name=='pc_pilot_diametral_allowance':cylinder('hip_stator_closure_1',5);cylinder('motor_carrier_1',4.8)
   elif name=='pr_seat_diametral_allowance':cylinder('roll_cartridge_1',32.625);cylinder('roll_stator_backplate_1',32.5)
   elif name=='pr_bearing_center_span':assert abs(current['roll_cartridge_1']['bounds_mm'][3]-baseline['roll_cartridge_1']['bounds_mm'][3]-1)<.001
   elif name=='fit_m4_hole_diametral_clearance':
    for key in ['input_crank','motor_carrier_1','hip_stator_closure_1']:cylinder(key,2.25)
   rows.append({'parameter':name,'original_expression':old,'tested_expression':value,'feature_health_passed':True,'interface_expectations_passed':True,'geometry':current})
  finally:parameter.expression=old;assert d.computeAll()
  restored=measure();drift=max(abs(a-b)for key in parts for a,b in zip(restored[key]['bounds_mm'],baseline[key]['bounds_mm']));volume=max(abs(restored[key]['volume_mm3']-baseline[key]['volume_mm3'])for key in parts);assert drift<.00001,(name,drift,volume);changed=[key for key in parts if abs(restored[key]['volume_mm3']-baseline[key]['volume_mm3'])>=.002];paths=[]
  for key in changed:
   path=os.path.join(tempfile.gettempdir(),'tinfox-native','motor-complex-restore-'+name+'-'+key+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,parts[key]));paths.append({'part':key,'path':path,'baseline_volume_mm3':baseline[key]['volume_mm3'],'restored_volume_mm3':restored[key]['volume_mm3']})
  rows[-1].update(restore_export_comparison_required=paths,restored_geometry=restored,restored_bounds_max_mm=drift,restored_volume_max_mm3=volume,elapsed_seconds=time.monotonic()-test_started);open(os.path.join(tempfile.gettempdir(),'tinfox-native','motor-complex-family-progress.json'),'w').write(json.dumps({'tests_complete':len(rows),'last_test':name,'elapsed_seconds':time.monotonic()-tick,'tests':rows}))
 print(json.dumps({'passed':not any(r['restore_export_comparison_required']for r in rows),'native_parameter_edits_passed':True,'saved':False,'tests':rows,'baseline_geometry':baseline,'elapsed_seconds':time.monotonic()-tick,'scope':'Six meaningful native geometry/fit edits and restore; purchased hardware dimensions are not scaled, and loaded strength/physical fit is not established.'}))
'''.replace('PARTS',repr({k:v[0]for k,v in COMPONENTS.items()})).replace('REMAINING',repr(remaining))
r=rpc(s,'motor-complex-family-edits',timeout=900);assert r[0]['success'],r;record=json.loads(r[0]['message'])
if remaining:
 progress=json.loads((ROOT/'audits/motor-complex-family-first-four-progress.json').read_text());assert progress['tests_complete']==4 and progress['last_test']=='pr_seat_diametral_allowance'
 timing=json.loads((ROOT/'audits/motor-complex-family-low-accuracy-timing.json').read_text());original=json.loads((ROOT/'audits/motor-complex-family-restore-inspection.json').read_text())['parameters'];prefix=[]
 for name,value in [('lc_thigh_length','175 mm'),('pc_case_diametral_allowance','3.2 mm'),('pc_pilot_diametral_allowance','.4 mm'),('pr_seat_diametral_allowance','.25 mm')]:
  prefix.append({'parameter':name,'original_expression':original[name],'tested_expression':value,'feature_health_passed':True,'interface_expectations_passed':True,'restored_bounds_upper_bound_mm':.00001,'restored_default_volume_upper_bound_mm3':.002,'evidence_kind':'Assertions completed before the persisted four-test checkpoint; detailed per-body values were not retained after the later fifth-test numerical failure.','evidence_progress':'audits/motor-complex-family-first-four-progress.json','executed_script_sha256':timing['script_sha256']})
 record['tests']=prefix+record['tests'];record['preserved_default_accuracy_failure']='audits/motor-complex-family-low-accuracy-diagnostic.json';record['restored_native_fingerprint']='audits/motor-complex-family-restore-inspection.json';record['volume_checker']='VeryHigh native physical properties for resumed tests; any remaining integration discrepancy requires independent exported-solid comparison. Original first-four strict default-volume assertions passed.';record['preserved_very_high_accuracy_failure']='audits/motor-complex-family-very-high-diagnostic.json'
(ROOT/'audits/motor-complex-family-edits.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'tests':len(record['tests']),'seconds':record['elapsed_seconds']})
