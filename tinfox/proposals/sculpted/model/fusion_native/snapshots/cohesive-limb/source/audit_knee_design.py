"""Compare crank packaging and report transparent nominal load screens."""
import hashlib,json,math,sys
from pathlib import Path
from kinematics import ROOT
folder=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'output/cohesive-limb-work'
raw=(folder/'model.json').read_bytes();model=json.loads(raw);p=model['parameters']
angles=range(-156,-47)
def minimum_arm(radius,phase):return min(abs(radius*math.cos(math.radians(q+phase))) for q in angles)
clock=[{'phase_deg':phase,'minimum_arm_mm':minimum_arm(28,phase),'rod_force_at_17Nm_N':17000/minimum_arm(28,phase)} for phase in [-90,-84,-78,-72,-66]]
radii=[{'radius_mm':r,'minimum_arm_mm':minimum_arm(r,-78),'rod_force_at_17Nm_N':17000/minimum_arm(r,-78),'radial_tie_head_gap_mm':43.5-2.8-(r+10.5),'radial_housing_gap_mm':40.2-(r+10.5)} for r in [28,30,32,36]]
import engineering as eng
eng.DATA=model;eng.PARTS=model['parts'];eng.P.update(p)
base_mass=eng.mass_budget()['base_kg']
inner_center=p['knee_bearing_inner_y']+4;outer_center=p['knee_bearing_outer_y']+4;span=outer_center-inner_center
wall=p['knee_crown_radius']-14
loads=[]
for torque,g_factor in [(6,1),(17,3)]:
 rod_force=torque*1000/minimum_arm(p['crank_radius'],p['crank_phase_deg'])
 foot_force=(base_mass+1)*9.81*.5*g_factor
 # Sum magnitudes conservatively; the actual rod/foot directions generally differ.
 outer=rod_force*(70-inner_center)/span+foot_force*(67-inner_center)/span
 inner=rod_force*(outer_center-70)/span+foot_force*(outer_center-67)/span
 reaction=max(inner,outer)
 loads.append({'motor_torque_Nm':torque,'vertical_acceleration_factor':g_factor,'all_up_mass_kg':base_mass+1,
  'rod_force_N':rod_force,'assumed_foot_force_N':foot_force,'inner_bearing_reaction_bound_N':inner,'outer_bearing_reaction_bound_N':outer,
  'nominal_projected_bearing_pressure_MPa':reaction/(28*8),'nominal_two_ligament_stress_MPa':reaction/(2*wall*8),
  'nominal_output_pin_bearing_pressure_MPa':rod_force/(2*6*5.8)})
report={'model_sha256':hashlib.sha256(raw).hexdigest(),
 'decision':'Retain the 28 mm equal cranks and -78 degree phase. Reposition bearings and reserve separate stem/eye clearance volumes; do not extend the rocker into the motor tie screws.',
 'clock_comparison':clock,'radius_comparison':radii,
 'geometry':{'bearing_centers_y_mm':[inner_center,outer_center],'bearing_center_span_mm':span,'inner_shoulder_mm':66.5-(p['knee_bearing_inner_y']+8),'outer_shoulder_mm':p['knee_bearing_outer_y']-73.5,'nominal_radial_wall_mm':wall,'nominal_entry_lip_wall_mm':wall-1.2,'bearing_wall_verified_minimum_mm':5.4,'spacer_length_mm':16,'leg_width_change_mm':0,'ligament_between_bearing_bore_and_inner_pin_counterbore_mm':28-14-5.3},
 'load_screens':loads,
 'material_reference':{'title':'Bambu PETG HF Technical Data Sheet V1.0','url':'https://store.bblcdn.com/3a230e260a3a47c2b0db0156e07eef91.pdf','tensile_strength_xy_MPa':34,'tensile_strength_z_MPa':23,'notes':'Manufacturer coupon means, not allowable stresses. Test coupons used 100% infill and thermal conditioning. These values cannot qualify another PETG formulation or this printed joint.'},
 'qualification':'Geometry and nominal equilibrium screens only. No strength pass is assigned. The pressure/net-section figures omit local stress concentration, fit interference, fork bending, shell deformation, cyclic loads, temperature and creep. Printed bearing-fit and load tests remain required.'}
(folder/'knee-design-review.json').write_text(json.dumps(report,indent=2));print(json.dumps({'geometry':report['geometry'],'load_screens':loads},indent=2))
