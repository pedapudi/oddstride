"""Native fit expressions preserving the frozen nominal limb geometry.

Functional allowances are independent of process compensation. Default print
and CNC compensation is zero until measured; neither profile is fit-qualified.
Hardware nominals are the frozen CAD references, not purchased-part inspection.
"""
class LegFitParameters:
 def __init__(self,g):self.g=g;self.d=g.design;self.records=[]
 def add(self,name,value,comment,units='mm'):
  self.g.parameter(name,value,units,comment=comment)
 def bind(self,name,expression):
  p=self.d.userParameters.itemByName(name);assert p is not None,name;before=p.expression;p.expression=expression;self.records.append({'parameter':name,'old_expression':before,'expression':expression})
 def apply(self):
  nominal='Frozen hardware nominal; independent of robot scale. Delivered dimensions require inspection.'
  for name,value in {'fit_axle_nominal_od':12,'fit_shoulder_pin_nominal_od':6,'fit_shoulder_thread_nominal_diameter':5,'fit_shoulder_head_nominal_diameter':10,'fit_m4_nominal_diameter':4,'fit_m3_nominal_diameter':3,'fit_m4_nut_nominal_af':7,'fit_m5_nut_nominal_af':8,'fit_m4_socket_head_nominal_diameter':7,'fit_bushing_nominal_od':8,'fit_bushing_flange_thickness':1,'fit_compression_sleeve_nominal_od':8,'fit_rs02_case_nominal_diameter':82}.items():self.add(name,value,nominal)
  self.add('fit_process_cnc',0,'Structural shell process: 0 selects printed compensation; 1 selects CNC. Both remain unqualified until measured.','')
  for name in ['fit_print_hole_compensation','fit_cnc_hole_compensation','fit_print_seam_compensation','fit_cnc_seam_compensation']:
   self.add(name,0,'Measured process compensation only. Zero is the reference default, not a measured accuracy claim.')
  for name in ['fit_crank_process_cnc','fit_carrier_process_cnc']:self.add(name,1,'Part-family process: frozen aluminum route is CNC; choose 0 only for a separately qualified printed prototype.','')
  self.add('fit_hole_compensation','(1-fit_process_cnc)*fit_print_hole_compensation+fit_process_cnc*fit_cnc_hole_compensation','Active diametral hole compensation; never a radius.')
  for family in ['crank','carrier']:self.add('fit_'+family+'_hole_compensation','(1-fit_'+family+'_process_cnc)*fit_print_hole_compensation+fit_'+family+'_process_cnc*fit_cnc_hole_compensation','Diametral compensation for this part family only.')
  self.add('fit_seam_compensation','(1-fit_process_cnc)*fit_print_seam_compensation+fit_process_cnc*fit_cnc_seam_compensation','Active total normal seam compensation; shared equally between mating faces.')
  allowances={'fit_bearing_seat_diametral_allowance':0,'fit_axle_hole_diametral_clearance':.2,'fit_pin_journal_diametral_clearance':.1,'fit_pin_thread_diametral_clearance':.4,'fit_pin_head_diametral_clearance':.6,'fit_m4_hole_diametral_clearance':.4,'fit_m3_hole_diametral_clearance':.4,'fit_m4_nut_total_af_clearance':.2,'fit_m5_nut_total_af_clearance':.2,'fit_m4_head_diametral_clearance':1.2,'fit_output_head_diametral_clearance':1,'fit_thigh_head_diametral_clearance':1.8,'fit_rod_bushing_diametral_allowance':0,'fit_shin_sleeve_diametral_clearance':.1,'fit_thigh_sleeve_diametral_clearance':.2,'fit_fork_total_side_clearance':.4,'fit_rod_body_side_clearance':.5,'fit_spacer_length_adjustment':0,'fit_outer_race_axial_gap':.3,'fit_outer_race_radial_gap':.3,'fit_motor_case_radial_clearance':.25,'fit_carrier_case_radial_clearance':.5,'fit_shell_total_seam_gap':0}
  for name,value in allowances.items():self.add(name,value,'Functional allowance preserving frozen reference geometry. Not a supplier tolerance or measured process compensation.')
  self.add('fit_fork_center_y',70,'Fixed rod and fork midplane; changing side clearance relieves both ears without shifting the linkage.')
  self.add('fit_fork_far_end_y',86,'Frozen outer fork-ear face independent of running clearance.')
  self.add('fit_fork_far_bridge_end_y',82,'Frozen outer bridge-pad face independent of running clearance.')
  bindings={
   'lc_bearing_fit_allowance':'(fit_bearing_seat_diametral_allowance+fit_hole_compensation)/2',
   'lc_axle_outer_radius':'fit_axle_nominal_od/2',
   'lc_axle_fit_radius':'(fit_axle_nominal_od+fit_axle_hole_diametral_clearance+fit_hole_compensation)/2',
   'lc_pin_shoulder_clearance':'(fit_shoulder_pin_nominal_od+fit_pin_journal_diametral_clearance+fit_hole_compensation)/2',
   'lc_pin_thread_clearance':'(fit_shoulder_thread_nominal_diameter+fit_pin_thread_diametral_clearance+fit_hole_compensation)/2',
   'lc_pin_head_clearance':'(fit_shoulder_head_nominal_diameter+fit_pin_head_diametral_clearance+fit_hole_compensation)/2',
   'lc_clamp_bolt_radius':'(fit_m4_nominal_diameter+fit_m4_hole_diametral_clearance+fit_hole_compensation)/2',
   'lc_rs02_output_hole_radius':'(fit_m4_nominal_diameter+fit_m4_hole_diametral_clearance+fit_hole_compensation)/2',
   'lc_carrier_stator_hole':'(fit_m3_nominal_diameter+fit_m3_hole_diametral_clearance+fit_carrier_hole_compensation)/2',
   'lc_clamp_nut_af':'fit_m4_nut_nominal_af+fit_m4_nut_total_af_clearance+fit_hole_compensation',
   'lc_pin_nut_af':'fit_m5_nut_nominal_af+fit_m5_nut_total_af_clearance+fit_hole_compensation',
   'lc_clamp_head_radius':'(fit_m4_socket_head_nominal_diameter+fit_m4_head_diametral_clearance+fit_hole_compensation)/2',
   'lc_rs02_output_head_radius':'(fit_m4_socket_head_nominal_diameter+fit_output_head_diametral_clearance+fit_hole_compensation)/2',
   'lc_thigh_clamp_head_radius':'(fit_m4_socket_head_nominal_diameter+fit_thigh_head_diametral_clearance+fit_hole_compensation)/2',
   'lc_rod_eye_bore':'(fit_bushing_nominal_od+fit_rod_bushing_diametral_allowance+fit_cnc_hole_compensation)/2',
   'lc_compression_sleeve_outer_radius':'fit_compression_sleeve_nominal_od/2',
   'lc_clamp_sleeve_radius':'(fit_compression_sleeve_nominal_od+fit_shin_sleeve_diametral_clearance+fit_hole_compensation)/2',
   'lc_thigh_clamp_sleeve_radius':'(fit_compression_sleeve_nominal_od+fit_thigh_sleeve_diametral_clearance+fit_hole_compensation)/2',
   'lc_drive_fork_gap':'lc_rod_thickness+2*fit_bushing_flange_thickness+fit_fork_total_side_clearance',
   'lc_drive_near_ear_depth':'fit_fork_center_y-lc_drive_fork_gap/2-lc_drive_near_ear_y',
   'lc_drive_plate_thickness':'fit_fork_center_y-lc_drive_fork_gap/2-lc_drive_plate_y',
   'lc_drive_near_pad_depth':'fit_fork_center_y-lc_drive_fork_gap/2-lc_drive_bridge_y',
   'lc_drive_far_ear_y':'fit_fork_center_y+lc_drive_fork_gap/2',
   'lc_drive_far_ear_depth':'fit_fork_far_end_y-lc_drive_far_ear_y',
   'lc_drive_far_pad_depth':'fit_fork_far_bridge_end_y-lc_drive_far_ear_y',
   'lc_rod_y':'fit_fork_center_y-lc_rod_thickness/2',
   'lc_rod_channel_y':'fit_fork_center_y-lc_rod_thickness/2-fit_rod_body_side_clearance',
   'lc_rod_channel_width':'lc_rod_thickness+2*fit_rod_body_side_clearance',
   'lc_knee_spacer_length':'lc_bearing_span-lc_bearing_width+fit_spacer_length_adjustment',
   'lc_stop_axial_gap':'fit_outer_race_axial_gap',
   'lc_stop_radial_gap':'fit_outer_race_radial_gap',
   'lc_motor_case_radius':'fit_rs02_case_nominal_diameter/2',
   'lc_rs02_body_fit':'fit_motor_case_radial_clearance+fit_hole_compensation/2',
   'lc_carrier_shell_inner':'fit_rs02_case_nominal_diameter/2+fit_carrier_case_radial_clearance+fit_carrier_hole_compensation/2',
  }
  for name,expression in bindings.items():self.bind(name,expression)
  independent={
   'fit_crank_pin_shoulder_radius':'(fit_shoulder_pin_nominal_od+fit_pin_journal_diametral_clearance+fit_crank_hole_compensation)/2',
   'fit_crank_pin_head_radius':'(fit_shoulder_head_nominal_diameter+fit_pin_head_diametral_clearance+fit_crank_hole_compensation)/2',
   'fit_crank_pin_nut_af':'fit_m5_nut_nominal_af+fit_m5_nut_total_af_clearance+fit_crank_hole_compensation',
   'fit_crank_output_hole_radius':'(fit_m4_nominal_diameter+fit_m4_hole_diametral_clearance+fit_crank_hole_compensation)/2',
   'fit_crank_output_head_radius':'(fit_m4_socket_head_nominal_diameter+fit_output_head_diametral_clearance+fit_crank_hole_compensation)/2',
   'fit_carrier_output_hole_radius':'(fit_m4_nominal_diameter+fit_m4_hole_diametral_clearance+fit_carrier_hole_compensation)/2',
   'fit_metal_spacer_axle_bore_radius':'(fit_axle_nominal_od+fit_axle_hole_diametral_clearance+fit_cnc_hole_compensation)/2',
  }
  for name,expression in independent.items():self.add(name,expression,'Process-specific finished interface; independent of shell compensation.')
  return self.records
