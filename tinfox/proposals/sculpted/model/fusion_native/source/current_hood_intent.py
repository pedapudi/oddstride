"""Current low sensor hood: eight native sections and an integrated native face."""
class CurrentHoodIntent:
 def __init__(self,g):self.g=g;self.c=g.component;self.d=g.design
 def parameters(self):
  g=self.g
  for name,value in {'hood_sensor_x':121,'hood_sensor_seat_z':80,'hood_wall':4,'hood_lower_opening_overlap':3,'hood_seat_radius':32,'hood_seat_thickness':5,'hood_cable_radius':9,'hood_boss_radius':6,'hood_driver_radius':3.25,'hood_driver_floor_z':73}.items():g.parameter(name,value,comment='Low sensor hood dimension. Selected sensor and fastener interfaces do not scale with robot size.')
  stations=[(76,32,58,66),(92,78,58,77),(121,80,58,80),(150,70,58,78),(185,54,56,72),(216,38,40,59),(240,150,31,44),(248,178,32,43)]
  for i,(x,w,lo,hi) in enumerate(stations):
   for suffix,value in [('x',x),('width',w),('lower_z',lo),('upper_z',hi)]:g.parameter('hood_station_'+str(i+1)+'_'+suffix,value,comment='Editable hood crosssection; endpoint profiles are interface datums.')
  g.design.userParameters.itemByName('hood_station_3_x').expression='hood_sensor_x';g.design.userParameters.itemByName('hood_station_3_upper_z').expression='hood_sensor_seat_z'
 def copy(self,body,name):
  objects=core.ObjectCollection.create();objects.add(body);f=self.c.features.copyPasteBodies.add(objects);f.name=name;assert f.isParametric and f.bodies.count==1;return f.bodies.item(0)
 def cylinder(self,x,y,z,radius,height,name):
  g=self.g;sk=self.c.sketches.add(g.plane(self.c.xYConstructionPlane,z,name+' datum'));sk.name=name+' section';p=g.skeleton_point(sk,x,y);g.point_dimensions(sk,p,x,y);circle=sk.sketchCurves.sketchCircles.addByCenterRadius(p.geometry,g.mm(radius)*.1);sk.geometricConstraints.addCoincident(circle.centerSketchPoint,p);sk.sketchDimensions.addRadialDimension(circle,core.Point3D.create(p.geometry.x+.4,p.geometry.y+.4,0)).parameter.expression=radius;return g.extrude(sk,height,name).bodies.item(0)
 def build(self,face):
  self.parameters();g=self.g;c=self.c;outer=[];inner=[]
  for i in range(1,9):
   prefix='hood_station_'+str(i)+'_';x=prefix+'x';w=prefix+'width';lo=prefix+'lower_z';hi=prefix+'upper_z';outer.append(g.yz_contour(x,w,'('+hi+')-('+lo+')','3.8 mm' if i==1 else '4 mm','(('+lo+')+('+hi+'))/2','Hood section '+str(i)));inner.append(g.yz_contour(x,'('+w+')-2*hood_wall','('+hi+')-hood_wall-(('+lo+')-hood_lower_opening_overlap)','2 mm','(('+lo+')-hood_lower_opening_overlap+('+hi+')-hood_wall)/2','Inner hood section '+str(i)))
  body=g.loft(outer,'Eight-section sensor hood envelope');masks=[self.copy(body,'Clamping boss envelope '+str(i+1)) for i in range(4)];inside=g.loft(inner,'Eight-section hollow interior');body=g.combine(body,[inside],fusion.FeatureOperations.CutFeatureOperation,'Hollow removable sensor hood');body=g.combine(body,[self.copy(face,'Shared native compound sensor face')],fusion.FeatureOperations.JoinFeatureOperation,'Continuous hood and compound face')
  seat=self.cylinder('hood_sensor_x','0 mm','hood_sensor_seat_z-hood_seat_thickness','hood_seat_radius','hood_seat_thickness','Integral lidar mounting seat');body=g.combine(body,[seat],fusion.FeatureOperations.JoinFeatureOperation,'Join lidar mounting seat');tool=g.box('400 mm','300 mm','100 mm','160 mm','0 mm','hood_sensor_seat_z+50 mm','Flat sensor seat tool');body=g.combine(body,[tool],fusion.FeatureOperations.CutFeatureOperation,'Level sensor mounting surface');tool=self.cylinder('hood_sensor_x','0 mm','40 mm','hood_cable_radius','60 mm','Shared cable opening');body=g.combine(body,[tool],fusion.FeatureOperations.CutFeatureOperation,'Open lidar cable route')
  bosses=[]
  for i,mask in enumerate(masks):
   tool=self.cylinder('saddle_hood_x_'+str(i),'saddle_hood_y_'+str(i),'saddle_split_z','hood_boss_radius','20 mm','Hood clamping boss '+str(i+1));bosses.append(g.combine(tool,[mask],fusion.FeatureOperations.IntersectFeatureOperation,'Conform boss '+str(i+1)+' to hood envelope'))
  body=g.combine(body,bosses,fusion.FeatureOperations.JoinFeatureOperation,'Four integral hood screw bosses');patterns=SensorSaddleIntent(g);centers=[('saddle_hood_x_'+str(i),'saddle_hood_y_'+str(i)) for i in range(4)];holes=patterns.circles('50 mm',centers,'saddle_hood_hole_radius','Shared M3 hood clearance pattern');g.extrude_all(holes,'40 mm','Four through hood fastener holes',fusion.FeatureOperations.CutFeatureOperation,[body]);drivers=patterns.circles('hood_driver_floor_z',centers,'hood_driver_radius','Common hood screw access pattern');g.extrude_all(drivers,'30 mm','Four open driver counterbores',fusion.FeatureOperations.CutFeatureOperation,[body]);assert c.bRepBodies.count==1;return c.bRepBodies.item(0)
