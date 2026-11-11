"""Separate frozen nominal hardware dimensions from editable prototype allowances."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py'])+'''
import json
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);g=IntentGeometry(d,d.rootComponent);rows=[]
 values={'mc_m3_shank_nominal':3,'mc_m4_shank_nominal':4,'mc_m3_through_diametral_allowance':.4,'mc_m4_through_diametral_allowance':.4,'mc_rs02_case_diameter':78.5,'pc_case_diametral_allowance':3,'pc_pilot_diametral_allowance':.3,'mc_m3_socket_head_diameter':5.5,'mc_m3_head_access_diametral_allowance':.9,'mc_m4_socket_head_diameter':7,'mc_m4_head_access_diametral_allowance':1}
 for key,value in values.items():g.parameter(key,value,comment='Frozen nominal reference or independent functional diametral allowance. Prototype fit has not been qualified by physical measurement; no manufacturing variation is implied.')
 bindings={'mc_m3_shank_nominal':'fit_m3_nominal_diameter','mc_m4_shank_nominal':'fit_m4_nominal_diameter','mc_m3_through_diametral_allowance':'fit_m3_hole_diametral_clearance','mc_m4_through_diametral_allowance':'fit_m4_hole_diametral_clearance','pc_motor_screw_radius':'(mc_m3_shank_nominal+mc_m3_through_diametral_allowance+fit_carrier_hole_compensation)/2','ph_stator_hole_radius':'(mc_m3_shank_nominal+mc_m3_through_diametral_allowance+fit_carrier_hole_compensation)/2','pr_retainer_bolt_radius':'(mc_m3_shank_nominal+mc_m3_through_diametral_allowance+fit_carrier_hole_compensation)/2','pc_closure_screw_radius':'(mc_m4_shank_nominal+mc_m4_through_diametral_allowance+fit_carrier_hole_compensation)/2','pr_motor_output_bolt_radius':'fit_carrier_output_hole_radius','lc_rs02_output_hole_radius':'(fit_m4_nominal_diameter+fit_m4_hole_diametral_clearance+fit_hole_compensation)/2','pc_motor_bore':'mc_rs02_case_diameter+pc_case_diametral_allowance+fit_carrier_hole_compensation','pc_pilot_clearance':'(pc_pilot_diametral_allowance+fit_carrier_hole_compensation)/2','pr_seat_radius':'(pr_bearing_od+pr_seat_diametral_allowance+fit_carrier_hole_compensation)/2','mc_thigh_head_access_diameter':'mc_m3_socket_head_diameter+mc_m3_head_access_diametral_allowance+fit_hole_compensation','lc_rs02_output_head_radius':'(fit_m4_socket_head_nominal_diameter+fit_output_head_diametral_clearance+fit_hole_compensation)/2'}
 for key,expression in bindings.items():
  p=d.userParameters.itemByName(key);assert p;before=p.value;old=p.expression;p.expression=expression;assert abs(p.value-before)<1e-9,(key,before,p.value);rows.append({'parameter':key,'old_expression':old,'expression':expression,'baseline_value_cm':p.value})
 crank=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_mc_input_crank')
 for sk in crank.sketches:
  for dim in sk.sketchDimensions:
   before=dim.parameter.value;old=dim.parameter.expression.strip();replacement={'lc_rs02_output_hole_radius':'fit_crank_output_hole_radius','lc_rs02_output_head_radius':'fit_crank_output_head_radius'}.get(old)
   if replacement:dim.parameter.expression=replacement;assert abs(dim.parameter.value-before)<1e-9;rows.append({'sketch':sk.name,'old_expression':old,'expression':replacement,'baseline_value_cm':dim.parameter.value})
 assert d.computeAll();issues=[{'component':c.partNumber,'feature':f.name,'message':f.errorOrWarningMessage}for c in d.allComponents for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues
 print(json.dumps({'saved':False,'bindings':rows,'baseline_values_unchanged':True,'feature_health_passed':True,'physical_fit_qualified':False}))
'''
r=rpc(s,'motor-complex-fit-bindings',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/motor-complex-fit-bindings.json').write_text(json.dumps(record,indent=2));print(record)
