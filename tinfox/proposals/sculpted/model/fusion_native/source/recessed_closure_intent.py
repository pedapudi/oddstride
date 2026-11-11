"""Recess common closure buttons while retaining the rear locating web."""
class RecessedClosureIntent(PairedCupIntent):
 def parameters(self):
  super().parameters();g=self.g
  values={'rc_button_head_nominal_diameter':7.6,'rc_button_head_height':2.2,'rc_button_underhead_fillet_diameter':4.7,'rc_counterbore_diametral_allowance':.6,'rc_pilot_diametral_allowance':.1,'rc_lug_back_extension':1.1,'rc_cup_relief_diametral_allowance':.2,'rc_head_top_y':0,'rc_screw_length':16}
  for key,value in values.items():g.parameter(key,value,comment='Common M4 ISO7380-1 closure interface. Nominal vendor dimensions separate from prototype clearances; preload and printed fit unqualified.')
  derived={'rc_counterbore_radius':'(rc_button_head_nominal_diameter+rc_counterbore_diametral_allowance)/2','rc_screw_pilot_radius':'(rc_button_underhead_fillet_diameter+rc_pilot_diametral_allowance)/2','rc_lug_back_y':'pc_split_y-rc_lug_back_extension','rc_head_floor_y':'rc_head_top_y-rc_button_head_height','rc_cup_relief_radius':'pc_lug_radius+rc_cup_relief_diametral_allowance/2','rc_retained_closure_web':'rc_head_floor_y-(rc_lug_back_y+pc_pilot_length+pc_pilot_axial_clearance)','rc_screw_tip_y':'rc_head_floor_y-rc_screw_length'}
  for key,value in derived.items():g.parameter(key,value)
 def closure(self):
  self.parameters();g=self.g;c=self.c
  body=self.ring_y('pc_split_y','pc_closure_depth','pc_outer_radius','pc_closure_bore','Unchanged motor stator annulus')
  body=self.extrude_all(self.lugs('rc_lug_back_y','pc_lug_radius','Three reinforced rearward closure lugs'),'pc_closure_front_y-rc_lug_back_y','Integral reinforced closure lugs',fusion.FeatureOperations.JoinFeatureOperation,body)
  body=self.extrude_all(self.lugs('rc_lug_back_y-.5 mm','rc_screw_pilot_radius','Three standard screw and fillet clearances'),'pc_closure_front_y-rc_lug_back_y+1 mm','Open screw and underhead fillet passages',fusion.FeatureOperations.CutFeatureOperation,body)
  body=self.extrude_all(self.lugs('rc_lug_back_y','pc_pilot_radius+pc_pilot_clearance','Rear-facing locating pockets'),'pc_pilot_length+pc_pilot_axial_clearance','Rear locating pockets preserve the support web',fusion.FeatureOperations.CutFeatureOperation,body)
  body=self.extrude_all(self.lugs('rc_head_floor_y','rc_counterbore_radius','Three ordinary button-head seats'),'pc_closure_front_y-rc_head_floor_y+.5 mm','Straight-access recessed closure head seats',fusion.FeatureOperations.CutFeatureOperation,body)
  axis=self.axis_y('pr_pitch_x_offset','Motor stator');sk=self.circles('pc_split_y-1.5 mm',[('pr_pitch_x_offset+pr_stator_pcd_radius','0 mm','pc_motor_screw_radius')],'Stator mounting hole seed');body=self.extrude_all(sk,'pc_closure_depth+2.9 mm','Stator mounting hole seed',fusion.FeatureOperations.CutFeatureOperation,body);body=self.pattern(c.features.extrudeFeatures.item(c.features.extrudeFeatures.count-1),axis,'9','Nine stator mounting holes')
  seed=self.cone_y(body,'pr_pitch_x_offset+pr_stator_pcd_radius','pc_closure_front_y-pc_motor_head_depth','pc_motor_screw_radius','pc_motor_head_radius','pc_motor_head_depth','Unchanged motor flat-head mounting seat');return self.pattern(seed,axis,'9','Nine unchanged motor flat-head seats')
 def revise_cup(self,parent,front):
  self.parameters();g=self.g;c=self.c;center='pr_pitch_x_offset'if front==1 else'-pr_pitch_x_offset';objects=core.ObjectCollection.create();objects.add(parent);copy=c.features.copyPasteBodies.add(objects);copy.name='Linked correctly clocked paired-bearing cup';body=copy.bodies.item(0)
  def profiles(y,radius,name,inner=None):
   definitions=[]
   for angle in [90,215,325]:
    x=f'({center})+pc_lug_pcd_radius*cos({angle} deg)';z=f'pc_lug_pcd_radius*sin({angle} deg)';definitions.append((x,z,radius))
    if inner:definitions.append((x,z,inner))
   return self.circles(y,definitions,name)
  sk=profiles('rc_lug_back_y','rc_cup_relief_radius','Three open reinforced-lug reliefs');body=self.extrude_all(sk,'pc_split_y+pc_pilot_length-rc_lug_back_y+1 mm','Lower cup lands and remove obsolete locating bosses',fusion.FeatureOperations.CutFeatureOperation,body)
  sk=profiles('rc_lug_back_y','pc_pilot_radius','Three relocated annular locating bosses','pc_closure_screw_radius');rings=core.ObjectCollection.create()
  for profile in sk.profiles:
   if profile.profileLoops.count==2:rings.add(profile)
  assert rings.count==3
  inp=c.features.extrudeFeatures.createInput(rings,fusion.FeatureOperations.JoinFeatureOperation);inp.participantBodies=[body];inp.setDistanceExtent(False,g.value('pc_pilot_length'));feature=c.features.extrudeFeatures.add(inp);feature.name='Relocated hollow pilots with unchanged screw bores';sk.isVisible=False;assert c.bRepBodies.count==1;return c.bRepBodies.item(0)
