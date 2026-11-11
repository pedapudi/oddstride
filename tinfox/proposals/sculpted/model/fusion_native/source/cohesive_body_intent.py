"""Native enclosure revision with one deliberate shoulder edge and open plan trim."""
class CohesiveBodyIntent(CompactCoverIntent):
 def parameters(self):
  super().parameters();g=self.g
  values={'cc_cover_mount_x':64,'cc_cover_mount_z':18,'cc_cover_plan_radius':52,'cc_belly_plan_width':174,'cc_belly_plan_depth':220,'cc_belly_plan_radius':14,'cc_cover_display_width':48.6,'cc_cover_display_depth':28.6,'cc_cover_display_radius':4,'cc_cover_button_radius':4.8,'cc_cover_process_hole_compensation':0,'cc_cover_hole_diameter':'frame_m3_nominal+robot_fastener_diametral_allowance+cc_cover_process_hole_compensation','cc_cover_edge_end_x':'cover_half_length+.6 mm','cc_cover_edge_outer_control_x':'cover_half_length-20.4 mm','cc_cover_edge_inner_control_x':'cover_half_length-29.4 mm','cc_cover_edge_high_z':'cover_roof_z-4.5 mm','cc_cover_edge_low_z':'cover_lower_edge_z'}
  for name,value in values.items():g.parameter(name,value,comment='Coherent enclosure revision. Functional shape and interface dimensions are independent of measured process compensation.')
 def cubic(self,sk,coordinates,name):
  g=self.g;points=[g.skeleton_point(sk,x,'-('+z+')') for x,z in coordinates]
  for p,(x,z) in zip(points,coordinates):g.point_dimensions(sk,p,x,'-('+z+')')
  spline=sk.sketchCurves.sketchControlPointSplines.add(points,fusion.SplineDegrees.SplineDegreeThree)
  for control,driver in zip(spline.controlPoints,points):
   if control.entityToken!=driver.entityToken:sk.geometricConstraints.addCoincident(control,driver)
  return points
 def edge_mask(self):
  g=self.g;c=self.c;plane=g.plane(c.xZConstructionPlane,'-150 mm','Shoulder edge through datum');sk=c.sketches.add(plane);sk.name='Two tangent cubic shoulders and continuous lower rim';left=self.cubic(sk,[('-cc_cover_edge_end_x','cc_cover_edge_high_z'),('-cc_cover_edge_outer_control_x','cc_cover_edge_high_z'),('-cc_cover_edge_inner_control_x','cc_cover_edge_low_z'),('-cc_cover_mount_x','cc_cover_edge_low_z')],'Left tangent shoulder');right=self.cubic(sk,[('cc_cover_mount_x','cc_cover_edge_low_z'),('cc_cover_edge_inner_control_x','cc_cover_edge_low_z'),('cc_cover_edge_outer_control_x','cc_cover_edge_high_z'),('cc_cover_edge_end_x','cc_cover_edge_high_z')],'Right tangent shoulder');top=[]
  for x in ['-cc_cover_edge_end_x','cc_cover_edge_end_x']:
   p=g.skeleton_point(sk,x,'-(cover_roof_z+30.5 mm)');g.point_dimensions(sk,p,x,'-(cover_roof_z+30.5 mm)');top.append(p)
  for a,b in [(top[0],left[0]),(left[-1],right[0]),(right[-1],top[1]),(top[1],top[0])]:sk.sketchCurves.sketchLines.addByTwoPoints(a,b)
  assert sk.profiles.count==1;return g.extrude(sk,'300 mm','Tangent shoulder opening envelope').bodies.item(0)
 def plan_mask(self,width,depth,radius,z,height,name):
  g=self.g;c=self.c;plane=g.plane(c.xYConstructionPlane,z,name+' datum');sk=g.rounded_rectangle(plane,width,depth,radius,'0 mm',name+' outline');return g.extrude(sk,height,name).bodies.item(0)
 def cover(self):
  self.parameters();g=self.g;c=self.c;plane=g.plane(c.yZConstructionPlane,'-cover_half_length','Central enclosure datum');sk=g.rounded_octagon(plane,'cover_half_width','cover_roof_z','cover_floor_z','cover_top_bevel','cover_bottom_bevel','cover_corner_radius','Constant central torso section');body=g.extrude(sk,'2*cover_half_length','Central enclosure envelope').bodies.item(0)
  plane=g.plane(c.yZConstructionPlane,'-cover_half_length-1 mm','Inner wall datum');sk=g.rounded_octagon(plane,'cover_half_width-cover_wall','cover_roof_z-cover_wall','cover_floor_z+cover_wall','cover_top_bevel+cover_wall*(sqrt(2)-2)','cover_bottom_bevel+cover_wall*(sqrt(2)-2)','cover_corner_radius-cover_wall','True offset central wall');g.extrude(sk,'2*cover_half_length+2 mm','Uniform enclosure wall',fusion.FeatureOperations.CutFeatureOperation,[body]);body=c.bRepBodies.item(0);body=g.combine(body,[self.edge_mask()],fusion.FeatureOperations.IntersectFeatureOperation,'One continuous shoulder lower edge');body=g.combine(body,[self.plan_mask('2*cover_half_length','2*cover_half_width','cc_cover_plan_radius','-40 mm','140 mm','Rounded body plan')],fusion.FeatureOperations.IntersectFeatureOperation,'Rounded ends without corner tabs')
  rib=self.box('2.4 mm','170 mm','5.5 mm','28 mm','0 mm','cover_roof_z-2.75 mm','Integral roof rib');body=self.join(body,[rib,self.reflected(rib,c.yZConstructionPlane,'Paired roof rib')],'Two continuous roof supports')
  plane=g.plane(c.xYConstructionPlane,'cover_roof_z-11.5 mm','Display opening datum');sk=g.rounded_rectangle(plane,'cc_cover_display_width','cc_cover_display_depth','cc_cover_display_radius','0 mm','Open display perimeter','20 mm');g.extrude(sk,'30 mm','Display aperture',fusion.FeatureOperations.CutFeatureOperation,[body]);body=c.bRepBodies.item(0);tool=self.cylinder('Z','cover_roof_z-7.5 mm','55 mm','-27 mm','cc_cover_button_radius','15 mm','Power button clearance');body=self.cut(body,[tool],'Accessible button opening')
  plane=g.plane(c.xYConstructionPlane,'-70 mm','Sensor removal opening datum');sk=g.rounded_rectangle(plane,'150 mm','92 mm','8 mm','0 mm','Shared sensor service opening','saddle_cover_service_x');g.extrude(sk,'200 mm','Open sensor installation path',fusion.FeatureOperations.CutFeatureOperation,[body]);body=c.bRepBodies.item(0)
  for start,radius,length,name in [('cover_hip_x-114.7 mm','41.25 mm','49.4 mm','Roll case relief'),('cover_hip_x-73.3 mm','42 mm','7 mm','Roll cartridge relief')]:
   tool=self.cylinder('X',start,'cover_roll_y','0 mm',radius,length,name);body=self.cut(body,self.four(tool,name),'Four outward-open '+name.lower()+'s')
  tool=self.cylinder('Y','cover_roll_y+37 mm','cc_cover_mount_x','cc_cover_mount_z','cc_cover_hole_diameter/2','10 mm','Lateral cover screw');body=self.cut(body,self.four(tool,'Cover screw'),'Four direct cover-to-frame clearances');assert c.bRepBodies.count==1;return body
 def trim_belly(self,body):
  self.parameters();tool=self.plan_mask('cc_belly_plan_width','cc_belly_plan_depth','cc_belly_plan_radius','-110 mm','150 mm','Short rounded battery wrap');return self.g.combine(body,[tool],fusion.FeatureOperations.IntersectFeatureOperation,'Remove obsolete lower motor crescents')
