"""Native transverse frame tie with shared rail width and shoulder position."""
class FrameTieIntent(FrameRailIntent):
 def parameters(self):
  super().parameters();g=self.g
  values={'frame_tie_half_x':6,'frame_tie_bottom_z':34,'frame_tie_thickness':2,'frame_tie_rise':6.8,'frame_tie_head_envelope_diameter':5.8,'frame_tie_head_diametral_allowance':.2,'frame_tie_countersink_diameter':'frame_tie_head_envelope_diameter+frame_tie_head_diametral_allowance','frame_tie_top_z':'frame_tie_bottom_z+frame_tie_rise+frame_tie_thickness'}
  for name,value in values.items():g.parameter(name,value,comment='Transverse tie datum or frozen countersunk screw envelope. Supplier and physical fit qualification remain separate.')
 def base(self):
  self.parameters();g=self.g;c=self.c;plane=g.plane(c.yZConstructionPlane,'rail_crossmember_x-frame_tie_half_x','Transverse tie front datum');sk=c.sketches.add(plane);sk.name='One continuous formed tie section';sk.isComputeDeferred=True;ys=['-frame_half_y+1 mm','-frame_half_y+5 mm','-frame_half_y+12 mm','frame_half_y-12 mm','frame_half_y-5 mm','frame_half_y-1 mm','frame_half_y-1 mm','frame_half_y-5 mm','frame_half_y-12 mm','-frame_half_y+12 mm','-frame_half_y+5 mm','-frame_half_y+1 mm'];zs=['frame_tie_bottom_z','frame_tie_bottom_z','frame_tie_bottom_z+frame_tie_rise','frame_tie_bottom_z+frame_tie_rise','frame_tie_bottom_z','frame_tie_bottom_z','frame_tie_bottom_z+frame_tie_thickness','frame_tie_bottom_z+frame_tie_thickness','frame_tie_top_z','frame_tie_top_z','frame_tie_bottom_z+frame_tie_thickness','frame_tie_bottom_z+frame_tie_thickness'];coordinates=[('-('+z+')',y) for y,z in zip(ys,zs)];points=[g.skeleton_point(sk,*pair) for pair in coordinates];xseen={};yseen={}
  for point,(x,y) in zip(points,coordinates):
   g.point_dimensions(sk,point,None if x in xseen else x,None if y in yseen else y)
   if x in xseen:sk.geometricConstraints.addVerticalPoints(xseen[x],point)
   if y in yseen:sk.geometricConstraints.addHorizontalPoints(yseen[y],point)
   xseen[x]=point;yseen[y]=point
  for i,p in enumerate(points):sk.sketchCurves.sketchLines.addByTwoPoints(p,points[(i+1)%len(points)])
  sk.isComputeDeferred=False;assert sk.profiles.count==1;body=g.extrude(sk,'2*frame_tie_half_x','Continuous transverse frame tie').bodies.item(0)
  helper=SensorSaddleIntent(g);centers=[('rail_crossmember_x'+sign+'rail_crossmember_hole_half_spacing',side+'(frame_half_y-3 mm)') for sign in ['-','+'] for side in ['-','']];plane=g.plane(c.xYConstructionPlane,'frame_tie_bottom_z+frame_tie_thickness','Countersunk fastener seating datum');layout=c.sketches.add(plane);layout.name='Four shared rail-to-tie screw centers';points=[g.skeleton_point(layout,x,y) for x,y in centers];columns={}
  for point,(x,y) in zip(points,centers):
   g.point_dimensions(layout,point,None if x in columns else x,y)
   if x in columns:layout.geometricConstraints.addVerticalPoints(columns[x],point)
   else:columns[x]=point
  selected=core.ObjectCollection.create()
  for point in points:selected.add(point)
  holes=c.features.holeFeatures;inp=holes.createCountersinkInput(g.value('frame_m3_clearance'),g.value('frame_tie_countersink_diameter'),g.value('90 deg'));assert inp.setPositionBySketchPoints(selected);assert inp.setDistanceExtent(g.value('6 mm'));inp.participantBodies=[body];feature=holes.add(inp);feature.name='Four standard countersunk rail attachments';layout.isLightBulbOn=False;body=c.bRepBodies.item(0)
  sk=helper.circles('frame_tie_top_z-4.8 mm',[('rail_crossmember_x','-18 mm'),('rail_crossmember_x','18 mm')],'frame_m3_clearance/2','Existing end attachment holes');g.extrude_all(sk,'6 mm','Two retained end attachment holes',fusion.FeatureOperations.CutFeatureOperation,[body]);assert c.bRepBodies.count==1;return c.bRepBodies.item(0)
 def front_sensor_holes(self,body):
  g=self.g;helper=SensorSaddleIntent(g);sk=helper.circles('25 mm',[('saddle_x','-saddle_foot_spacing/2'),('saddle_x','saddle_foot_spacing/2')],'saddle_root_hole_radius','Shared M4 sensor saddle root pattern');g.extrude_all(sk,'25 mm','Two sensor saddle mounting clearances',fusion.FeatureOperations.CutFeatureOperation,[body]);return self.c.bRepBodies.item(0)
