"""Native sensor cradle from two feet, two rails, a crossweb and four bosses.

All dimensions drive sketches or features. Hardware fits stay independent of
body size. This constructor needs export, edit and assembly audits before use.
"""
class SensorSaddleIntent:
 def __init__(self,geometry):
  self.g=geometry;self.c=geometry.component

 def parameters(self):
  dims={'saddle_x':121,'saddle_foot_spacing':48,'saddle_foot_width':22,
        'saddle_foot_depth':16,'saddle_foot_height':17.2,'saddle_frame_top_z':42.8,
        'saddle_foot_edge_radius':1,'saddle_split_z':60,'saddle_rail_length':88,
        'saddle_rail_width':6,'saddle_rail_height':7,'saddle_rail_center_x':130,
        'saddle_rail_half_spacing':19,'saddle_web_length':16,'saddle_web_width':44,
        'saddle_web_height':5,'saddle_web_bottom_z':53,'saddle_boss_radius':7,
        'saddle_boss_bottom_z':50,'saddle_hood_hole_radius':1.7,
        'saddle_hood_nut_af':5.8,'saddle_hood_nut_bottom_z':48,
        'saddle_hood_nut_depth':8.4,'saddle_root_hole_radius':2.2,
        'saddle_root_counterbore_radius':5,'saddle_root_counterbore_z':53.2}
  for name,value in dims.items():self.g.parameter(name,value,comment='Sensor cradle design or independent common-fastener fit dimension')
  for i,(x,y) in enumerate([(92,-25),(92,25),(164,-18),(164,18)]):
   self.g.parameter('saddle_hood_x_'+str(i),x)
   self.g.parameter('saddle_hood_y_'+str(i),y)
  values={'saddle_hood_nominal_diameter':3,'saddle_root_nominal_diameter':4,'saddle_fastener_diametral_clearance':.4,'saddle_hood_nut_nominal_af':5.5,'saddle_nut_af_allowance':.3,'saddle_root_head_diameter':7,'saddle_driver_diametral_clearance':3}
  for name,value in values.items():self.g.parameter(name,value,comment='Independent selected hardware interface. Process compensation and physical fit are unqualified.')
  expressions={'saddle_foot_height':'saddle_split_z-saddle_frame_top_z','saddle_rail_center_x':'saddle_x+9 mm','saddle_web_bottom_z':'saddle_split_z-7 mm','saddle_boss_bottom_z':'saddle_split_z-10 mm','saddle_hood_nut_bottom_z':'saddle_split_z-12 mm','saddle_root_counterbore_z':'saddle_frame_top_z+10.4 mm','saddle_hood_hole_radius':'(saddle_hood_nominal_diameter+saddle_fastener_diametral_clearance)/2','saddle_root_hole_radius':'(saddle_root_nominal_diameter+saddle_fastener_diametral_clearance)/2','saddle_hood_nut_af':'saddle_hood_nut_nominal_af+saddle_nut_af_allowance','saddle_root_counterbore_radius':'(saddle_root_head_diameter+saddle_driver_diametral_clearance)/2'}
  for i in range(4):expressions['saddle_hood_x_'+str(i)]='saddle_x'+('-29 mm' if i<2 else '+43 mm')
  for name,expression in expressions.items():self.g.design.userParameters.itemByName(name).expression=expression

 def circles(self,z,centers,radius,name):
  g=self.g;c=self.c;sk=c.sketches.add(g.plane(c.xYConstructionPlane,z,name+' datum'));sk.name=name
  points=[g.skeleton_point(sk,x,y) for x,y in centers];columns={}
  for point,(x,y) in zip(points,centers):
   column=round(g.mm(x),8);g.point_dimensions(sk,point,None if column in columns else x,y)
   if column in columns:sk.geometricConstraints.addVerticalPoints(columns[column],point)
   else:columns[column]=point
  for point in points:
   circle=sk.sketchCurves.sketchCircles.addByCenterRadius(point.geometry,g.mm(radius)*.1);sk.geometricConstraints.addCoincident(circle.centerSketchPoint,point)
   sk.sketchDimensions.addRadialDimension(circle,core.Point3D.create(point.geometry.x+.4,point.geometry.y+.4,0)).parameter.expression=radius
  assert sk.profiles.count==len(centers),(name,sk.profiles.count)
  return sk

 def hexagons(self,z,centers,af,name):
  g=self.g;c=self.c;sk=c.sketches.add(g.plane(c.xYConstructionPlane,z,name+' datum'));sk.name=name
  polygons=[];coordinates=[]
  for x,y in centers:
   polygon=[]
   for i in range(6):
    angle=str(i*60)+' deg';xe='('+x+') + ('+af+')/sqrt(3)*cos('+angle+')';ye='('+y+') + ('+af+')/sqrt(3)*sin('+angle+')';point=g.skeleton_point(sk,xe,ye);polygon.append(point);coordinates.append((point,xe,ye))
   polygons.append(polygon)
  xs={};ys={}
  for point,x,y in coordinates:
   xv=round(g.mm(x),8);yv=round(g.mm(y),8);g.point_dimensions(sk,point,None if xv in xs else x,None if yv in ys else y)
   if xv in xs:sk.geometricConstraints.addVerticalPoints(xs[xv],point)
   else:xs[xv]=point
   if yv in ys:sk.geometricConstraints.addHorizontalPoints(ys[yv],point)
   else:ys[yv]=point
  for points in polygons:
   for i in range(6):sk.sketchCurves.sketchLines.addByTwoPoints(points[i],points[(i+1)%6])
  assert sk.profiles.count==len(centers)
  return sk

 def build(self):
  g=self.g;self.parameters();stock=[]
  for sign,label in [('-','Left'),('','Right')]:
   foot=g.box('saddle_foot_width','saddle_foot_depth','saddle_foot_height','saddle_x',sign+'saddle_foot_spacing/2','saddle_frame_top_z+saddle_foot_height/2',label+' load foot')
   stock.append(g.round_edges(foot,'saddle_foot_edge_radius',label+' foot edge radii'))
   stock.append(g.box('saddle_rail_length','saddle_rail_width','saddle_rail_height','saddle_rail_center_x',sign+'saddle_rail_half_spacing','saddle_split_z-saddle_rail_height/2',label+' connecting rail'))
  stock.append(g.box('saddle_web_length','saddle_web_width','saddle_web_height','saddle_x','0 mm','saddle_web_bottom_z+saddle_web_height/2','Transverse connecting web'))
  centers=[('saddle_hood_x_'+str(i),'saddle_hood_y_'+str(i)) for i in range(4)]
  sk=self.circles('saddle_boss_bottom_z',centers,'saddle_boss_radius','Four hood clamping bosses')
  g.extrude_all(sk,'saddle_split_z-saddle_boss_bottom_z','Hood clamping bosses',fusion.FeatureOperations.NewBodyFeatureOperation)
  stock=list(self.c.bRepBodies)
  body=g.combine(stock[0],stock[1:],fusion.FeatureOperations.JoinFeatureOperation,'Connected structural cradle')
  sk=self.circles('saddle_hood_nut_bottom_z',centers,'saddle_hood_hole_radius','M3 hood screw clearance')
  g.extrude_all(sk,'20 mm','Four M3 clearance bores',fusion.FeatureOperations.CutFeatureOperation,[body])
  sk=self.hexagons('saddle_hood_nut_bottom_z',centers,'saddle_hood_nut_af','Open M3 nut pockets')
  g.extrude_all(sk,'saddle_hood_nut_depth','Four accessible nut pockets',fusion.FeatureOperations.CutFeatureOperation,[body])
  roots=[('saddle_x',s+'saddle_foot_spacing/2') for s in ['-','']]
  sk=self.circles('30 mm',roots,'saddle_root_hole_radius','M4 root screw clearances')
  g.extrude_all(sk,'35 mm','Through root holes',fusion.FeatureOperations.CutFeatureOperation,[body])
  sk=self.circles('saddle_root_counterbore_z',roots,'saddle_root_counterbore_radius','Root screw and driver pockets')
  g.extrude_all(sk,'20 mm','Open root counterbores',fusion.FeatureOperations.CutFeatureOperation,[body])
  assert self.c.bRepBodies.count==1
  return self.c.bRepBodies.item(0)
