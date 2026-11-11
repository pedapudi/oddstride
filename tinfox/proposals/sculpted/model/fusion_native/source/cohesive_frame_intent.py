"""Native open rail joints and transverse ties with integral tapped pads."""
class CohesiveFrameIntent(FrameTieIntent):
 def parameters(self):
  super().parameters();g=self.g
  values={'cc_cover_mount_x':64,'cc_cover_mount_z':18,'cc_tie_pad_x':'rail_crossmember_x-6 mm','cc_tie_hole_y':'frame_half_y+2 mm','cc_tie_foot_y':'frame_half_y+1.5 mm','cc_tie_foot_width':18,'cc_tie_foot_depth':12,'cc_tie_foot_radius':1,'cc_tie_pad_width':16,'cc_tie_pad_depth':9,'cc_tie_pad_thickness':8,'cc_sensor_pad_radius':5,'cc_sensor_pad_thickness':6.8,'cc_sensor_tap_nominal':3.3,'cc_sensor_tap_compensation':0,'cc_sensor_tap_diameter':'cc_sensor_tap_nominal+cc_sensor_tap_compensation'}
  for name,value in values.items():g.parameter(name,value,comment='Coherent chassis interface datum or nominal tap-drill size. Taps, threads and stock dimensions require a manufacturing plan.')
 def counterbore_grid(self,body,centers,diameter,counter_diameter,counter_depth,top_z,depth,name):
  g=self.g;c=self.c;plane=g.plane(c.xYConstructionPlane,top_z,name+' datum');sk=c.sketches.add(plane);sk.name=name+' positions';points=[g.skeleton_point(sk,x,y) for x,y in centers];xs={};ys={}
  for p,(x,y) in zip(points,centers):
   g.point_dimensions(sk,p,None if x in xs else x,None if y in ys else y)
   if x in xs:sk.geometricConstraints.addVerticalPoints(xs[x],p)
   if y in ys:sk.geometricConstraints.addHorizontalPoints(ys[y],p)
   xs[x]=p;ys[y]=p
  chosen=core.ObjectCollection.create()
  for p in points:chosen.add(p)
  holes=c.features.holeFeatures;inp=holes.createCounterboreInput(g.value(diameter),g.value(counter_diameter),g.value(counter_depth));assert inp.setPositionBySketchPoints(chosen);assert inp.setDistanceExtent(g.value(depth));inp.participantBodies=[body];f=holes.add(inp);f.name=name;sk.isLightBulbOn=False;assert c.bRepBodies.count==1;return c.bRepBodies.item(0)
 def tie_base(self):
  self.parameters();g=self.g;c=self.c;plane=g.plane(c.yZConstructionPlane,'rail_crossmember_x-frame_tie_half_x','Transverse tie end datum');sk=c.sketches.add(plane);sk.name='Continuous folded bridge without retired feet';ys=['-frame_half_y+4 mm','-frame_half_y+12 mm','frame_half_y-12 mm','frame_half_y-4 mm','frame_half_y-4 mm','frame_half_y-12 mm','-frame_half_y+12 mm','-frame_half_y+4 mm'];zs=['frame_tie_bottom_z','frame_tie_bottom_z+frame_tie_rise','frame_tie_bottom_z+frame_tie_rise','frame_tie_bottom_z','frame_tie_bottom_z+frame_tie_thickness','frame_tie_top_z','frame_tie_top_z','frame_tie_bottom_z+frame_tie_thickness'];coordinates=[('-('+z+')',y) for y,z in zip(ys,zs)];points=[g.skeleton_point(sk,*pair) for pair in coordinates];xs={};ys0={}
  for p,(x,y) in zip(points,coordinates):
   g.point_dimensions(sk,p,None if x in xs else x,None if y in ys0 else y)
   if x in xs:sk.geometricConstraints.addVerticalPoints(xs[x],p)
   if y in ys0:sk.geometricConstraints.addHorizontalPoints(ys0[y],p)
   xs[x]=p;ys0[y]=p
  for i,p in enumerate(points):sk.sketchCurves.sketchLines.addByTwoPoints(p,points[(i+1)%len(points)])
  assert sk.profiles.count==1;body=g.extrude(sk,'2*frame_tie_half_x','One formed transverse bridge').bodies.item(0);plane=g.plane(c.xYConstructionPlane,'frame_tie_bottom_z','Tie foot seating datum');sk=g.rounded_rectangle(plane,'cc_tie_foot_width','cc_tie_foot_depth','cc_tie_foot_radius','cc_tie_foot_y','Open rounded tie foot','cc_tie_pad_x');foot=g.extrude(sk,'frame_tie_thickness','Integral rounded tie foot').bodies.item(0);body=self.join(body,[foot,self.reflected(foot,c.xZConstructionPlane,'Opposite tie foot')],'Bridge with two integral feet')
  centers=[('cc_tie_pad_x'+sign+'rail_crossmember_hole_half_spacing',side+'cc_tie_hole_y') for sign in ['-','+'] for side in ['-','']];plane=g.plane(c.xYConstructionPlane,'frame_tie_bottom_z+frame_tie_thickness','Countersunk seating datum');layout=c.sketches.add(plane);layout.name='Four tapped-pad attachment centers';points=[g.skeleton_point(layout,x,y) for x,y in centers];columns={}
  for p,(x,y) in zip(points,centers):
   g.point_dimensions(layout,p,None if x in columns else x,y)
   if x in columns:layout.geometricConstraints.addVerticalPoints(columns[x],p)
   else:columns[x]=p
  selected=core.ObjectCollection.create()
  for p in points:selected.add(p)
  inp=c.features.holeFeatures.createCountersinkInput(g.value('frame_m3_clearance'),g.value('frame_tie_countersink_diameter'),g.value('90 deg'));assert inp.setPositionBySketchPoints(selected);assert inp.setDistanceExtent(g.value('6 mm'));inp.participantBodies=[body];c.features.holeFeatures.add(inp).name='Four standard countersunk pad attachments';layout.isLightBulbOn=False;body=c.bRepBodies.item(0)
  helper=SensorSaddleIntent(g);sk=helper.circles('frame_tie_top_z-4.8 mm',[('rail_crossmember_x','-18 mm'),('rail_crossmember_x','18 mm')],'frame_m3_clearance/2','Retained open end attachments');g.extrude_all(sk,'6 mm','Two retained end attachments',fusion.FeatureOperations.CutFeatureOperation,[body]);return c.bRepBodies.item(0)
 def front_sensor_pads(self,body):
  g=self.g;helper=SensorSaddleIntent(g);centers=[('saddle_x','-saddle_foot_spacing/2'),('saddle_x','saddle_foot_spacing/2')];sk=helper.circles('frame_tie_bottom_z',centers,'cc_sensor_pad_radius','Integral sensor support pads');f=g.extrude_all(sk,'cc_sensor_pad_thickness','M4 thread engagement pads');body=self.join(body,list(f.bodies),'Two integral sensor pads');return self.counterbore_grid(body,centers,'cc_sensor_tap_diameter','2*saddle_root_hole_radius','4 mm','frame_tie_top_z+2 mm','12 mm','M4 pilot bores with bridge clearance')
 def rail(self):
  self.parameters();g=self.g;c=self.c;body=FrameRailIntent.build(self,legacy_mounts=False)
  boss=self.box('12 mm','5 mm','12 mm','cc_cover_mount_x','frame_half_y+3.5 mm','cc_cover_mount_z','Open cover mounting boss','1.5 mm');body=self.join(body,[boss,self.reflected(boss,c.yZConstructionPlane,'Rear cover mounting boss')],'Two broad lateral cover mounts')
  plane=g.plane(c.yZConstructionPlane,'cc_cover_mount_x-4 mm','Cover gusset datum');sk=c.sketches.add(plane);sk.name='Broad triangular cover gusset';coordinates=[('-cc_cover_mount_z','frame_half_y'),('-(cc_cover_mount_z+4 mm)','frame_half_y+6 mm'),('-(cc_cover_mount_z+14 mm)','frame_half_y')];points=[g.skeleton_point(sk,*pair) for pair in coordinates]
  g.point_dimensions(sk,points[0],coordinates[0][0],coordinates[0][1]);g.point_dimensions(sk,points[1],coordinates[1][0],coordinates[1][1]);g.point_dimensions(sk,points[2],coordinates[2][0],None);sk.geometricConstraints.addHorizontalPoints(points[0],points[2])
  for i,p in enumerate(points):sk.sketchCurves.sketchLines.addByTwoPoints(p,points[(i+1)%3])
  assert sk.profiles.count==1;gusset=g.extrude(sk,'8 mm','Integral cover-boss gusset').bodies.item(0);body=self.join(body,[gusset,self.reflected(gusset,c.yZConstructionPlane,'Rear cover-boss gusset')],'Gusseted wall attachments')
  plane=g.plane(c.xZConstructionPlane,'frame_half_y-2 mm','Cover pilot entry datum');sk=self.circles_line(plane,['cc_cover_mount_x','-cc_cover_mount_x'],'-cc_cover_mount_z','frame_m3_tap_drill','M3 tapped cover mounting pilots');g.extrude_all(sk,'10 mm','Two M3 cover tap pilots',fusion.FeatureOperations.CutFeatureOperation,[body]);body=c.bRepBodies.item(0)
  pad=self.box('cc_tie_pad_width','cc_tie_pad_depth','cc_tie_pad_thickness','cc_tie_pad_x','cc_tie_hole_y','frame_tie_bottom_z-cc_tie_pad_thickness/2','Integral transverse tie pad','1 mm');body=self.join(body,[pad,self.reflected(pad,c.yZConstructionPlane,'Rear transverse tie pad')],'Two integral aluminum thread pads')
  plane=g.plane(c.xYConstructionPlane,'frame_tie_bottom_z-cc_tie_pad_thickness-1 mm','Tie tap entry datum');xs=['cc_tie_pad_x-rail_crossmember_hole_half_spacing','cc_tie_pad_x+rail_crossmember_hole_half_spacing','-cc_tie_pad_x+rail_crossmember_hole_half_spacing','-cc_tie_pad_x-rail_crossmember_hole_half_spacing'];sk=self.circles_line(plane,xs,'cc_tie_hole_y','frame_m3_tap_drill','Four M3 transverse tie pilots');g.extrude_all(sk,'cc_tie_pad_thickness+2 mm','Four replaceable standard screw attachments',fusion.FeatureOperations.CutFeatureOperation,[body]);assert c.bRepBodies.count==1;return self.final_rail_interfaces(c.bRepBodies.item(0))
 def final_rail_interfaces(self,body):
  objects=core.ObjectCollection.create()
  for key in ['chassis_crossmember_121','chassis_crossmember_-121']:
   candidate=next((c for c in self.g.design.allComponents if c.partNumber=='CANDIDATE_cc_'+key),None);source=candidate or next(c for c in self.g.design.allComponents if c.partNumber==key);assert source.bRepBodies.count==1;objects.add(source.bRepBodies.item(0))
  copied=self.c.features.copyPasteBodies.add(objects);copied.name='Shared native transverse tie seating datums';assert copied.isParametric;return self.cut(body,list(copied.bodies),'Open seating faces for the transverse ties')
