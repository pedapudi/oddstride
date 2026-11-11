"""One editable thigh silhouette shared by both structural shell halves."""
class CohesiveThighIntent(CohesiveLimbIntent):
 def thigh_parameters(self):
  for key,value in {'lc_motor_case_radius':41,'lc_thigh_motor_radial_margin':8,'lc_thigh_knee_radial_margin':2,'lc_thigh_inner_y':47,'lc_thigh_outer_y':100,'lc_thigh_outer_edge_radius':7,'lc_thigh_inner_edge_radius':4}.items():self.g.parameter(key,value)
  for key,value in {'lc_thigh_hip_radius':'lc_motor_case_radius+lc_thigh_motor_radial_margin','lc_thigh_knee_radius':'lc_knee_crown_radius+lc_thigh_knee_radial_margin','lc_thigh_width':'lc_thigh_outer_y-lc_thigh_inner_y'}.items():self.g.parameter(key,value)
 def thigh_outline(self,fit):
  g=self.g;c=self.c;self.thigh_parameters();plane=g.plane(c.xZConstructionPlane,'lc_thigh_inner_y','Shared thigh inner datum');sk=c.sketches.add(plane);sk.name='Shared hip-to-knee design envelope';sk.isComputeDeferred=True
  hip=g.skeleton_point(sk,'0 mm','0 mm');sk.geometricConstraints.addCoincident(hip,sk.originPoint);knee=g.skeleton_point(sk,'0 mm','lc_thigh_length');g.point_dimensions(sk,knee,'0 mm','lc_thigh_length')
  _,hip_left,hip_right=g.driven_arc(sk,hip,'lc_thigh_hip_radius','-180 deg','0 deg','Hip crown')
  _,knee_right,knee_left=g.driven_arc(sk,knee,'lc_thigh_knee_radius','0 deg','180 deg','Knee crown')
  for row in fit:
   side=row['side'];station_count=row['station_count'];expr=[]
   for i,(x,z) in enumerate(row['stations_and_derivatives_mm']):
    if i<station_count:
     if side=='front' and i==0 or side=='rear' and i==station_count-1:xe=('' if side=='front' else '-')+'lc_thigh_hip_radius'
     elif side=='front' and i==station_count-1 or side=='rear' and i==0:xe=('' if side=='front' else '-')+'lc_thigh_knee_radius'
     else:xe=f'({x/49:.15g})*lc_thigh_hip_radius'
    else:xe=f'({x/170:.15g})*lc_thigh_length'
    expr.append((xe,f'({-z/170:.15g})*lc_thigh_length'))
   last=None
   for span_index,span in enumerate(row['spans']):
    points=[]
    for i,weights in enumerate(span['coefficients']):
     if i==0 and last is not None:points.append(last);continue
     if span_index==0 and i==0:points.append(hip_right if side=='front' else knee_left);continue
     if span_index==len(row['spans'])-1 and i==3:points.append(knee_right if side=='front' else hip_left);continue
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
    last=points[-1]
  sk.isComputeDeferred=False;assert sk.profiles.count==1,sk.profiles.count;return sk
 def thigh_blank(self,fit):
  g=self.g;sk=self.thigh_outline(fit);body=g.extrude(sk,'lc_thigh_width','Continuous structural thigh envelope').bodies.item(0)
  for y,r,name in [('lc_thigh_outer_y','lc_thigh_outer_edge_radius','Soft outer cheek'),('lc_thigh_inner_y','lc_thigh_inner_edge_radius','Soft inboard cheek')]:
   edges=core.ObjectCollection.create();value=g.mm(y)/10
   for e in body.edges:
    box=e.boundingBox
    if abs(box.minPoint.y-value)<1e-6 and abs(box.maxPoint.y-value)<1e-6:edges.add(e)
   inp=self.c.features.filletFeatures.createInput();inp.edgeSetInputs.addConstantRadiusEdgeSet(edges,g.value(r),False);f=self.c.features.filletFeatures.add(inp);f.name=name;body=f.bodies.item(0)
  return body
 def thigh_rod_space(self,body):
  g=self.g
  for key,value in {'lc_thigh_rod_clearance_radius':9,'lc_thigh_rod_channel_y':65.5,'lc_thigh_rod_channel_width':9}.items():g.parameter(key,value)
  for key,value in {'lc_thigh_rod_upper_angle':'-(lc_knee_max+lc_crank_phase)','lc_thigh_rod_lower_angle':'-(lc_knee_min+lc_crank_phase)'}.items():g.parameter(key,value,'deg')
  for key,value in {'lc_thigh_rod_upper_x':'lc_crank_radius*cos(lc_thigh_rod_upper_angle)','lc_thigh_rod_upper_z':'lc_crank_radius*sin(lc_thigh_rod_upper_angle)','lc_thigh_rod_lower_x':'lc_crank_radius*cos(lc_thigh_rod_lower_angle)','lc_thigh_rod_lower_z':'-lc_thigh_length+lc_crank_radius*sin(lc_thigh_rod_lower_angle)'}.items():g.parameter(key,value)
  g.parameter('lc_thigh_rod_chord_normal','atan((lc_thigh_rod_lower_x-lc_thigh_rod_upper_x)/(lc_thigh_rod_upper_z-lc_thigh_rod_lower_z))','deg')
  plane=g.plane(self.c.xZConstructionPlane,'lc_thigh_rod_channel_y','Equal-crank rod plane');sk=self.c.sketches.add(plane);sk.name='Continuous two-crank rod envelope';sk.isComputeDeferred=True
  centers=[]
  for x,z in [('lc_thigh_rod_upper_x','lc_thigh_rod_upper_z'),('0 mm','0 mm'),('0 mm','-lc_thigh_length'),('lc_thigh_rod_lower_x','lc_thigh_rod_lower_z')]:
   p=g.skeleton_point(sk,x,'-('+z+')');g.point_dimensions(sk,p,x,'-('+z+')');centers.append(p)
  definitions=[('lc_thigh_rod_clearance_radius','lc_thigh_rod_chord_normal','lc_thigh_rod_upper_angle'),('lc_crank_radius+lc_thigh_rod_clearance_radius','lc_thigh_rod_upper_angle','180 deg'),('lc_crank_radius+lc_thigh_rod_clearance_radius','180 deg','lc_thigh_rod_lower_angle'),('lc_thigh_rod_clearance_radius','lc_thigh_rod_lower_angle','lc_thigh_rod_chord_normal+360 deg')]
  arcs=[g.driven_arc(sk,c,r,'-('+a+')','-('+b+')','Rod envelope') for c,(r,a,b) in zip(centers,definitions)]
  for i,(_,first,last) in enumerate(arcs):
   following=arcs[(i+1)%len(arcs)][1]
   if last.geometry.distanceTo(following.geometry)>1e-7:sk.sketchCurves.sketchLines.addByTwoPoints(last,following)
  sk.isComputeDeferred=False;assert sk.profiles.count==1,sk.profiles.count;return self.extrude_all(sk,'lc_thigh_rod_channel_width','Equal-crank pushrod swept clearance',fusion.FeatureOperations.CutFeatureOperation,body)
