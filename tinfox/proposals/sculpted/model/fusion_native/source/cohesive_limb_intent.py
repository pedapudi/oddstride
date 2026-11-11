"""Compact dimensional limb geometry sharing one native outline per shell pair."""
class CohesiveLimbIntent:
 def __init__(self,g):self.g=g;self.c=g.component;self.d=g.design
 def parameters(self):
  definitions={'lc_thigh_length':170,'lc_shank_foot_center':148,'lc_profile_tip_setback':12,'lc_shin_half_width':11,'lc_shin_curve_amplitude':14,'lc_bearing_od':28,'lc_bearing_id':12,'lc_bearing_width':8,'lc_knee_radial_land':7,'lc_shin_y_min':51,'lc_shin_width':34,'lc_shin_split_offset':16,'lc_crank_radius':28,'lc_pin_eye_radius':10.5,'lc_shin_edge_radius':1.2}
  for key,value in definitions.items():self.g.parameter(key,value,comment='Cohesive limb family: dimensions separate structural envelope from hardware interfaces')
  for key,value in {'lc_shin_profile_length':'lc_shank_foot_center - lc_profile_tip_setback','lc_knee_crown_radius':'lc_bearing_od/2 + lc_knee_radial_land','lc_shin_y_max':'lc_shin_y_min + lc_shin_width','lc_shin_split_y':'lc_shin_y_min + lc_shin_split_offset','lc_pin_x':'lc_crank_radius*cos(lc_crank_phase)','lc_pin_z':'-lc_crank_radius*sin(lc_crank_phase)'}.items():self.g.parameter(key,value)
 def outline(self,fit):
  g=self.g;c=self.c;g.parameter('lc_crank_phase',-78,'deg');self.parameters();g.parameter('lc_cam_tangent_angle','acos((lc_knee_crown_radius-lc_pin_eye_radius)/lc_crank_radius)','deg')
  plane=g.plane(c.xZConstructionPlane,'lc_shin_y_min','Shin inboard envelope datum');sk=c.sketches.add(plane);sk.name='Shared shin cam and flowing stem';sk.isComputeDeferred=True;origin=g.skeleton_point(sk,'0 mm','0 mm');sk.geometricConstraints.addCoincident(origin,sk.originPoint)
  pin=g.skeleton_point(sk,'lc_pin_x','-lc_pin_z');g.point_dimensions(sk,pin,'lc_pin_x','-lc_pin_z')
  # Native XZ coordinates are (world X, -world Z), so angular directions reverse.
  arc0,left,a=g.driven_arc(sk,origin,'lc_knee_crown_radius','-180 deg','lc_crank_phase-lc_cam_tangent_angle','Crown left')
  eye,bb,cc=g.driven_arc(sk,pin,'lc_pin_eye_radius','lc_crank_phase-lc_cam_tangent_angle','lc_crank_phase+lc_cam_tangent_angle','Integral pushrod eye')
  arc1,dd,right=g.driven_arc(sk,origin,'lc_knee_crown_radius','lc_crank_phase+lc_cam_tangent_angle','0 deg','Crown right')
  sk.sketchCurves.sketchLines.addByTwoPoints(a,bb);sk.sketchCurves.sketchLines.addByTwoPoints(cc,dd)
  curves={}
  # Each side uses four original design stations and two endpoint tangents.
  # Three cubic spans are the minimal exact native representation of the
  # source's nonuniform cubic; all poles derive from that compact skeleton.
  for row in fit:
   side=row['side'];values=row['stations_and_derivatives_mm'];expr=[]
   for i,(x,z) in enumerate(values):
    if i<4:
     ze=f'({z/136:.15g})*lc_shin_profile_length'
     if i==0 and side=='right' or i==3 and side=='left':xe=('' if side=='right' else '-')+'lc_knee_crown_radius'
     elif i==3 and side=='right' or i==0 and side=='left':
      ft='(lc_shin_profile_length/lc_shank_foot_center)';xe='lc_shin_curve_amplitude*'+ft+'*(1-'+ft+')'+('+' if side=='right' else '-')+'lc_shin_half_width'
     else:xe=f'({x:.15g}/11)*lc_shin_half_width'
    else:xe=f'({x/136:.15g})*lc_shin_profile_length';ze=f'({z/136:.15g})*lc_shin_profile_length'
    expr.append((xe,'-('+ze+')'))
   last=None;first=None
   for span_index,span in enumerate(row['spans']):
    points=[]
    for i,weights in enumerate(span['coefficients']):
     if i==0 and last is not None:points.append(last);continue
     if side=='right' and span_index==0 and i==0:points.append(right);continue
     if side=='left' and span_index==2 and i==3:points.append(left);continue
     expressions=[' + '.join(f'({weight:.16g})*({expr[k][axis]})' for k,weight in enumerate(weights) if abs(weight)>1e-12) or '0 mm' for axis in [0,1]]
     point=g.skeleton_point(sk,*expressions);g.point_dimensions(sk,point,*expressions);points.append(point)
    spline=sk.sketchCurves.sketchControlPointSplines.add(points,fusion.SplineDegrees.SplineDegreeThree)
    for control,driver in zip(spline.controlPoints,points):
     queue=[control];seen=[];linked=False
     while queue:
      point=queue.pop()
      if point==driver:linked=True;break
      if any(point==old for old in seen):continue
      seen.append(point)
      for constraint in point.geometricConstraints:
       if constraint.objectType==fusion.CoincidentConstraint.classType():
        for endpoint in [constraint.point,constraint.entity]:
         if endpoint.objectType==fusion.SketchPoint.classType() and not any(endpoint==old for old in seen):queue.append(endpoint)
     if not linked:sk.geometricConstraints.addCoincident(control,driver)
    if first is None:first=points[0]
    last=points[-1]
   curves[side]=(first,last)
  sk.sketchCurves.sketchLines.addByTwoPoints(curves['right'][1],curves['left'][0]);sk.isComputeDeferred=False;assert sk.profiles.count==1,sk.profiles.count;return sk
 def blank(self,fit):
  g=self.g;sk=self.outline(fit);feature=g.extrude(sk,'lc_shin_width','Shared structural shin envelope');body=feature.bodies.item(0);edges=core.ObjectCollection.create()
  for edge in body.edges:
   box=edge.boundingBox
   if any(abs(box.minPoint.y-v)<1e-6 and abs(box.maxPoint.y-v)<1e-6 for v in [g.mm('lc_shin_y_min')/10,g.mm('lc_shin_y_max')/10]):edges.add(edge)
  inp=self.c.features.filletFeatures.createInput();inp.edgeSetInputs.addConstantRadiusEdgeSet(edges,g.value('lc_shin_edge_radius'),False);f=self.c.features.filletFeatures.add(inp);f.name='Soft printable cheek edges';return f.bodies.item(0)
 def circles(self,y,definitions,name):
  g=self.g;plane=g.plane(self.c.xZConstructionPlane,y,name+' datum');sk=self.c.sketches.add(plane);sk.name=name;sk.isComputeDeferred=True
  previous={}
  for x,z,r in definitions:
   center=g.skeleton_point(sk,x,'-('+z+')');g.point_dimensions(sk,center,x if x not in previous else None,'-('+z+')')
   if x in previous:sk.geometricConstraints.addVerticalPoints(previous[x],center)
   previous[x]=center;circle=sk.sketchCurves.sketchCircles.addByCenterRadius(center.geometry,g.mm(r)/10);sk.geometricConstraints.addCoincident(circle.centerSketchPoint,center);dim=sk.sketchDimensions.addRadialDimension(circle,core.Point3D.create(center.geometry.x+.5,center.geometry.y+.5,0));dim.parameter.expression=r
  sk.isComputeDeferred=False;return sk
 def extrude_all(self,sk,depth,name,operation,body=None):
  profiles=core.ObjectCollection.create()
  for p in sk.profiles:profiles.add(p)
  inp=self.c.features.extrudeFeatures.createInput(profiles,operation);inp.setDistanceExtent(False,self.g.value(depth))
  if body is not None:inp.participantBodies=[body]
  f=self.c.features.extrudeFeatures.add(inp);f.name=name;sk.isLightBulbOn=False;return f.bodies.item(0)
 def housing(self,body):
  g=self.g;definitions={'lc_shell_wall':4,'lc_web_tip_margin':8,'lc_web_top_width':22,'lc_web_tip_width':14,'lc_web_tip_center_x':1,'lc_web_corner_radius':4,'lc_clamp_land_radius':8.6,'lc_clamp_x':2,'lc_clamp_upper_z':-30,'lc_clamp_lower_z':-105,'lc_inner_bearing_lead':2,'lc_bearing_span':24,'lc_bearing_fit_allowance':0,'lc_shaft_channel_radius':8.2}
  for key,value in definitions.items():g.parameter(key,value)
  for key,value in {'lc_pocket_y':'lc_shin_y_min + lc_shell_wall','lc_pocket_depth':'lc_shin_width - 2*lc_shell_wall','lc_web_top_z':'-(lc_knee_crown_radius+lc_shell_wall)','lc_web_bottom_z':'-(lc_shin_profile_length-lc_web_tip_margin)','lc_bearing_inner_y':'lc_shin_y_min + lc_inner_bearing_lead','lc_bearing_outer_y':'lc_bearing_inner_y + lc_bearing_span','lc_bearing_seat_radius':'lc_bearing_od/2+lc_bearing_fit_allowance'}.items():g.parameter(key,value)
  plane=g.plane(self.c.xZConstructionPlane,'lc_pocket_y','Shared inner web datum');sk=self.c.sketches.add(plane);sk.name='Four-point tapered structural web';sk.isComputeDeferred=True
  expressions=[('-lc_web_top_width/2','-lc_web_top_z'),('lc_web_top_width/2','-lc_web_top_z'),('lc_web_tip_center_x+lc_web_tip_width/2','-lc_web_bottom_z'),('lc_web_tip_center_x-lc_web_tip_width/2','-lc_web_bottom_z')];points=[]
  for i,(x,z) in enumerate(expressions):
   p=g.skeleton_point(sk,x,z);g.point_dimensions(sk,p,x,z if i in [0,2] else None);points.append(p)
   if i in [1,3]:sk.geometricConstraints.addHorizontalPoints(points[i-1],p)
  for i,p in enumerate(points):sk.sketchCurves.sketchLines.addByTwoPoints(p,points[(i+1)%4])
  sk.isComputeDeferred=False;body=self.extrude_all(sk,'lc_pocket_depth','Hollow structural web',fusion.FeatureOperations.CutFeatureOperation,body)
  edges=core.ObjectCollection.create()
  for e in body.edges:
   box=e.boundingBox
   if abs(box.minPoint.y-g.mm('lc_pocket_y')/10)<1e-6 and abs(box.maxPoint.y-g.mm('lc_pocket_y+lc_pocket_depth')/10)<1e-6 and abs(box.maxPoint.x-box.minPoint.x)<1e-6 and abs(box.maxPoint.z-box.minPoint.z)<1e-6:edges.add(e)
  assert edges.count==4,edges.count;inp=self.c.features.filletFeatures.createInput();inp.edgeSetInputs.addConstantRadiusEdgeSet(edges,g.value('lc_web_corner_radius'),False);f=self.c.features.filletFeatures.add(inp);f.name='Printable web corner radii';body=f.bodies.item(0)
  sk=self.circles('lc_shin_y_min',[('lc_clamp_x','lc_clamp_upper_z','lc_clamp_land_radius'),('lc_clamp_x','lc_clamp_lower_z','lc_clamp_land_radius')],'Paired compression lands');body=self.extrude_all(sk,'lc_shin_width','Integral clamp lands',fusion.FeatureOperations.JoinFeatureOperation,body)
  sk=self.circles('lc_shin_y_min-1 mm',[('0 mm','0 mm','lc_bearing_seat_radius')],'Inboard bearing seat');body=self.extrude_all(sk,'lc_bearing_inner_y+lc_bearing_width-lc_shin_y_min+1 mm','Inboard serviceable bearing seat',fusion.FeatureOperations.CutFeatureOperation,body)
  sk=self.circles('lc_bearing_outer_y',[('0 mm','0 mm','lc_bearing_seat_radius')],'Outboard bearing seat');body=self.extrude_all(sk,'lc_shin_y_max-lc_bearing_outer_y+1 mm','Outboard serviceable bearing seat',fusion.FeatureOperations.CutFeatureOperation,body)
  sk=self.circles('lc_shin_y_min-7 mm',[('0 mm','0 mm','lc_shaft_channel_radius')],'Knee shaft passage');body=self.extrude_all(sk,'lc_shin_width+14 mm','Knee shaft and spacer clearance',fusion.FeatureOperations.CutFeatureOperation,body)
  return body
 def motion_envelope(self,kind):
  g=self.g
  for key,value in {'lc_rod_length':'lc_thigh_length','lc_rod_stem_half_width':3,'lc_rod_eye_half_width':7.5,'lc_rod_taper_length':12,'lc_rod_clearance':1,'lc_rod_channel_y':66.5,'lc_rod_channel_width':7}.items():g.parameter(key,value)
  for key,value in {'lc_knee_min':-156,'lc_knee_max':-48}.items():g.parameter(key,value,'deg')
  for key,value in {'lc_rod_base_angle':'atan(lc_rod_taper_length/lc_rod_stem_half_width)','lc_rod_tip_angle':'atan((lc_rod_length-lc_rod_taper_length)/lc_rod_stem_half_width)'}.items():g.parameter(key,value,'deg')
  for key,value in {'lc_rod_mid_radius':'sqrt(lc_rod_taper_length^2+lc_rod_stem_half_width^2)','lc_rod_tip_radius':'sqrt((lc_rod_length-lc_rod_taper_length)^2+lc_rod_stem_half_width^2)'}.items():g.parameter(key,value)
  g.parameter('lc_rod_tangent_angle','acos(lc_rod_eye_half_width/lc_rod_mid_radius)','deg')
  plane=g.plane(self.c.xZConstructionPlane,'lc_rod_channel_y',kind+' motion clearance datum');sk=self.c.sketches.add(plane);sk.name=kind+' continuous motion envelope';sk.isComputeDeferred=True;center=g.skeleton_point(sk,'lc_pin_x','-lc_pin_z');g.point_dimensions(sk,center,'lc_pin_x','-lc_pin_z')
  def point(radius,a):
   x='lc_pin_x+('+radius+')*cos('+a+')';z='-(lc_pin_z+('+radius+')*sin('+a+'))';p=g.skeleton_point(sk,x,z);g.point_dimensions(sk,p,x,z);return p
  def arc(c,r,a,b):return g.driven_arc(sk,c,r,'-('+a+')','-('+b+')',kind)
  g.parameter('lc_rod_chord_normal','(lc_knee_min+lc_knee_max)/2+270 deg','deg');normal='lc_rod_chord_normal';theta_e='lc_rod_base_angle+lc_knee_min';theta_f='180 deg-lc_rod_base_angle+lc_knee_max';clear='lc_rod_clearance'
  if kind=='Rod stem':
   a=point('lc_rod_mid_radius',theta_e);b=point('lc_rod_tip_radius','lc_rod_tip_angle+lc_knee_min');c=point('lc_rod_tip_radius','180 deg-lc_rod_tip_angle+lc_knee_max');dd=point('lc_rod_mid_radius',theta_f)
   arcs=[arc(a,clear,normal,'lc_knee_min+360 deg'),arc(b,clear,'lc_knee_min','lc_rod_tip_angle+lc_knee_min'),arc(center,'lc_rod_tip_radius+lc_rod_clearance','lc_rod_tip_angle+lc_knee_min','180 deg-lc_rod_tip_angle+lc_knee_max'),arc(c,clear,'180 deg-lc_rod_tip_angle+lc_knee_max','lc_knee_max+180 deg'),arc(dd,clear,'lc_knee_max+180 deg',normal)]
  else:
   a=point('lc_rod_eye_half_width','180 deg+lc_knee_max');b=point('lc_rod_eye_half_width','lc_knee_min');e=point('lc_rod_mid_radius',theta_e);f=point('lc_rod_mid_radius',theta_f)
   arcs=[arc(a,clear,'180 deg+lc_knee_max',normal),arc(b,clear,normal,'lc_knee_min+360 deg'),arc(center,'lc_rod_eye_half_width+lc_rod_clearance','lc_knee_min',theta_e+'-lc_rod_tangent_angle'),arc(e,clear,theta_e+'-lc_rod_tangent_angle',theta_e),arc(center,'lc_rod_mid_radius+lc_rod_clearance',theta_e,theta_f),arc(f,clear,theta_f,theta_f+'+lc_rod_tangent_angle'),arc(center,'lc_rod_eye_half_width+lc_rod_clearance',theta_f+'+lc_rod_tangent_angle','180 deg+lc_knee_max')]
  for i,(_,first,last) in enumerate(arcs):
   following=arcs[(i+1)%len(arcs)][1]
   if last.geometry.distanceTo(following.geometry)>1e-7:sk.sketchCurves.sketchLines.addByTwoPoints(last,following)
  sk.isComputeDeferred=False;assert sk.profiles.count==1,(kind,sk.profiles.count);return sk
 def rod_clearances(self,body):
  for kind in ['Rod stem','Rod taper']:
   sk=self.motion_envelope(kind);body=self.extrude_all(sk,'lc_rod_channel_width',kind+' swept clearance',fusion.FeatureOperations.CutFeatureOperation,body)
  self.g.parameter('lc_bushing_flange_radius',6.3);self.g.parameter('lc_pin_eye_clearance_radius',8.5)
  sk=self.circles('lc_rod_channel_y',[('lc_pin_x','lc_pin_z','lc_pin_eye_clearance_radius')],'Output eye axial clearance');body=self.extrude_all(sk,'lc_rod_channel_width','Output eye clearance',fusion.FeatureOperations.CutFeatureOperation,body)
  sk=self.circles('lc_rod_channel_y-.7 mm',[('lc_pin_x','lc_pin_z','lc_bushing_flange_radius')],'Bushing flange clearance');body=self.extrude_all(sk,'lc_rod_channel_width+1.4 mm','Bushing flange clearance',fusion.FeatureOperations.CutFeatureOperation,body)
  return body
 def hexagons(self,y,definitions,name):
  g=self.g;plane=g.plane(self.c.xZConstructionPlane,y,name+' datum');sk=self.c.sketches.add(plane);sk.name=name;sk.isComputeDeferred=True;centers={}
  for x,z,af in definitions:
   cx,cy,r=g.mm(x)/10,-g.mm(z)/10,g.mm(af)/math.sqrt(3)/10;points=[core.Point3D.create(cx+r*math.cos(i*math.pi/3),cy+r*math.sin(i*math.pi/3),0) for i in range(6)];lines=[]
   for i,p in enumerate(points):
    start=lines[-1].endSketchPoint if lines else p;end=lines[0].startSketchPoint if i==5 else points[i+1];lines.append(sk.sketchCurves.sketchLines.addByTwoPoints(start,end))
   polygon=sk.geometricConstraints.addPolygon(lines);center=polygon.centerPoint;g.point_dimensions(sk,center,x if x not in centers else None,'-('+z+')')
   if x in centers:sk.geometricConstraints.addVerticalPoints(centers[x],center)
   centers[x]=center;vertex=min(polygon.points,key=lambda p:p.geometry.distanceTo(points[0]));sk.geometricConstraints.addHorizontalPoints(center,vertex);g.point_dimensions(sk,vertex,'('+x+')+('+af+')/sqrt(3)',None)
  sk.isComputeDeferred=False;return sk
 def hardware(self,body):
  g=self.g
  definitions={'lc_pin_head_clearance':5.3,'lc_pin_shoulder_clearance':3.05,'lc_pin_thread_clearance':2.7,'lc_pin_nut_af':8.2,'lc_clamp_sleeve_radius':4.05,'lc_clamp_bolt_radius':2.2,'lc_clamp_head_radius':4.1,'lc_clamp_nut_af':7.2,'lc_extraction_radius':1.3}
  for key,value in definitions.items():g.parameter(key,value)
  self.d.userParameters.itemByName('lc_clamp_lower_z').expression='-(105/136)*lc_shin_profile_length'
  def cut(y,depth,defs,name):
   nonlocal body
   sk=self.circles(y,defs,name);body=self.extrude_all(sk,depth,name,fusion.FeatureOperations.CutFeatureOperation,body)
  pin=lambda r:[('lc_pin_x','lc_pin_z',r)]
  clamp=lambda r:[('lc_clamp_x','lc_clamp_upper_z',r),('lc_clamp_x','lc_clamp_lower_z',r)]
  cut('lc_shin_y_min-1 mm','10 mm',pin('lc_pin_head_clearance'),'Shoulder screw head recess')
  cut('lc_shin_y_min+9 mm','20 mm',pin('lc_pin_shoulder_clearance'),'Shoulder screw journal')
  cut('lc_shin_y_max-5.1 mm','12 mm',pin('lc_pin_thread_clearance'),'M5 screw tip clearance')
  sk=self.hexagons('lc_shin_y_max-5 mm',[('lc_pin_x','lc_pin_z','lc_pin_nut_af')],'Captured M5 nut');body=self.extrude_all(sk,'12 mm','Captured M5 nut',fusion.FeatureOperations.CutFeatureOperation,body)
  cut('lc_shin_y_min+7 mm','18 mm',clamp('lc_clamp_sleeve_radius'),'Compression sleeve seats')
  cut('lc_shin_y_min-5 mm','lc_shin_width+8 mm',clamp('lc_clamp_bolt_radius'),'M4 clamp clearance')
  cut('lc_shin_y_min-1 mm','8 mm',clamp('lc_clamp_head_radius'),'M4 clamp head recesses')
  sk=self.hexagons('lc_shin_y_max-9 mm',clamp('lc_clamp_nut_af'),'Paired M4 nut pockets');body=self.extrude_all(sk,'12 mm','Paired M4 nut pockets',fusion.FeatureOperations.CutFeatureOperation,body)
  cut('lc_bearing_inner_y+lc_bearing_width','lc_bearing_span-lc_bearing_width',[('lc_bearing_od/2-lc_extraction_radius','0 mm','lc_extraction_radius'),('-(lc_bearing_od/2-lc_extraction_radius)','0 mm','lc_extraction_radius')],'Bearing extraction punch paths')
  return body
