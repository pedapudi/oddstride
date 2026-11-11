"""A coupling, a single radial arm and two bridged fork ears."""
class CohesiveCrankIntent(CohesiveLimbIntent):
 def parameters(self):
  g=self.g
  dims={'lc_drive_coupling_radius':18,'lc_drive_coupling_bore':5,'lc_drive_face_y':54.4,'lc_drive_coupling_depth':7.4,'lc_drive_plate_y':61,'lc_drive_plate_thickness':4.8,'lc_drive_plate_half_height':8,'lc_drive_near_ear_y':55.8,'lc_drive_near_ear_depth':10,'lc_drive_fork_gap':8.4,'lc_drive_far_ear_depth':11.8,'lc_drive_bridge_width':14,'lc_drive_bridge_height':4.8,'lc_drive_bridge_y':59.8,'lc_drive_bridge_depth':22.2,'lc_drive_bridge_z':-10.3,'lc_drive_bridge_radius':.7,'lc_drive_pad_height':5.2,'lc_drive_pad_z':-7.7,'lc_drive_pad_radius':.8,'lc_drive_near_pad_depth':6,'lc_drive_far_pad_depth':7.8,'lc_rs02_output_pcd_radius':12,'lc_rs02_output_hole_radius':2.2,'lc_rs02_output_head_radius':4}
  for name,value in dims.items():g.parameter(name,value,comment='Explicit coupling, fork or RS02 output-interface dimension; not uniformly scaled')
  g.parameter('lc_drive_far_ear_y','lc_drive_near_ear_y+lc_drive_near_ear_depth+lc_drive_fork_gap');g.parameter('lc_drive_bridge_center_x','lc_crank_radius-1 mm');g.parameter('lc_rs02_output_bolt_count',6,'')
 def rounded_box(self,cx,cz,width,height,y,depth,radius,name):
  g=self.g;plane=g.plane(self.c.xZConstructionPlane,y,name+' datum');sk=self.c.sketches.add(plane);sk.name=name+' section';sk.isComputeDeferred=True;left='('+cx+')-('+width+')/2';right='('+cx+')+('+width+')/2';top='-(('+cz+')+('+height+')/2)';bottom='-(('+cz+')-('+height+')/2)';expressions=[(left,top),(right,top),(right,bottom),(left,bottom)];points=[];xs={};ys={}
  for x,z in expressions:
   p=g.skeleton_point(sk,x,z);g.point_dimensions(sk,p,None if x in xs else x,None if z in ys else z)
   if x in xs:sk.geometricConstraints.addVerticalPoints(xs[x],p)
   if z in ys:sk.geometricConstraints.addHorizontalPoints(ys[z],p)
   xs[x]=p;ys[z]=p;points.append(p)
  for i,p in enumerate(points):sk.sketchCurves.sketchLines.addByTwoPoints(p,points[(i+1)%4])
  sk.isComputeDeferred=False;body=g.extrude(sk,depth,name).bodies.item(0);edges=core.ObjectCollection.create()
  for edge in body.edges:edges.add(edge)
  inp=self.c.features.filletFeatures.createInput();inp.edgeSetInputs.addConstantRadiusEdgeSet(edges,g.value(radius),False);f=self.c.features.filletFeatures.add(inp);f.name=name+' edge radii';return f.bodies.item(0)
 def blank(self):
  g=self.g;c=self.c;self.parameters();sk=self.circles('lc_drive_face_y',[('0 mm','0 mm','lc_drive_coupling_radius'),('0 mm','0 mm','lc_drive_coupling_bore')],'Motor output coupling');profile=next(p for p in sk.profiles if p.profileLoops.count==2);inp=c.features.extrudeFeatures.createInput(profile,fusion.FeatureOperations.NewBodyFeatureOperation);inp.setDistanceExtent(False,g.value('lc_drive_coupling_depth'));f=c.features.extrudeFeatures.add(inp);f.name='Annular motor coupling';body=f.bodies.item(0);sk.isLightBulbOn=False
  plane=g.plane(c.xZConstructionPlane,'lc_drive_plate_y','Radial arm datum');sk=c.sketches.add(plane);sk.name='Radial arm with round end';center=g.skeleton_point(sk,'lc_crank_radius','0 mm');g.point_dimensions(sk,center,'lc_crank_radius','0 mm');arc,top,bottom=g.driven_arc(sk,center,'lc_drive_plate_half_height','-90 deg','90 deg','Rounded arm end');left_top=g.skeleton_point(sk,'0 mm','-lc_drive_plate_half_height');left_bottom=g.skeleton_point(sk,'0 mm','lc_drive_plate_half_height');g.point_dimensions(sk,left_top,'0 mm','-lc_drive_plate_half_height');g.point_dimensions(sk,left_bottom,'0 mm','lc_drive_plate_half_height');sk.sketchCurves.sketchLines.addByTwoPoints(top,left_top);sk.sketchCurves.sketchLines.addByTwoPoints(left_top,left_bottom);sk.sketchCurves.sketchLines.addByTwoPoints(left_bottom,bottom);assert sk.profiles.count==1;body=g.extrude(sk,'lc_drive_plate_thickness','Single radial drive arm',fusion.FeatureOperations.JoinFeatureOperation,[body]).bodies.item(0)
  sk=self.circles('lc_drive_near_ear_y',[('lc_crank_radius','0 mm','lc_pin_eye_radius')],'Near fork ear');body=self.extrude_all(sk,'lc_drive_near_ear_depth','Near fork ear',fusion.FeatureOperations.JoinFeatureOperation,body)
  sk=self.circles('lc_drive_far_ear_y',[('lc_crank_radius','0 mm','lc_pin_eye_radius')],'Far fork ear');far=self.extrude_all(sk,'lc_drive_far_ear_depth','Far fork ear',fusion.FeatureOperations.NewBodyFeatureOperation)
  tools=[far,self.rounded_box('lc_drive_bridge_center_x','lc_drive_bridge_z','lc_drive_bridge_width','lc_drive_bridge_height','lc_drive_bridge_y','lc_drive_bridge_depth','lc_drive_bridge_radius','Fork bridge')]
  for name,y,depth in [('Near bridge root','lc_drive_bridge_y','lc_drive_near_pad_depth'),('Far bridge root','lc_drive_far_ear_y','lc_drive_far_pad_depth')]:tools.append(self.rounded_box('lc_drive_bridge_center_x','lc_drive_pad_z','lc_drive_bridge_width','lc_drive_pad_height',y,depth,'lc_drive_pad_radius',name))
  body=g.combine(body,tools,fusion.FeatureOperations.JoinFeatureOperation,'Integral bridged fork');assert c.bRepBodies.count==1;return body
 def interfaces(self,body,open_heads=False):
  g=self.g;c=self.c
  if open_heads:g.parameter('mc_head_access_overrun','4 mm',comment='Open mounting screw approach beyond the far fork; seating plane is unchanged.')
  head_depth='lc_drive_far_ear_y+lc_drive_far_ear_depth+mc_head_access_overrun-lc_drive_plate_y'if open_heads else'4 mm'
  for name,y,depth,radius in [('Motor mounting bores','54 mm','12 mm','lc_rs02_output_hole_radius'),('Motor screw head pockets','61 mm',head_depth,'lc_rs02_output_head_radius')]:
   sk=self.circles(y,[('lc_rs02_output_pcd_radius','0 mm',radius)],name+' seed');body=self.extrude_all(sk,depth,name+' seed',fusion.FeatureOperations.CutFeatureOperation,body);seed=c.features.extrudeFeatures.item(c.features.extrudeFeatures.count-1);objects=core.ObjectCollection.create();objects.add(seed);inp=c.features.circularPatternFeatures.createInput(objects,c.yConstructionAxis);inp.quantity=g.value('lc_rs02_output_bolt_count');inp.totalAngle=g.value('360 deg');inp.patternComputeOption=fusion.PatternComputeOptions.AdjustPatternCompute;f=c.features.circularPatternFeatures.add(inp);f.name=name+' circular pattern';body=c.bRepBodies.item(0)
  for y,depth,radius,name in [('54 mm','6 mm','lc_pin_head_clearance','Shoulder screw head'),('60 mm','20 mm','lc_pin_shoulder_clearance','Six millimeter shoulder journal')]:
   sk=self.circles(y,[('lc_crank_radius','0 mm',radius)],name);body=self.extrude_all(sk,depth,name,fusion.FeatureOperations.CutFeatureOperation,body)
  sk=self.hexagons('80 mm',[('lc_crank_radius','0 mm','lc_pin_nut_af')],'Captured M5 shoulder screw nut');body=self.extrude_all(sk,'12 mm','Captured M5 nut pocket',fusion.FeatureOperations.CutFeatureOperation,body)
  # Rod-flange clearance lies wholly in the open fork gap; the M5 hex already
  # clears the screw tip. Omitting these empty cuts preserves a healthy history.
  return body
