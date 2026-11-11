"""Open paired-bearing cartridge and removable rear stator plate."""
class PairedHousingIntent(PairedRollIntent):
 def housing_parameters(self):
  self.parameters()
  for name,value in {'ph_column_radius':3.5,'ph_stator_hole_radius':1.7,'ph_stator_plate_bore_radius':27,'ph_retainer_nut_af':5.8,'ph_retainer_bolt_length':25,'ph_retainer_tip_offset':.5,'ph_retainer_nut_thickness':2.4,'ph_ear_x':-59.5,'ph_ear_y':26.5,'ph_lower_ear_z':-12,'ph_upper_ear_z':24,'ph_ear_width':11,'ph_ear_depth':13,'ph_ear_height':11,'ph_ear_round':2,'ph_ear_hole_radius':1.7}.items():self.g.parameter(name,value,comment='Frozen detached motor-fit cartridge dimension; printed strength and chassis integration remain unqualified.')
  self.g.parameter('ph_nut_pocket_end_x','pr_bearing_end_x+pr_retainer_thickness-ph_retainer_bolt_length+ph_retainer_tip_offset+ph_retainer_nut_thickness')
 def hexagons_x(self,x,name):
  g=self.g;c=self.c;plane=g.plane(c.yZConstructionPlane,x,name+' datum');sk=c.sketches.add(plane);sk.name=name;sk.isComputeDeferred=True
  for phase in [20,140,260]:
   cy=f'pr_retainer_lug_radius*cos({phase} deg)';cz=f'pr_retainer_lug_radius*sin({phase} deg)';points=[]
   # The source polygon starts on +Y after its original XZ section is turned
   # onto the bearing axis. A sign reversal is immaterial for this hexagon.
   for angle in range(0,360,60):
    y='('+cy+')+(ph_retainer_nut_af/sqrt(3))*cos('+str(angle)+' deg)';z='('+cz+')+(ph_retainer_nut_af/sqrt(3))*sin('+str(angle)+' deg)';p=g.skeleton_point(sk,'-('+z+')',y);g.point_dimensions(sk,p,'-('+z+')',y);points.append(p)
   for i,p in enumerate(points):sk.sketchCurves.sketchLines.addByTwoPoints(p,points[(i+1)%6])
  sk.isComputeDeferred=False;assert sk.profiles.count==3;return sk
 def cut_hexagons(self,body,x,depth,name):
  return CohesiveLimbIntent(self.g).extrude_all(self.hexagons_x(x,name),depth,name,fusion.FeatureOperations.CutFeatureOperation,body)
 def cartridge(self):
  self.housing_parameters();g=self.g;c=self.c;body=self.annulus('pr_housing_split_x','pr_bearing_end_x-pr_housing_split_x','pr_housing_radius','pr_seat_radius','Through-bored bearing barrel');body=self.patterned_circle(body,'pr_housing_split_x','pr_bearing_end_x-pr_housing_split_x','ph_column_radius','pr_stator_pcd_radius',0,9,'Nine stator screw columns',True);ears=[];limb=CohesiveLimbIntent(g)
  for z,label in [('ph_lower_ear_z','Lower'),('ph_upper_ear_z','Upper')]:
   ear=g.box('ph_ear_width','ph_ear_depth','ph_ear_height','ph_ear_x','ph_ear_y',z,label+' chassis attachment ear');ear=g.round_edges(ear,'ph_ear_round',label+' ear edge radii');sk=limb.circles('7 mm',[('ph_ear_x',z,'ph_ear_hole_radius')],label+' ear screw entry');ear=limb.extrude_all(sk,'30 mm',label+' ear screw entry',fusion.FeatureOperations.CutFeatureOperation,ear);ears.append(ear)
  body=g.combine(body,ears,fusion.FeatureOperations.JoinFeatureOperation,'Integral chassis attachment ears');body=self.patterned_circle(body,'pr_housing_split_x','pr_bearing_end_x-pr_housing_split_x','pr_retainer_lug_size','pr_retainer_lug_radius',20,3,'Three retaining-plate pillars',True);body=self.patterned_circle(body,'pr_housing_split_x-1 mm','pr_bearing_end_x-pr_housing_split_x+2 mm','pr_retainer_bolt_radius','pr_retainer_lug_radius',20,3,'Three retainer bolt passages');body=self.cut_hexagons(body,'pr_housing_split_x','ph_nut_pocket_end_x-pr_housing_split_x','Rear-open retainer nut seats');sk=self.circles('pr_housing_split_x-1 mm',[('0 mm','0 mm','pr_seat_radius')],'Full bearing press-out opening');body=g.extrude(sk,'pr_bearing_end_x-pr_housing_split_x+2 mm','Full bearing press-out opening',fusion.FeatureOperations.CutFeatureOperation,[body]).bodies.item(0);return self.patterned_circle(body,'pr_housing_split_x-1 mm','pr_bearing_end_x-pr_housing_split_x+2 mm','ph_stator_hole_radius','pr_stator_pcd_radius',0,9,'Nine motor-stator screw passages')
 def stator_backplate(self):
  self.housing_parameters();g=self.g;body=self.annulus('pr_housing_back_x','pr_stator_plate_thickness','pr_stator_plate_radius','ph_stator_plate_bore_radius','Removable stator mounting plate');body=self.patterned_circle(body,'pr_housing_back_x','pr_stator_plate_thickness','pr_retainer_lug_size','pr_retainer_lug_radius',20,3,'Three retaining-plate rim lands',True);collar=self.annulus('pr_housing_split_x','pr_bearing_rear_x-pr_housing_split_x','pr_bearing_od/2','pr_outer_open_radius','Removable rear outer-race stop');body=g.combine(body,[collar],fusion.FeatureOperations.JoinFeatureOperation,'Integral open locating collar');body=self.cut_hexagons(body,'pr_housing_back_x','pr_stator_plate_thickness','Three open retainer nut passages');return self.patterned_circle(body,'pr_housing_back_x-1 mm','pr_stator_plate_thickness+2 mm','ph_stator_hole_radius','pr_stator_pcd_radius',0,9,'Nine standard stator mounting holes')
