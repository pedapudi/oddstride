"""Lower shell from one section, a stepped clearance and two access profiles.

Local replay proves that the omitted ear, rail and upper connector tools never
intersect this part. Shared body datums drive the shell; hardware envelopes and
process clearances remain independent dimensions.
"""
class CompactLowerShellIntent(CompactCoverIntent):
 def parameters(self):
  super().parameters();g=self.g
  for name,value in {'body_shell_seam_gap':.3,'belly_top_z':-10.3,'belly_battery_aperture_width':148,'belly_battery_aperture_depth':202,'belly_battery_corner_radius':8,'belly_battery_cut_top_z':-20,'body_roll_case_radius':39.25,'body_roll_case_radial_clearance':2,'body_roll_cartridge_relief_radius':42,'body_roll_end_relief_radius':38,'body_roll_output_setback':67.3,'body_roll_port_axial_datum':-37.6,'body_roll_port_radial_datum':35.6,'body_roll_connector_width':18,'body_roll_connector_depth':21,'body_roll_connector_axial_clearance':12,'body_roll_connector_start':-5.5}.items():g.parameter(name,value,comment='Body interface or selected RS02 connector envelope; physical fit and supplier geometry remain unqualified.')
  g.parameter('body_roll_connector_clock',40,'deg',comment='Selected fixed roll-motor port clock datum')
  g.parameter('body_roll_port_angle','body_roll_connector_clock-3.8 deg','deg',comment='Connector envelope rotation from the vendor drawing datum')
  g.design.userParameters.itemByName('belly_top_z').expression='cover_lower_edge_z-body_shell_seam_gap'
 def lower_connector(self):
  g=self.g;c=self.c;angle='body_roll_port_angle';radial='body_roll_port_radial_datum+body_roll_connector_start+body_roll_connector_depth/2';cx='('+radial+')*cos('+angle+')';cy='cover_roll_y+('+radial+')*sin('+angle+')';plane=g.plane(c.yZConstructionPlane,'cover_hip_x-body_roll_output_setback+body_roll_port_axial_datum-body_roll_connector_axial_clearance/2','Lower connector axial datum');sk=c.sketches.add(plane);sk.name='Lower connector clearance section';points=[]
  for radial_sign,tangent_sign in [(-1,-1),(1,-1),(1,1),(-1,1)]:
   x=cx+' + '+str(radial_sign)+'*body_roll_connector_depth/2*cos('+angle+') - '+str(tangent_sign)+'*body_roll_connector_width/2*sin('+angle+')';y=cy+' + '+str(radial_sign)+'*body_roll_connector_depth/2*sin('+angle+') + '+str(tangent_sign)+'*body_roll_connector_width/2*cos('+angle+')';p=g.skeleton_point(sk,x,y);g.point_dimensions(sk,p,x,y);points.append(p)
  for i,p in enumerate(points):sk.sketchCurves.sketchLines.addByTwoPoints(p,points[(i+1)%4])
  assert sk.profiles.count==1;return g.extrude(sk,'body_roll_connector_axial_clearance','Lower fixed-motor connector envelope').bodies.item(0)
 def build(self):
  self.parameters();g=self.g;c=self.c;plane=g.plane(c.yZConstructionPlane,'-cover_half_length','Lower shell end datum');outer=g.rounded_octagon(plane,'cover_half_width','cover_roof_z','cover_floor_z','cover_top_bevel','cover_bottom_bevel','cover_corner_radius','Shared transverse body section');body=g.extrude(outer,'2*cover_half_length','Lower shell envelope').bodies.item(0)
  plane=g.plane(c.yZConstructionPlane,'-cover_half_length-1 mm','Lower inner wall datum');inner=g.rounded_octagon(plane,'cover_half_width-cover_wall','cover_roof_z-cover_wall','cover_floor_z+cover_wall','cover_top_bevel+cover_wall*(sqrt(2)-2)','cover_bottom_bevel+cover_wall*(sqrt(2)-2)','cover_corner_radius-cover_wall','Shared normal-offset body wall');g.extrude(inner,'2*cover_half_length+2 mm','Uniform lower shell wall',fusion.FeatureOperations.CutFeatureOperation,[body]);body=c.bRepBodies.item(0)
  tool=self.box('2*cover_half_length+10 mm','2*cover_half_width+10 mm','100 mm','0 mm','0 mm','belly_top_z+50 mm','Upper split opening tool');body=self.cut(body,[tool],'Open structural shell at shared seam')
  radius='body_roll_case_radius+body_roll_case_radial_clearance';stations=[('cover_hip_x-114.7 mm','0 mm'),('cover_hip_x-114.7 mm',radius),('cover_hip_x-73.3 mm',radius),('cover_hip_x-73.3 mm','body_roll_cartridge_relief_radius'),('cover_hip_x-66.3 mm','body_roll_cartridge_relief_radius'),('cover_hip_x-66.3 mm',radius),('cover_hip_x-65.3 mm',radius),('cover_hip_x-65.3 mm','body_roll_end_relief_radius'),('cover_hip_x-51.5 mm','body_roll_end_relief_radius'),('cover_hip_x-51.5 mm','0 mm')];tool=self.turned_x(stations,'cover_roll_y','360 deg','Stepped fixed-motor clearance');body=self.cut(body,self.four(tool,'Lower motor relief'),'Four fixed-motor clearances')
  plane=g.plane(c.xYConstructionPlane,'belly_battery_cut_top_z-80 mm','Battery removal aperture datum');sk=g.rounded_rectangle(plane,'belly_battery_aperture_width','belly_battery_aperture_depth','belly_battery_corner_radius','0 mm','Rounded battery removal aperture');g.extrude(sk,'80 mm','Open battery removal path',fusion.FeatureOperations.CutFeatureOperation,[body]);body=c.bRepBodies.item(0);tool=self.lower_connector();body=self.cut(body,self.four(tool,'Lower connector relief'),'Four lower connector clearances');assert c.bRepBodies.count==1;return c.bRepBodies.item(0)
