"""Native worst-case interval expressions, separate from geometry allowances."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/intent_geometry.py').read_text()+'''
def run(_context: str):
 import json
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);g=IntentGeometry(d,d.rootComponent);variations={}
 for item in ['bearing_od','bearing_id','bearing_width','bearing_seat','axle_od','fork_gap','rod_thickness','bushing_flange','spacer_length','bearing_station_span']:
  for bound in ['minus','plus']:
   name='tol_'+item+'_'+bound;g.parameter(name,0,comment='Nonnegative manufacturing variation magnitude, not a CAD allowance. UNMEASURED reference default; zero is not evidence of perfect manufacture.');variations[name]=d.userParameters.itemByName(name).expression
 formulas={
 'stack_bearing_seat_min':'2*lc_bearing_seat_radius-tol_bearing_seat_minus-lc_bearing_od-tol_bearing_od_plus',
 'stack_bearing_seat_max':'2*lc_bearing_seat_radius+tol_bearing_seat_plus-lc_bearing_od+tol_bearing_od_minus',
 'stack_axle_running_min':'lc_bearing_id-tol_bearing_id_minus-fit_axle_nominal_od-tol_axle_od_plus',
 'stack_axle_running_max':'lc_bearing_id+tol_bearing_id_plus-fit_axle_nominal_od+tol_axle_od_minus',
 'stack_fork_side_min':'lc_drive_fork_gap-tol_fork_gap_minus-lc_rod_thickness-tol_rod_thickness_plus-2*(fit_bushing_flange_thickness+tol_bushing_flange_plus)',
 'stack_fork_side_max':'lc_drive_fork_gap+tol_fork_gap_plus-lc_rod_thickness+tol_rod_thickness_minus-2*(fit_bushing_flange_thickness-tol_bushing_flange_minus)',
 'stack_spacer_excess_min':'lc_knee_spacer_length-tol_spacer_length_minus-(lc_bearing_span+tol_bearing_station_span_plus-lc_bearing_width+tol_bearing_width_minus)',
 'stack_spacer_excess_max':'lc_knee_spacer_length+tol_spacer_length_plus-(lc_bearing_span-tol_bearing_station_span_minus-lc_bearing_width-tol_bearing_width_plus)',
 }
 for name,expression in formulas.items():g.parameter(name,expression,comment='Deterministic worst-case interval; no statistical RSS. Negative seat/shaft clearance means interference; positive spacer excess means spacer longer than available gap.')
 def values():return {name:d.userParameters.itemByName(name).value*10 for name in formulas}
 nominal=values();rows=[]
 try:
  for factor,label in [(0,'Nominal interval'),(.5,'Half illustrative variation'),(1,'Full illustrative variation')]:
   for name in variations:
    value=(.02 if 'bushing_flange' in name or 'bearing_width' in name else .05)*factor;d.userParameters.itemByName(name).expression=str(value)+' mm'
   assert d.computeAll();result=values();expected={'stack_bearing_seat_min':-.1*factor,'stack_bearing_seat_max':.1*factor,'stack_axle_running_min':-.1*factor,'stack_axle_running_max':.1*factor,'stack_fork_side_min':.4-.14*factor,'stack_fork_side_max':.4+.14*factor,'stack_spacer_excess_min':-.12*factor,'stack_spacer_excess_max':.12*factor};assert all(abs(result[key]-value)<1e-8 for key,value in expected.items()),(result,expected);rows.append({'case':label,'values_mm':result,'passed':True,'scope':'Illustrative arithmetic exercise, not measured or recommended production tolerances.'})
 finally:
  for name,expression in variations.items():d.userParameters.itemByName(name).expression=expression
  assert d.computeAll()
 assert all(abs(values()[key]-value)<1e-8 for key,value in nominal.items());print(json.dumps({'passed':True,'saved':False,'manufacturing_deviation_parameters':list(variations),'native_worst_case_formulas':formulas,'cases':rows,'restored':values(),'measurement_status':'Unmeasured. Supplier tolerances and print/CNC coupons remain required; no production fit qualification.'}))
'''
r=rpc(s,'native-leg-fit-stacks',timeout=120);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/native-leg-fit-stacks.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'variation_parameters':len(record['manufacturing_deviation_parameters']),'stack_expressions':len(record['native_worst_case_formulas'])})
