"""Four-curve thigh skeleton with independent hardware and structural dimensions."""
class SlimThighIntent(CohesiveThighIntent):
 def slim_parameters(self):
  g=self.g
  for name,value in {'st_hip_half_width':44.5,'st_hip_crown_height':51,'st_knee_radius':21.5,'st_rear_clamp_flare':3.5,'st_root_y':9,'st_cap_y':94,'st_wall':8,'st_inner_face':6,'st_waist_skin':6,'st_outer_edge_radius':6}.items():g.parameter(name,value,comment='Current closed structural thigh; hardware datums remain separate from the exterior dimensions.')
 def slim_outline(self,skeleton,y='st_root_y'):
  self.slim_parameters();g=self.g;c=self.c;plane=g.plane(c.xZConstructionPlane,y,'Thigh shared outline datum');sk=c.sketches.add(plane);sk.name='Elliptical hip, two flowing sides and circular knee';sk.isComputeDeferred=True
  arc=sk.sketchCurves.sketchEllipses.add(sk.originPoint,core.Point3D.create(0,-g.mm('st_hip_crown_height')/10,0),core.Point3D.create(g.mm('st_hip_half_width')/10,0,0))
  sk.sketchDimensions.addEllipseMajorRadiusDimension(arc,core.Point3D.create(1,-6,0)).parameter.expression='st_hip_crown_height';sk.sketchDimensions.addEllipseMinorRadiusDimension(arc,core.Point3D.create(5,-1,0)).parameter.expression='st_hip_half_width'
  hip_left=g.skeleton_point(sk,'-st_hip_half_width','0 mm');g.point_dimensions(sk,hip_left,'-st_hip_half_width','0 mm');hip_right=g.skeleton_point(sk,'st_hip_half_width','0 mm');g.point_dimensions(sk,hip_right,'st_hip_half_width','0 mm')
  tangent=sk.sketchCurves.sketchLines.addByTwoPoints(hip_left,core.Point3D.create(hip_left.geometry.x,1,0));tangent.isConstruction=True;sk.geometricConstraints.addVertical(tangent);sk.geometricConstraints.addTangent(arc,tangent)
  sk.sketchCurves.sketchLines.addByTwoPoints(hip_left,hip_right)
  knee=g.skeleton_point(sk,'0 mm','lc_thigh_length');g.point_dimensions(sk,knee,'0 mm','lc_thigh_length');_,knee_right,knee_left=g.driven_arc(sk,knee,'st_knee_radius','0 deg','180 deg','Knee crown')
  for row in skeleton['sides']:
   side=row['side'];values=row['stations_and_derivatives_mm'];n=row['station_count'];expressions=[]
   for i,(x,z)in enumerate(values):
    if i<n:
     if abs(z)<1e-8:xe=(''if x>0 else'-')+'st_hip_half_width'
     elif abs(z+170)<1e-8:xe=(''if x>0 else'-')+'st_knee_radius'
     elif side=='rear'and abs(z+48)<1e-8:xe='-44.8 mm-.22*st_rear_clamp_flare'
     elif side=='rear'and abs(z+75)<1e-8:xe='-40 mm-st_rear_clamp_flare'
     elif side=='rear'and abs(z+100)<1e-8:xe='-36.5 mm-.27*st_rear_clamp_flare'
     else:xe=f'({x/44.5:.17g})*st_hip_half_width'
    else:xe=f'({x/170:.17g})*lc_thigh_length'
    expressions.append([xe,f'({-z/170:.17g})*lc_thigh_length'])
   drivers=[];xdrivers={}
   for i,weights in enumerate(row['station_to_control_pole_coefficients']):
    if i==0:
     first=knee_right if side=='front'else hip_left;drivers.append(first);xdrivers[round(first.geometry.x,9)]=first;continue
    if i==len(row['station_to_control_pole_coefficients'])-1:drivers.append(hip_right if side=='front'else knee_left);continue
    expr=[' + '.join(f'({w:.17g})*({expressions[k][axis]})'for k,w in enumerate(weights)if abs(w)>1e-14)for axis in[0,1]];p=g.skeleton_point(sk,*expr);key=round(p.geometry.x,9);g.point_dimensions(sk,p,None if key in xdrivers else expr[0],expr[1])
    if key in xdrivers:sk.geometricConstraints.addVerticalPoints(xdrivers[key],p)
    xdrivers[key]=p;drivers.append(p)
   native_nonuniform_cubic(sk,drivers,row['internal_normalized_knots'])
  sk.isComputeDeferred=False;assert sk.profiles.count==3,sk.profiles.count
  assert sk.sketchCurves.sketchControlPointSplines.count==2
  return sk
 def structural_parameters(self):
  self.slim_parameters()
  for key,value in {'st_case_outer_radius':45.4,'st_case_back_y':51,'st_face_crown_radius':500,'st_face_crown_center_y':'st_cap_y-st_face_crown_radius','st_waist_floor_y':86,'st_waist_blend_radius':2,'st_roof_inner_offset':4,'st_guard_width':12,'st_guard_depth':19,'st_guard_height':10,'st_guard_radius':2,'st_guard_center_y':41.5,'st_guard_center_z':45}.items():self.g.parameter(key,value)
 def fillet_selected(self,body,radius,name,accept,tangent=False):
  edges=core.ObjectCollection.create()
  for edge in body.edges:
   if accept(edge):edges.add(edge)
  assert edges.count,(name,'No matching edges')
  inp=self.c.features.filletFeatures.createInput();inp.edgeSetInputs.addConstantRadiusEdgeSet(edges,self.g.value(radius),tangent);feature=self.c.features.filletFeatures.add(inp);feature.name=name;return feature.bodies.item(0)
 def copy_body(self,body,name):
  objects=core.ObjectCollection.create();objects.add(body);feature=self.c.features.copyPasteBodies.add(objects);feature.name=name;return feature.bodies.item(0)
 def cap_stock(self,radius,name):
  g=self.g;plane=g.plane(self.c.xYConstructionPlane,'-250 mm',name+' datum');sk=self.c.sketches.add(plane);sk.name=name+' cylindrical face crown';p=g.skeleton_point(sk,'0 mm','st_face_crown_center_y');g.point_dimensions(sk,p,'0 mm','st_face_crown_center_y');curve=sk.sketchCurves.sketchCircles.addByCenterRadius(p.geometry,g.mm(radius)/10);sk.geometricConstraints.addCoincident(curve.centerSketchPoint,p);sk.sketchDimensions.addRadialDimension(curve,core.Point3D.create(1,1,0)).parameter.expression=radius;return g.extrude(sk,'400 mm',name).bodies.item(0)
 def roof_stock(self,offset,reinforced,name):
  g=self.g;plane=g.plane(self.c.yZConstructionPlane,'-100 mm',name+' datum');sk=self.c.sketches.add(plane);sk.name=name+' two tangent cubic spans';sk.isComputeDeferred=True
  ydrivers={}
  def constrained_point(ze,ye):
   p=g.skeleton_point(sk,ze,ye);key=round(p.geometry.y,9);g.point_dimensions(sk,p,ze,None if key in ydrivers else ye)
   if key in ydrivers:sk.geometricConstraints.addHorizontalPoints(ydrivers[key],p)
   ydrivers[key]=p;return p
  def point(z,y):
   ze=f'({-z/170:.17g})*lc_thigh_length';ye=('st_waist_floor_y' if y==86 else 'st_cap_y')+'-('+offset+')'
   if reinforced and y==86:ye+='-(st_waist_skin-st_roof_inner_offset)'
   return constrained_point(ze,ye)
  points={};last=None
  for controls in [[(-117,94),(-108,94),(-105,86),(-90,86)],[(-90,86),(-76,86),(-61,94),(-45,94)]]:
   drivers=[]
   for z,y in controls:
    p=points.get((z,y))
    if p is None:p=point(z,y);points[(z,y)]=p
    drivers.append(p)
   native_nonuniform_cubic(sk,drivers,[])
  # The lower boundary and the ends lie outside the part, while their top
  # height follows the same roof and wall dimensions as the two cubic spans.
  def outer(z,y):
   ze=f'{-z} mm';ye='st_cap_y-('+offset+')' if y==94 else '-40 mm-('+offset+')';return constrained_point(ze,ye)
  a,b,c,d=outer(-250,-40),outer(-250,94),outer(100,94),outer(100,-40)
  for p,q in [(a,b),(b,points[(-117,94)]),(points[(-45,94)],c),(c,d),(d,a)]:sk.sketchCurves.sketchLines.addByTwoPoints(p,q)
  sk.isComputeDeferred=False;assert sk.profiles.count==1;return g.extrude(sk,'200 mm',name).bodies.item(0)
 def shell_stock(self,body,cavity,prewaist_only=False):
  self.structural_parameters();g=self.g;c=self.c
  body=self.fillet_selected(body,'st_outer_edge_radius','Continuous outer cheek edge',lambda e:abs(e.boundingBox.minPoint.y-g.mm('st_cap_y')/10)<1e-6 and abs(e.boundingBox.maxPoint.y-g.mm('st_cap_y')/10)<1e-6)
  fill_blank=self.copy_body(body,'Shared unwaisted stock for continuous exterior');fill_blank.name='Construction continuous exterior stock';fill_blank.isLightBulbOn=False
  root=self.extrude_all(self.circles('st_root_y',[('0 mm','0 mm','st_case_outer_radius')],'Proximal motor structural cup'),'st_case_back_y-st_root_y','Proximal motor cup stock',fusion.FeatureOperations.NewBodyFeatureOperation)
  guard=g.box('st_guard_width','st_guard_depth','st_guard_height','0 mm','st_guard_center_y','st_guard_center_z','Broad flange guard');guard=g.round_edges(guard,'st_guard_radius','Guard accessible edge radii');objects=core.ObjectCollection.create();objects.add(guard);inp=c.features.circularPatternFeatures.createInput(objects,c.yConstructionAxis);inp.quantity=g.value('3');inp.totalAngle=g.value('360 deg');feature=c.features.circularPatternFeatures.add(inp);feature.name='Three structural flange guards';guards=list(feature.bodies)
  if guard not in guards:guards.append(guard)
  root=g.combine(root,guards,fusion.FeatureOperations.JoinFeatureOperation,'Integral motor cup with flange guards')
  underside=g.box('220 mm','2*lc_thigh_inner_y','300 mm','0 mm','0 mm','-90 mm','Open inboard relief stock');tool=g.combine(underside,[root],fusion.FeatureOperations.CutFeatureOperation,'Inboard relief preserves the motor cup');body=g.combine(body,[tool],fusion.FeatureOperations.CutFeatureOperation,'Open inboard limb face')
  cap=self.cap_stock('st_face_crown_radius','Subtle transverse outside crown');body=g.combine(body,[cap],fusion.FeatureOperations.IntersectFeatureOperation,'Outside face crown',True);fill_blank=g.combine(fill_blank,[cap],fusion.FeatureOperations.IntersectFeatureOperation,'Continuous exterior crown')
  roof=self.roof_stock('0 mm',False,'Waist envelope');body=g.combine(body,[roof],fusion.FeatureOperations.IntersectFeatureOperation,'Waist depth transition')
  if prewaist_only:
   body.name='Construction prewaist structural stock';return body,fill_blank,cavity
  return self.finish_structural_stock(body,fill_blank,cavity)
 def finish_structural_stock(self,body,fill_blank,cavity):
  g=self.g;c=self.c
  def waist(edge):
   ok,lo,hi=edge.evaluator.getParameterExtents();assert ok
   parameters=[lo]+[lo+(hi-lo)*i/40 for i in range(1,40)]+[hi];ok,points=edge.evaluator.getPointsAtParameters(parameters);assert ok
   total=0;center=core.Vector3D.create()
   for a,b in zip(points,points[1:]):
    length=a.distanceTo(b);total+=length;center.add(core.Vector3D.create((a.x+b.x)*length/2,(a.y+b.y)*length/2,(a.z+b.z)*length/2))
   center.scaleBy(1/total)
   if not(-15<center.z<-5.5 and center.y>8 and edge.length>1.5):return False
   assert edge.faces.count==2
   normals=[]
   for face in edge.faces:
    ok,normal=face.evaluator.getNormalAtPoint(points[20]);assert ok;normal.normalize();normals.append(normal)
   # Tangential seams already belong to a smooth source surface. OCC ignores
   # them in its edge list; explicitly exclude them from Fusion's fillet input.
   return abs(normals[0].dotProduct(normals[1]))<.999999
  body=self.fillet_selected(body,'st_waist_blend_radius','Waist-to-side transition radii',waist,True)
  cap=self.cap_stock('st_face_crown_radius-st_roof_inner_offset','Inner crowned face');cavity=g.combine(cavity,[cap],fusion.FeatureOperations.IntersectFeatureOperation,'Cavity follows the face crown');roof=self.roof_stock('st_roof_inner_offset',True,'Reinforced inner waist');cavity=g.combine(cavity,[roof],fusion.FeatureOperations.IntersectFeatureOperation,'Six millimeter waist skin')
  # Keep a native copy of the outer blank for clamp and tie lands. It is
  # consumed by the next stage, rather than becoming an extra printed part.
  land_blank=self.copy_body(body,'Shared stock for integral clamp and tie lands');land_blank.name='Construction land clipping stock';land_blank.isLightBulbOn=False
  body=g.combine(body,[cavity],fusion.FeatureOperations.CutFeatureOperation,'Hollow structural thigh with linked sidewalls');body.name='Closed thigh structural stock';fill_blank.name='Construction continuous exterior stock';return body,fill_blank,land_blank
 def interface_parameters(self):
  for key,value in {'st_rear_clamp_x':-36,'st_rear_clamp_z':'-(66/170)*lc_thigh_length','st_front_clamp_x':5,'st_front_clamp_z':'-(70/170)*lc_thigh_length','st_clamp_land_radius':8.8,'st_tie_land_radius':5.2,'st_case_reference_radius':40,'st_case_radial_allowance':.25,'st_stator_radial_allowance':.3,'st_knee_cheek_radius':45,'st_knee_cheek_y':45,'st_knee_cheek_thickness':4,'st_knee_chamber_y':50.5,'st_knee_chamber_width':36,'st_knee_chamber_radius':53,'st_knee_chamber_fillet':3,'st_output_tail_y':85.5,'st_output_tail_width':3.5,'st_output_tail_radius':4.25,'st_rod_stem_clearance_radius':4.5}.items():self.g.parameter(key,value)
  for key,value in {'st_case_fit_radius':'st_case_reference_radius+st_case_radial_allowance','st_pocket_radius':'sm_stator_outer_radius+st_stator_radial_allowance','st_pocket_lobe_radius':'sm_stator_lobe_radius+st_stator_radial_allowance'}.items():self.g.parameter(key,value)
  self.g.parameter('st_pocket_tangent_angle','acos((st_pocket_radius-st_pocket_lobe_radius)/sm_tie_radius)','deg')
 def tie_centers(self,radius):return [(f'sm_tie_radius*cos({a} deg)',f'sm_tie_radius*sin({a} deg)',radius)for a in [90,210,330]]
 def structural_lands(self,body,envelope,outline_body):
  self.interface_parameters();g=self.g;c=self.c
  pad=self.extrude_all(self.circles('st_knee_cheek_y',[('0 mm','-lc_thigh_length','st_knee_cheek_radius')],'Inboard knee reinforcement'),'st_knee_cheek_thickness','Integral knee cheek stock',fusion.FeatureOperations.NewBodyFeatureOperation);pad=g.round_edges(pad,'1 mm','Knee cheek edge radii')
  # At this inboard depth the shared stock still has its original silhouette:
  # neither the far-side edge round nor transverse crown reaches the cheek.
  # Reuse that native stock instead of projecting and extruding its loop again.
  assert g.mm('st_knee_cheek_y+st_knee_cheek_thickness')<g.mm('st_cap_y-st_outer_edge_radius')
  pad=g.combine(pad,[outline_body],fusion.FeatureOperations.IntersectFeatureOperation,'Knee cheek follows the shared limb outline',True);body=g.combine(body,[pad],fusion.FeatureOperations.JoinFeatureOperation,'Integral inboard knee reinforcement')
  groups=[('Paired structural clamp lands','44 mm','56 mm',[('st_rear_clamp_x','st_rear_clamp_z','st_clamp_land_radius'),('st_front_clamp_x','st_front_clamp_z','st_clamp_land_radius')]),('Motor tie compression lands','st_root_y','51 mm',self.tie_centers('st_tie_land_radius'))]
  for name,y,depth,definitions in groups:
   sk=self.circles(y,definitions,name);f=g.extrude_all(sk,depth,name);pieces=list(f.bodies);clipped=[]
   for i,piece in enumerate(pieces):clipped.append(g.combine(piece,[envelope],fusion.FeatureOperations.IntersectFeatureOperation,name+' boundary '+str(i+1),True))
   body=g.combine(body,clipped,fusion.FeatureOperations.JoinFeatureOperation,name+' joined to both shell faces')
  c.features.removeFeatures.add(envelope).name='Consume shared structural clipping stock';return body
 def stator_pocket(self,datum=None):
  g=self.g;c=self.c;plane=g.plane(c.xZConstructionPlane,datum or 'sm_stator_base_y-.2 mm','Stator plate pocket datum');sk=c.sketches.add(plane);sk.name='Three tangent lobes with independent fit allowance';sk.isComputeDeferred=True;centers=[];ys={}
  for theta in [90,210,330]:
   x=f'sm_tie_radius*cos({theta} deg)';y=f'-sm_tie_radius*sin({theta} deg)';p=g.skeleton_point(sk,x,y);v=round(p.geometry.y,9);g.point_dimensions(sk,p,x,y if v not in ys else None)
   if v in ys:sk.geometricConstraints.addHorizontalPoints(ys[v],p)
   ys[v]=p;centers.append(p)
  arcs=[]
  for theta,center in zip([90,210,330],centers):
   start=f'-({theta} deg-st_pocket_tangent_angle)';end=f'-({theta} deg+st_pocket_tangent_angle)';arcs.extend([g.driven_arc(sk,center,'st_pocket_lobe_radius',start,end,'Tie lobe clearance'),g.driven_arc(sk,sk.originPoint,'st_pocket_radius',end,f'-({theta+120} deg-st_pocket_tangent_angle)','Central stator clearance')])
  for i,(_,first,last)in enumerate(arcs):sk.sketchCurves.sketchLines.addByTwoPoints(last,arcs[(i+1)%len(arcs)][1])
  sk.isComputeDeferred=False;assert sk.profiles.count==1;return sk
 def output_tail(self):
  g=self.g;c=self.c;plane=g.plane(c.xZConstructionPlane,'st_output_tail_y','Knee pin tail movement plane');sk=c.sketches.add(plane);sk.name='True annular knee pin-tail sweep';sk.isComputeDeferred=True
  center=g.skeleton_point(sk,'0 mm','lc_thigh_length');g.point_dimensions(sk,center,'0 mm','lc_thigh_length');upper='-(lc_knee_max+lc_crank_phase)';lower='-(lc_knee_min+lc_crank_phase)';points=[]
  for angle in [upper,lower]:
   x='lc_crank_radius*cos('+angle+')';y='lc_thigh_length-lc_crank_radius*sin('+angle+')';p=g.skeleton_point(sk,x,y);g.point_dimensions(sk,p,x if not points else None,y)
   if points:sk.geometricConstraints.addVerticalPoints(points[0],p)
   points.append(p)
  arcs=[g.driven_arc(sk,center,'lc_crank_radius+st_output_tail_radius','-('+upper+')','-('+lower+')','Outer orbit'),g.driven_arc(sk,points[1],'st_output_tail_radius','-('+lower+')','-('+lower+'+180 deg)','Lower rounded end'),g.driven_arc(sk,center,'lc_crank_radius-st_output_tail_radius','-('+lower+')','-('+upper+')','Inner orbit'),g.driven_arc(sk,points[0],'st_output_tail_radius','-('+upper+'+180 deg)','-('+upper+'+360 deg)','Upper rounded end')]
  sk.isComputeDeferred=False;assert sk.profiles.count==1;return sk
 def motor_and_linkage_interfaces(self,body):
  g=self.g;c=self.c;self.interface_parameters()
  for y,depth,r,name in [('8 mm','53 mm','2.8 mm','Three tie passages'),('60 mm','8 mm','3.1 mm','Tie sleeve lead-ins'),('8.8 mm','1.2 mm','6.3 mm','Inboard tie-pad clearances'),('53.5 mm','1.6 mm','4.8 mm','Outboard stator pad clearances')]:body=self.extrude_all(self.circles(y,self.tie_centers(r),name),depth,name,fusion.FeatureOperations.CutFeatureOperation,body)
  body=self.extrude_all(self.circles('st_root_y',[('0 mm','0 mm','st_case_fit_radius')],'Motor case nominal and process fit'),'sm_stator_base_y-st_root_y','Motor case pocket',fusion.FeatureOperations.CutFeatureOperation,body)
  body=self.extrude_all(self.stator_pocket(),'sm_stator_thickness+.4 mm','Accessible tangent-lobed stator pocket',fusion.FeatureOperations.CutFeatureOperation,body)
  body=self.extrude_all(self.circles('sm_stator_mount_plane',[('0 mm','0 mm','40.2 mm')],'Proximal crank chamber'),'36.5 mm','Proximal crank chamber',fusion.FeatureOperations.CutFeatureOperation,body)
  tool=self.extrude_all(self.circles('st_knee_chamber_y',[('0 mm','-lc_thigh_length','st_knee_chamber_radius')],'Knee chamber stock'),'st_knee_chamber_width','Knee chamber stock',fusion.FeatureOperations.NewBodyFeatureOperation);tool=g.round_edges(tool,'st_knee_chamber_fillet','Knee chamber corner radius');body=g.combine(body,[tool],fusion.FeatureOperations.CutFeatureOperation,'Open knee chamber')
  body=self.extrude_all(self.output_tail(),'st_output_tail_width','Swept pin tail clearance preserves bearing lands',fusion.FeatureOperations.CutFeatureOperation,body)
  xmin='-lc_crank_radius-st_rod_stem_clearance_radius';xmax='lc_crank_radius*cos(-(lc_knee_max+lc_crank_phase))+st_rod_stem_clearance_radius';zmin='-lc_crank_radius*sin(-(lc_knee_max+lc_crank_phase))-lc_thigh_length+12 mm';zmax='lc_crank_radius*sin(-(lc_knee_max+lc_crank_phase))-12 mm';tool=g.box('('+xmax+')-('+xmin+')','9 mm','('+zmax+')-('+zmin+')','(('+xmin+')+('+xmax+'))/2','70 mm','(('+zmin+')+('+zmax+'))/2','Equal-crank straight rod channel');return g.combine(body,[tool],fusion.FeatureOperations.CutFeatureOperation,'Straight pushrod channel')
 def connector_access(self,body):
  g=self.g;c=self.c;g.parameter('st_motor_port_angle',-23.8,'deg')
  for key,value in {'st_motor_port_face_y':54.4,'st_motor_port_rear_offset':37.6,'st_motor_port_width':18,'st_motor_port_axial_width':12,'st_motor_port_start_radius':30.1,'st_motor_port_radial_depth':21,'st_motor_cable_radius':5,'st_motor_cable_center_radius':46.6,'st_motor_cable_depth':27,'st_service_window_center_y':31.5,'st_service_window_height':50,'st_lower_window_center_y':39.6}.items():g.parameter(key,value,comment='Independent RS02 XT30 2+2 connector envelope or straight tool-access dimension.')
  plane=g.plane(c.xZConstructionPlane,'st_motor_port_face_y-st_motor_port_rear_offset-st_motor_port_axial_width/2','Two radial plug insertion planes');sk=c.sketches.add(plane);sk.name='Opposed plug insertion rectangles';sk.isComputeDeferred=True
  for sign in [-1,1]:
   points=[]
   for r,t in [('st_motor_port_start_radius','-st_motor_port_width/2'),('st_motor_port_start_radius+st_motor_port_radial_depth','-st_motor_port_width/2'),('st_motor_port_start_radius+st_motor_port_radial_depth','st_motor_port_width/2'),('st_motor_port_start_radius','st_motor_port_width/2')]:
    x=f'{sign}*(('+r+')*sin(st_motor_port_angle)+('+t+')*cos(st_motor_port_angle))';z=f'{-sign}*(('+r+')*cos(st_motor_port_angle)-('+t+')*sin(st_motor_port_angle))';p=g.skeleton_point(sk,x,z);g.point_dimensions(sk,p,x,z);points.append(p)
   for i,p in enumerate(points):sk.sketchCurves.sketchLines.addByTwoPoints(p,points[(i+1)%4])
  sk.isComputeDeferred=False;assert sk.profiles.count==2;body=self.extrude_all(sk,'st_motor_port_axial_width','Two open XT30 plug insertion windows',fusion.FeatureOperations.CutFeatureOperation,body)
  defs=[(f'{sign}*st_motor_cable_center_radius*sin(st_motor_port_angle)',f'{sign}*st_motor_cable_center_radius*cos(st_motor_port_angle)','st_motor_cable_radius')for sign in [-1,1]];body=self.extrude_all(self.circles('st_motor_port_face_y-st_motor_port_rear_offset+2 mm',defs,'Opposed cable bend channels'),'st_motor_cable_depth','Cable bend passages',fusion.FeatureOperations.CutFeatureOperation,body)
  for sign,width,height,radius,radial_start,depth,cy,name in [(-1,'st_motor_port_width','st_service_window_height','3 mm','30.1 mm','21 mm','st_service_window_center_y','Lower straight maintenance window'),(1,'st_motor_port_width','st_service_window_height','3 mm','30.1 mm','21 mm','st_service_window_center_y','Upper straight maintenance window'),(-1,'30 mm','36 mm','4 mm','29.6 mm','45 mm','st_lower_window_center_y','Open lower cable service window')]:
   angle='st_motor_port_angle'+(' + 180 deg'if sign<0 else'');inp=c.constructionPlanes.createInput();assert inp.setByAngle(c.yConstructionAxis,g.value(angle),c.xYConstructionPlane);angular=c.constructionPlanes.add(inp);angular.name=name+' radial orientation';plane=g.plane(angular,radial_start,name+' radial start');sk=g.rounded_rectangle(plane,height,width,radius,'0 mm',name,cy)
   theta=self.d.unitsManager.evaluateExpression(angle,'deg');r=g.mm(radial_start)/10;center=core.Point3D.create(r*math.sin(theta),g.mm(cy)/10,r*math.cos(theta));q=sk.modelToSketchSpace(center);assert abs(q.x-g.mm(cy)/10)<1e-6 and abs(q.y)<1e-6 and abs(q.z)<1e-6,(name,q.asArray())
   body=self.extrude_all(sk,depth,name,fusion.FeatureOperations.CutFeatureOperation,body)
  return body
 def continuous_exterior(self,body,fill_blank):
  g=self.g;roof=self.roof_stock('2 mm',False,'Continuous exterior inner limit');fill=g.combine(fill_blank,[roof],fusion.FeatureOperations.CutFeatureOperation,'Continuous exterior stock above the waist');window=g.box('150 mm','40 mm','74 mm','0 mm','90 mm','-(81/170)*lc_thigh_length','Exterior continuity region');fill=g.combine(fill,[window],fusion.FeatureOperations.IntersectFeatureOperation,'Local continuous exterior crown');return g.combine(body,[fill],fusion.FeatureOperations.JoinFeatureOperation,'Continuous thigh exterior without a roof depression')
 def split_mask(self):
  g=self.g;c=self.c
  for name,value in {'st_split_cup_y':50.3,'st_split_stem_y':67,'st_split_upper_z':'-(38/170)*lc_thigh_length','st_split_lower_z':'-(82/170)*lc_thigh_length','st_split_radius':3}.items():g.parameter(name,value)
  plane=g.plane(c.yZConstructionPlane,'-100 mm','Shared stepped shell split');sk=c.sketches.add(plane);sk.name='Cup-to-stem split with straight tool access';sk.isComputeDeferred=True;xs={};ys={};points=[]
  for x,y in [('-80 mm','-50 mm'),('-80 mm','st_split_cup_y'),('-st_split_upper_z','st_split_cup_y'),('-st_split_lower_z','st_split_stem_y'),('230 mm','st_split_stem_y'),('230 mm','-50 mm')]:
   p=g.skeleton_point(sk,x,y);g.point_dimensions(sk,p,None if x in xs else x,None if y in ys else y)
   if x in xs:sk.geometricConstraints.addVerticalPoints(xs[x],p)
   if y in ys:sk.geometricConstraints.addHorizontalPoints(ys[y],p)
   xs[x]=p;ys[y]=p;points.append(p)
  for i,p in enumerate(points):sk.sketchCurves.sketchLines.addByTwoPoints(p,points[(i+1)%len(points)])
  sk.isComputeDeferred=False;assert sk.profiles.count==1;body=g.extrude(sk,'200 mm','Shared stepped split stock').bodies.item(0);body=self.fillet_selected(body,'st_split_radius','Accessible split transition radii',lambda e:abs(e.boundingBox.maxPoint.x-e.boundingBox.minPoint.x-20)<1e-6 and abs(e.boundingBox.maxPoint.y-e.boundingBox.minPoint.y)<1e-6 and abs(e.boundingBox.maxPoint.z-e.boundingBox.minPoint.z)<1e-6)
  inp=c.constructionPlanes.createInput();assert inp.setByAngle(c.yConstructionAxis,g.value('st_motor_port_angle'),c.yZConstructionPlane);p=c.constructionPlanes.add(inp);p.name='Cup seam through the opposed connector centers';sk=g.rectangle(p,'700 mm','500 mm','0 mm','0 mm','Forward cup sector');tool=g.extrude(sk,'300 mm','Forward cup split region').bodies.item(0);body=g.combine(body,[tool],fusion.FeatureOperations.CutFeatureOperation,'Shared split keeps a connected inboard cup');body.name='Construction shared thigh split';body.isLightBulbOn=False;return body
 def bearing_stop(self,body,outer):
  g=self.g;c=self.c
  for name,value in {'st_stop_radial_gap':.3,'st_stop_axial_gap':.3,'st_stop_recess_depth':1,'st_stop_race_land_width':1.3,'st_stop_shaft_relief_radius':8.2,'st_inner_stop_boss_radius':11.2,'st_axle_nominal_diameter':12,'st_axle_diametral_allowance':.2,'st_outer_stop_base_y':91,'st_outer_stop_base_radius':16,'st_outer_stop_top_y':'st_cap_y+3 mm'}.items():g.parameter(name,value)
  for name,value in {'st_axle_fit_radius':'(st_axle_nominal_diameter+st_axle_diametral_allowance)/2','st_stop_outer_radius':'lc_bearing_od/2-st_stop_radial_gap','st_stop_recess_radius':'st_stop_outer_radius-st_stop_race_land_width','st_inner_stop_end':'lc_bearing_inner_y-st_stop_axial_gap','st_outer_stop_start':'lc_bearing_outer_y+lc_bearing_width+st_stop_axial_gap'}.items():g.parameter(name,value)
  if outer:profile=[('st_stop_outer_radius','st_outer_stop_start'),('st_stop_outer_radius','st_outer_stop_base_y'),('st_outer_stop_base_radius','st_outer_stop_base_y'),('st_outer_stop_base_radius','st_outer_stop_top_y'),('st_axle_fit_radius','st_outer_stop_top_y'),('st_axle_fit_radius','st_outer_stop_base_y'),('st_stop_shaft_relief_radius','st_outer_stop_base_y'),('st_stop_shaft_relief_radius','st_outer_stop_start+st_stop_recess_depth'),('st_stop_recess_radius','st_outer_stop_start+st_stop_recess_depth'),('st_stop_recess_radius','st_outer_stop_start')]
  else:profile=[('st_stop_outer_radius','st_knee_chamber_y'),('st_stop_outer_radius','st_inner_stop_end'),('st_stop_recess_radius','st_inner_stop_end'),('st_stop_recess_radius','st_inner_stop_end-st_stop_recess_depth'),('st_inner_stop_boss_radius','st_inner_stop_end-st_stop_recess_depth'),('st_inner_stop_boss_radius','st_inner_stop_end-st_stop_axial_gap'),('st_axle_fit_radius','st_inner_stop_end-st_stop_axial_gap'),('st_axle_fit_radius','st_knee_chamber_y')]
  plane=g.plane(c.xYConstructionPlane,'-lc_thigh_length','Knee shaft axis');sk=c.sketches.add(plane);sk.name=('Outer'if outer else'Inner')+' integral bearing backup section';sk.isComputeDeferred=True;xs={};ys={};points=[]
  for x,y in profile:
   p=g.skeleton_point(sk,x,y);g.point_dimensions(sk,p,None if x in xs else x,None if y in ys else y)
   if x in xs:sk.geometricConstraints.addVerticalPoints(xs[x],p)
   if y in ys:sk.geometricConstraints.addHorizontalPoints(ys[y],p)
   xs[x]=p;ys[y]=p;points.append(p)
  for i,p in enumerate(points):sk.sketchCurves.sketchLines.addByTwoPoints(p,points[(i+1)%len(points)])
  axis=sk.sketchCurves.sketchLines.addByTwoPoints(sk.originPoint,core.Point3D.create(0,1,0));axis.isConstruction=True;sk.geometricConstraints.addVertical(axis);sk.sketchDimensions.addDistanceDimension(axis.startSketchPoint,axis.endSketchPoint,fusion.DimensionOrientations.AlignedDimensionOrientation,core.Point3D.create(.5,.5,0)).parameter.expression='10 mm';sk.isComputeDeferred=False;assert sk.profiles.count==1;inp=c.features.revolveFeatures.createInput(sk.profiles.item(0),axis,fusion.FeatureOperations.JoinFeatureOperation);inp.setAngleExtent(False,g.value('360 deg'));f=c.features.revolveFeatures.add(inp);f.name='Integral bearing backup and axle boss';body=f.bodies.item(0);sk.isVisible=False
  if outer:
   body=self.crown_revolve(body)
  return body
 def crown_revolve(self,body):
  g=self.g;c=self.c
  for name,value in {'st_crown_root_radius':21,'st_crown_middle_radius':20}.items():g.parameter(name,value)
  g.parameter('st_crown_middle_parameter',.28533935033142227,'',comment='Source three-station crown interpolation parameter; the meridian passes through all three independently dimensioned stations.')
  plane=g.plane(c.xYConstructionPlane,'-lc_thigh_length','Knee crown meridian datum');sk=c.sketches.add(plane);sk.name='Three-station quadratic knee crown meridian';sk.isComputeDeferred=True;t='st_crown_middle_parameter';den='(2*'+t+'*(1-'+t+'))';stations=[('st_crown_root_radius','st_cap_y-2 mm'),('st_crown_middle_radius','st_cap_y'),('st_outer_stop_base_radius','st_outer_stop_top_y')];control=['(('+stations[1][a]+')-(1-'+t+')^2*('+stations[0][a]+')-'+t+'^2*('+stations[2][a]+'))/'+den for a in [0,1]];expr=[stations[0],tuple('('+stations[0][a]+')/3+2*('+control[a]+')/3'for a in[0,1]),tuple('('+stations[2][a]+')/3+2*('+control[a]+')/3'for a in[0,1]),stations[2]];points=[]
  for x,y in expr:
   p=g.skeleton_point(sk,x,y);g.point_dimensions(sk,p,x,y);points.append(p)
  native_nonuniform_cubic(sk,points,[]);axis_points=[]
  for endpoint in [points[0],points[-1]]:
   p=sk.sketchPoints.add(core.Point3D.create(0,endpoint.geometry.y,0));sk.geometricConstraints.addVerticalPoints(sk.originPoint,p);sk.geometricConstraints.addHorizontalPoints(endpoint,p);axis_points.append(p)
  for a,b in [(axis_points[0],points[0]),(points[-1],axis_points[1]),(axis_points[1],axis_points[0])]:sk.sketchCurves.sketchLines.addByTwoPoints(a,b)
  axis=sk.sketchCurves.sketchLines.addByTwoPoints(sk.originPoint,core.Point3D.create(0,1,0));axis.isConstruction=True;sk.geometricConstraints.addVertical(axis);sk.sketchDimensions.addDistanceDimension(axis.startSketchPoint,axis.endSketchPoint,fusion.DimensionOrientations.AlignedDimensionOrientation,core.Point3D.create(.5,.5,0)).parameter.expression='10 mm';sk.isComputeDeferred=False;assert sk.profiles.count==1;inp=c.features.revolveFeatures.createInput(sk.profiles.item(0),axis,fusion.FeatureOperations.JoinFeatureOperation);inp.participantBodies=[body];inp.setAngleExtent(False,g.value('360 deg'));f=c.features.revolveFeatures.add(inp);f.name='Revolved three-station integral knee crown';sk.isVisible=False;return f.bodies.item(0)
 def shell_hardware(self,body,outer):
  g=self.g;c=self.c
  for name,value in {'st_clamp_sleeve_od':8,'st_clamp_sleeve_diametral_allowance':.2,'st_clamp_sleeve_length':18,'st_clamp_sleeve_start_y':58,'st_clamp_washer_od':12,'st_clamp_washer_diametral_allowance':.4,'st_knee_washer_od':15,'st_knee_washer_diametral_allowance':.4,'st_knee_washer_inner_floor_y':49.4,'st_knee_washer_outer_floor_y':94}.items():g.parameter(name,value,comment='Nominal standard hardware and independent unqualified process allowances.')
  for name,value in {'st_clamp_sleeve_radius':'(st_clamp_sleeve_od+st_clamp_sleeve_diametral_allowance)/2','st_clamp_washer_access_radius':'(st_clamp_washer_od+st_clamp_washer_diametral_allowance)/2','st_clamp_outer_floor_y':'st_clamp_sleeve_start_y+st_clamp_sleeve_length','st_knee_washer_access_radius':'(st_knee_washer_od+st_knee_washer_diametral_allowance)/2'}.items():g.parameter(name,value)
  def cut(y,depth,defs,name):
   nonlocal body
   body=self.extrude_all(self.circles(y,defs,name),depth,name,fusion.FeatureOperations.CutFeatureOperation,body)
  cut('0 mm','140 mm',[('0 mm','-lc_thigh_length','st_axle_fit_radius')],'Removable twelve millimeter knee axle fit')
  if outer:cut('94.3 mm','12 mm',[('0 mm','-lc_thigh_length','9.2 mm')],'Open outer axle socket access')
  cut('st_knee_washer_outer_floor_y'if outer else'st_knee_washer_inner_floor_y-8 mm','16 mm'if outer else'8 mm',[('0 mm','-lc_thigh_length','st_knee_washer_access_radius')],'Standard M5 large washer seating floor')
  clamps=lambda r:[('st_rear_clamp_x','st_rear_clamp_z',r),('st_front_clamp_x','st_front_clamp_z',r)]
  cut('st_clamp_sleeve_start_y','st_clamp_sleeve_length',clamps('st_clamp_sleeve_radius'),'Two hard compression sleeve fits')
  cut('st_clamp_outer_floor_y'if outer else'st_clamp_sleeve_start_y-15 mm','40 mm'if outer else'15 mm',clamps('st_clamp_washer_access_radius'),'Open standard M4 washer and socket access')
  if outer:
   sketches=[self.circles(y,[('0 mm','-lc_thigh_length',r)],'Outer knee socket entry')for y,r in [('96.5 mm','9.2 mm'),('97 mm','9.7 mm')]];inp=c.features.loftFeatures.createInput(fusion.FeatureOperations.CutFeatureOperation)
  else:
   cut('43 mm','5.7 mm',[('-45 mm','-38 mm','5.5 mm')],'Fixed shoulder screw edge clearance');sketches=[self.circles(y,[('0 mm','0 mm',r)],'Motor bore lead-in')for y,r in [('st_root_y','st_case_fit_radius+.6 mm'),('st_root_y+1 mm','st_case_fit_radius')]];inp=c.features.loftFeatures.createInput(fusion.FeatureOperations.CutFeatureOperation)
  inp.isSolid=True
  for sk in sketches:inp.loftSections.add(sk.profiles.item(0))
  f=c.features.loftFeatures.add(inp);f.name='Accessible axial entry chamfer';body=f.bodies.item(0)
  for sk in sketches:sk.isVisible=False
  return body
