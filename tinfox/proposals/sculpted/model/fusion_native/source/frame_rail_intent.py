"""A native motor rail with shared shoulder, cover and deck mounting datums."""
class FrameRailIntent(FrameDeckIntent):
 def parameters(self):
  super().parameters();g=self.g
  settings={'rail_half_length':'robot_hip_x-55 mm','rail_skin_thickness':2,'rail_height':54,'rail_center_z':8,'rail_edge_radius':.7,'rail_window_x':'robot_hip_x-94 mm','rail_cartridge_bolt_x':'robot_hip_x-59.5 mm','rail_cartridge_bolt_half_z':18,'rail_cartridge_bolt_center_z':6,'rail_cartridge_pad_radius':5.5,'rail_cover_boss_x':'cover_boss_x','rail_crossmember_x':'robot_hip_x-64 mm','rail_crossmember_hole_half_spacing':3,'rail_motor_case_radius':39.25,'rail_motor_radial_allowance':1.5,'rail_enclosure_clearance':3.4}
  for name,value in settings.items():g.parameter(name,value,comment='Frame rail design datum or independent hardware clearance; baseline dimensions reproduce the frozen metal frame.')
 def circles_line(self,plane,coordinates,y,diameter,name):
  g=self.g;c=self.c;sk=c.sketches.add(plane);sk.name=name;points=[g.skeleton_point(sk,x,y) for x in coordinates];g.point_dimensions(sk,points[0],coordinates[0],y)
  for i,p in enumerate(points[1:],1):g.point_dimensions(sk,p,coordinates[i],None);sk.geometricConstraints.addHorizontalPoints(points[0],p)
  circles=[]
  for p in points:
   circle=sk.sketchCurves.sketchCircles.addByCenterRadius(p.geometry,g.mm(diameter)/20);sk.geometricConstraints.addCoincident(circle.centerSketchPoint,p)
   if circles:sk.geometricConstraints.addEqual(circles[0],circle)
   else:sk.sketchDimensions.addDiameterDimension(circle,core.Point3D.create(p.geometry.x+.4,p.geometry.y+.4,0)).parameter.expression=diameter
   circles.append(circle)
  assert sk.profiles.count==len(coordinates);return sk
 def pad_grid(self,plane,diameter,name):
  g=self.g;c=self.c;sk=c.sketches.add(plane);sk.name=name;x='rail_cartridge_bolt_x';z='rail_cartridge_bolt_half_z';center='-rail_cartridge_bolt_center_z';top=center+'+'+z;bottom=center+'-'+z;coordinates=[(x,top),('-'+x,top),('-'+x,bottom),(x,bottom)];points=[g.skeleton_point(sk,*pair) for pair in coordinates];g.point_dimensions(sk,points[0],x,top);g.point_dimensions(sk,points[1],'-'+x,None);sk.geometricConstraints.addHorizontalPoints(points[0],points[1]);g.point_dimensions(sk,points[2],None,bottom);sk.geometricConstraints.addVerticalPoints(points[1],points[2]);sk.geometricConstraints.addHorizontalPoints(points[2],points[3]);sk.geometricConstraints.addVerticalPoints(points[0],points[3]);circles=[]
  for p in points:
   circle=sk.sketchCurves.sketchCircles.addByCenterRadius(p.geometry,g.mm(diameter)/20);sk.geometricConstraints.addCoincident(circle.centerSketchPoint,p)
   if circles:sk.geometricConstraints.addEqual(circles[0],circle)
   else:sk.sketchDimensions.addDiameterDimension(circle,core.Point3D.create(p.geometry.x+.4,p.geometry.y+.4,0)).parameter.expression=diameter
   circles.append(circle)
  assert sk.profiles.count==4;return sk
 def y_window(self,body,x,z,width,height,radius,label,pair=False):
  g=self.g;c=self.c;plane=g.plane(c.xZConstructionPlane,'frame_half_y-3 mm',label+' through datum');sk=g.rounded_rectangle(plane,width,height,radius,'-('+z+')',label+' section',x);tool=g.extrude(sk,'6 mm',label+' tool').bodies.item(0);tools=[tool]
  if pair:tools.append(self.reflected(tool,c.yZConstructionPlane,label+' rear match'))
  return self.cut(body,tools,label)
 def build(self,legacy_mounts=True):
  self.parameters();g=self.g;c=self.c;body=self.box('2*rail_half_length','rail_skin_thickness','rail_height','0 mm','frame_half_y','rail_center_z','Continuous rail web','rail_edge_radius');body=self.y_window(body,'rail_window_x','0 mm','56 mm','52 mm','4 mm','Front and rear weight openings',True);body=self.y_window(body,'0 mm','5 mm','80 mm','28 mm','6 mm','Central weight opening')
  flange=self.box('2*rail_half_length','8 mm','2 mm','0 mm','frame_half_y-3 mm','33 mm','Rail top return','.5 mm');tool=self.box('138 mm','20 mm','6 mm','0 mm','frame_half_y-3 mm','33 mm','Open electronics return');tools=core.ObjectCollection.create();tools.add(tool);cut_input=c.features.combineFeatures.createInput(flange,tools);cut_input.operation=fusion.FeatureOperations.CutFeatureOperation;cut=c.features.combineFeatures.add(cut_input);cut.name='Open electronics clearance between the end returns';flanges=list(cut.bodies);assert len(flanges)==2;middle=self.box('138 mm','6 mm','2 mm','0 mm','frame_half_y+3 mm','33 mm','Outer center return','.5 mm');body=self.join(body,flanges+[middle],'Continuous stiffening flange')
  plane=g.plane(c.xZConstructionPlane,'frame_half_y-1 mm','Cartridge reinforcement datum');sk=self.pad_grid(plane,'2*rail_cartridge_pad_radius','Four cartridge mounting pads');f=g.extrude_all(sk,'5 mm','Integral cartridge pads');pads=list(f.bodies);assert len(pads)==4;body=self.join(body,pads,'Reinforced roll-cartridge supports')
  plane=g.plane(c.xZConstructionPlane,'frame_half_y-3 mm','Cartridge bolt entry datum');sk=self.pad_grid(plane,'frame_m3_clearance','Common cartridge bolt clearance');g.extrude_all(sk,'9 mm','Four cartridge attachment bores',fusion.FeatureOperations.CutFeatureOperation,[body]);body=c.bRepBodies.item(0)
  if legacy_mounts:
   boss=self.box('9 mm','5 mm','9 mm','rail_cover_boss_x','frame_half_y+1.5 mm','22 mm','Front body-cover mount','.5 mm');body=self.join(body,[boss,self.reflected(boss,c.yZConstructionPlane,'Rear body-cover mount')],'Body-cover mounting bosses')
  for xs,z,diameter,label,start,depth in [entry for entry in [(['rail_cover_boss_x','-rail_cover_boss_x'],'22 mm','frame_m3_tap_drill','Tapped body-cover mounts','frame_half_y-2 mm','9 mm'),(['frame_deck_mount_x','-frame_deck_mount_x'],'-6 mm','frame_m3_clearance','Battery cassette attachments','frame_half_y-3 mm','8 mm')] if legacy_mounts or entry[3]!='Tapped body-cover mounts']:
   plane=g.plane(c.xZConstructionPlane,start,label+' datum');sk=self.circles_line(plane,xs,'-('+z+')',diameter,label);g.extrude_all(sk,depth,label,fusion.FeatureOperations.CutFeatureOperation,[body]);body=c.bRepBodies.item(0)
  if legacy_mounts:
   plane=g.plane(c.xYConstructionPlane,'29 mm','Crossmember bolt entry datum');xs=['rail_crossmember_x-rail_crossmember_hole_half_spacing','rail_crossmember_x+rail_crossmember_hole_half_spacing','-rail_crossmember_x+rail_crossmember_hole_half_spacing','-rail_crossmember_x-rail_crossmember_hole_half_spacing'];sk=self.circles_line(plane,xs,'frame_half_y-3 mm','frame_m3_clearance','Paired transverse tie attachment pattern');g.extrude_all(sk,'8 mm','Four transverse tie holes',fusion.FeatureOperations.CutFeatureOperation,[body]);body=c.bRepBodies.item(0)
  tool=self.cylinder('X','robot_hip_x-114.7 mm','robot_roll_y','0 mm','rail_motor_case_radius+rail_motor_radial_allowance','49.4 mm','Fixed roll motor clearance');body=self.cut(body,[tool,self.reflected(tool,c.yZConstructionPlane,'Rear fixed roll motor clearance')],'Two fixed roll-motor envelopes')
  ledge=self.box('12 mm','10 mm','4 mm','frame_rail_mount_x','frame_half_y-4 mm','-1.5 mm','Front lower diaphragm support','.4 mm');tool=self.box('13 mm','11.3 mm','17 mm','frame_deck_mount_x','frame_half_y-7.85 mm','-8 mm','Cassette bracket clearance');ledge=self.cut(ledge,[tool],'Open cassette insertion beside diaphragm');body=self.join(body,[ledge,self.reflected(ledge,c.yZConstructionPlane,'Rear lower diaphragm support')],'Integral lower diaphragm supports')
  plane=g.plane(c.xYConstructionPlane,'-4 mm','Diaphragm screw datum');sk=self.circles_line(plane,['frame_rail_mount_x','-frame_rail_mount_x'],'frame_rail_mount_y','frame_m3_tap_drill','Shared diaphragm attachment pattern');g.extrude_all(sk,'7 mm','Tapped diaphragm mounts',fusion.FeatureOperations.CutFeatureOperation,[body]);body=c.bRepBodies.item(0)
  inset='rail_enclosure_clearance';plane=g.plane(c.yZConstructionPlane,'-robot_hip_x','Common body clearance datum');sk=g.rounded_octagon(plane,'cover_half_width-'+inset,'cover_roof_z-'+inset,'cover_floor_z+'+inset,'cover_top_bevel+'+inset+'*(sqrt(2)-2)','cover_bottom_bevel+'+inset+'*(sqrt(2)-2)','cover_corner_radius-'+inset,'Normal-offset chassis envelope');tool=g.extrude(sk,'2*robot_hip_x','Shared body clearance envelope').bodies.item(0);body=g.combine(body,[tool],fusion.FeatureOperations.IntersectFeatureOperation,'Fit rail inside the structural enclosure');assert c.bRepBodies.count==1;return body
