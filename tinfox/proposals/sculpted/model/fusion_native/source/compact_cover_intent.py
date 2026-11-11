"""Native central cover from an extruded rim, four roof stations and cuffs.

The central span is constant in the frozen design. Nose/tail lofts and sampled
shoulder sweeps lie outside this part and are deliberately not reconstructed.
"""
class CompactCoverIntent:
 def __init__(self,g):self.g=g;self.c=g.component;self.d=g.design
 def parameters(self):
  values={'cover_half_length':125.4,'cover_half_width':111.2,'cover_roof_z':49.5,'cover_floor_z':-48,'cover_top_bevel':18,'cover_bottom_bevel':17,'cover_corner_radius':9,'cover_wall':2.8,'cover_lower_edge_z':-10,'cover_hip_x':185,'cover_roll_y':68,'cover_boss_x':112,'cover_boss_y':106.25,'cover_boss_z':22,'cover_boss_width':9,'cover_boss_depth':7.5,'cover_boss_height':14,'cover_boss_radius':.5,'cover_fastener_radius':1.7}
  for name,value in values.items():self.g.parameter(name,value,comment='Central enclosure family dimension; motor and fastener fits remain independent.')
 def box(self,w,depth,h,x,y,z,name,radius=None):
  body=self.g.box(w,depth,h,x,y,z,name)
  return self.g.round_edges(body,radius,name+' edge radii') if radius else body
 def reflected(self,body,plane,name):
  before={b.entityToken for b in self.c.bRepBodies};objects=core.ObjectCollection.create();objects.add(body);inp=self.c.features.mirrorFeatures.createInput(objects,plane);inp.isCombine=False;f=self.c.features.mirrorFeatures.add(inp);f.name=name;new=[b for b in self.c.bRepBodies if b.entityToken not in before];assert len(new)==1,(name,len(new));return new[0]
 def four(self,body,name):
  side=self.reflected(body,self.c.xZConstructionPlane,name+' opposite side');front=self.reflected(body,self.c.yZConstructionPlane,name+' opposite end');diagonal=self.reflected(side,self.c.yZConstructionPlane,name+' diagonal');return [body,side,front,diagonal]
 def cut(self,body,tools,name):return self.g.combine(body,tools,fusion.FeatureOperations.CutFeatureOperation,name)
 def join(self,body,tools,name):return self.g.combine(body,tools,fusion.FeatureOperations.JoinFeatureOperation,name)
 def cylinder(self,axis,start,u,v,radius,length,name):
  g=self.g;c=self.c
  if axis=='X':plane=g.plane(c.yZConstructionPlane,start,name+' datum');a,b='-('+v+')',u
  elif axis=='Y':plane=g.plane(c.xZConstructionPlane,start,name+' datum');a,b=u,'-('+v+')'
  else:plane=g.plane(c.xYConstructionPlane,start,name+' datum');a,b=u,v
  sk=c.sketches.add(plane);sk.name=name+' circular section';point=g.skeleton_point(sk,a,b);g.point_dimensions(sk,point,a,b);circle=sk.sketchCurves.sketchCircles.addByCenterRadius(point.geometry,g.mm(radius)/10);sk.geometricConstraints.addCoincident(circle.centerSketchPoint,point);sk.sketchDimensions.addRadialDimension(circle,core.Point3D.create(point.geometry.x+.4,point.geometry.y+.4,0)).parameter.expression=radius;return g.extrude(sk,length,name).bodies.item(0)
 def turned_x(self,stations,center_y,angle,name):
  g=self.g;sk=self.c.sketches.add(self.c.xYConstructionPlane);sk.name=name+' section';sk.isComputeDeferred=True;points=[];xs={};ys={}
  for x,r in stations:
   y='('+center_y+')+('+r+')';p=g.skeleton_point(sk,x,y);g.point_dimensions(sk,p,None if x in xs else x,None if y in ys else y)
   if x in xs:sk.geometricConstraints.addVerticalPoints(xs[x],p)
   if y in ys:sk.geometricConstraints.addHorizontalPoints(ys[y],p)
   xs[x]=p;ys[y]=p;points.append(p)
  for i,p in enumerate(points):sk.sketchCurves.sketchLines.addByTwoPoints(p,points[(i+1)%len(points)])
  sk.isComputeDeferred=False;assert sk.profiles.count==1,(name,sk.profiles.count);datum=g.plane(self.c.xZConstructionPlane,center_y,name+' axis offset');axis_input=self.c.constructionAxes.createInput();assert axis_input.setByTwoPlanes(datum,self.c.xYConstructionPlane);axis=self.c.constructionAxes.add(axis_input);axis.name=name+' axis';direction=axis.geometry.direction.x;assert abs(abs(direction)-1)<1e-8;inp=self.c.features.revolveFeatures.createInput(sk.profiles.item(0),axis,fusion.FeatureOperations.NewBodyFeatureOperation);inp.setAngleExtent(False,g.value(angle if direction>0 else '-('+angle+')'));f=self.c.features.revolveFeatures.add(inp);f.name=name;sk.isLightBulbOn=False;datum.isLightBulbOn=False;axis.isLightBulbOn=False;return f.bodies.item(0)

 def base(self,include_window=False):
  self.parameters();g=self.g;c=self.c;plane=g.plane(c.yZConstructionPlane,'-cover_half_length','Cover end datum');outer=g.rounded_octagon(plane,'cover_half_width','cover_roof_z','cover_floor_z','cover_top_bevel','cover_bottom_bevel','cover_corner_radius','Transverse structural envelope');body=g.extrude(outer,'2*cover_half_length','Constant central body span').bodies.item(0)
  plane=g.plane(c.yZConstructionPlane,'-cover_half_length-1 mm','Inner wall opening datum');inner=g.rounded_octagon(plane,'cover_half_width-cover_wall','cover_roof_z-cover_wall','cover_floor_z+cover_wall','cover_top_bevel+cover_wall*(sqrt(2)-2)','cover_bottom_bevel+cover_wall*(sqrt(2)-2)','cover_corner_radius-cover_wall','Normal-offset inner wall');g.extrude(inner,'2*cover_half_length+2 mm','Uniform central shell wall',fusion.FeatureOperations.CutFeatureOperation,[body]);body=c.bRepBodies.item(0)
  tool=self.box('2*cover_half_length+10 mm','2*cover_half_width+10 mm','100 mm','0 mm','0 mm','cover_lower_edge_z-50 mm','Open underside tool');body=self.cut(body,[tool],'Open underside for assembly and printing')
  if include_window:
   plane=g.plane(c.xYConstructionPlane,'cover_roof_z-.6 mm','Status display recess datum');sk=g.rounded_rectangle(plane,'48 mm','28 mm','4 mm','0 mm','Original display recess','20 mm');g.extrude(sk,'1 mm','Original display recess',fusion.FeatureOperations.CutFeatureOperation,[body])
  rib=self.box('2.4 mm','170 mm','5.5 mm','28 mm','0 mm','46.75 mm','Roof stiffening rib');body=self.join(body,[rib,self.reflected(rib,c.yZConstructionPlane,'Second roof stiffener')],'Integral roof ribs')
  stations=[('cover_hip_x-114.7 mm','0 mm'),('cover_hip_x-114.7 mm','41.25 mm'),('cover_hip_x-73.3 mm','41.25 mm'),('cover_hip_x-73.3 mm','42 mm'),('cover_hip_x-66.3 mm','42 mm'),('cover_hip_x-66.3 mm','41.25 mm'),('cover_hip_x-65.3 mm','41.25 mm'),('cover_hip_x-65.3 mm','38 mm'),('cover_hip_x-51.5 mm','38 mm'),('cover_hip_x-51.5 mm','0 mm')]
  tool=self.turned_x(stations,'cover_roll_y','360 deg','Stepped roll cartridge clearance');body=self.cut(body,self.four(tool,'Roll cartridge clearance'),'Four fixed motor clearances')
  # Ear and longitudinal channel tools have zero intersection here; the local
  # semantic replay records these omissions before any native authoring.
  boss=self.box('cover_boss_width','cover_boss_depth','cover_boss_height','cover_boss_x','cover_boss_y','cover_boss_z','Cover attachment boss','cover_boss_radius');body=self.join(body,self.four(boss,'Cover boss'),'Four integral mounting bosses')
  tool=self.box('9.4 mm','5.4 mm','80 mm','cover_boss_x','103.5 mm','-13.3 mm','Open mounting boss channel','.3 mm');body=self.cut(body,self.four(tool,'Boss channel'),'Four downward-open boss channels')
  tool=self.box('10 mm','4 mm','100 mm','cover_boss_x','101.5 mm','-5 mm','Inner boss release tool');body=self.cut(body,self.four(tool,'Inner boss release'),'Open inner mounting channels')
  tool=self.cylinder('Y','101 mm','cover_boss_x','cover_boss_z','cover_fastener_radius','12 mm','Lateral cover screw hole');body=self.cut(body,self.four(tool,'Cover screw hole'),'Four accessible M3 cover holes')
  tool=self.cylinder('X','cover_hip_x-73.3 mm','cover_roll_y','0 mm','42 mm','7 mm','Boss to cartridge clearance');body=self.cut(body,self.four(tool,'Final cartridge relief'),'Keep mounting bosses clear of cartridges')
  tool=self.box('32 mm','260 mm','100 mm','cover_half_length','0 mm','-35.8 mm','Lower end service relief','2 mm');body=self.cut(body,[tool,self.reflected(tool,c.yZConstructionPlane,'Opposite lower end relief')],'Open lower end service paths');return body
 def roof(self,body):
  g=self.g;c=self.c;outer=[];inner=[]
  for i,(z,w,depth,radius) in enumerate([('cover_roof_z-2.7 mm','2*cover_half_length-1.3 mm','2*cover_half_width-21.4 mm','19 mm'),('cover_roof_z+.5 mm','2*cover_half_length-4.8 mm','2*cover_half_width-27.4 mm','23 mm'),('cover_roof_z+4.5 mm','2*cover_half_length-20.8 mm','2*cover_half_width-48.4 mm','32 mm'),('cover_roof_z+6 mm','2*cover_half_length-38.8 mm','2*cover_half_width-77.4 mm','36 mm')]):
   outer.append(g.rounded_rectangle(g.plane(c.xYConstructionPlane,z,'Roof section '+str(i+1)),w,depth,radius,'0 mm','Roof outline '+str(i+1)))
   inner.append(g.rounded_rectangle(g.plane(c.xYConstructionPlane,'('+z+')-3 mm','Inner roof section '+str(i+1)),'('+w+')-6 mm','('+depth+')-6 mm','('+radius+')-3 mm','0 mm','Inner roof outline '+str(i+1)))
  outside=g.loft(outer,'Four-station curved roof');inside=g.loft(inner,'Four-station inner roof');dome=self.cut(outside,[inside],'Hollow curved roof');body=self.join(body,[dome],'Continuous raised roof')
  plane=g.plane(c.xYConstructionPlane,'45.8 mm','Open old roof datum');sk=g.rounded_rectangle(plane,'207 mm','139 mm','32 mm','0 mm','Open old roof outline');tool=g.extrude(sk,'4 mm','Old double wall removal tool').bodies.item(0);body=self.cut(body,[tool],'Single roof wall')
  tool=self.box('50 mm','30 mm','20 mm','20 mm','0 mm','55 mm','Display aperture tool','4 mm');body=self.cut(body,[tool],'Rounded display opening')
  # The current roof-seat replacement removes the entire old lidar mount.
  # It is therefore built directly by SensorBodyDeltaIntent below.
  stations=[('118.8 mm','48 mm'),('128 mm','48 mm'),('132 mm','43 mm'),('135 mm','40.5 mm'),('135 mm','37.5 mm'),('132 mm','37.5 mm'),('128 mm','42.5 mm'),('118.8 mm','42.5 mm')]
  cuff=self.turned_x(stations,'cover_roll_y','180 deg','Upper half roll cuff');tools=self.four(cuff,'Shoulder cuff');root=self.box('9 mm','32 mm','5 mm','121 mm','cover_roll_y','46.5 mm','Cuff structural root','1 mm');tools+=self.four(root,'Cuff root');body=self.join(body,tools,'Four integral upper shoulder cuffs')
  tool=self.box('14 mm','184 mm','4.6 mm','121 mm','0 mm','41.8 mm','Crossmember underside clearance');body=self.cut(body,[tool,self.reflected(tool,c.yZConstructionPlane,'Opposite crossmember underside clearance')],'Crossmember to cuff clearance')
  for z,label in [('24 mm','Upper')]:
   tool=self.box('14 mm','16 mm','14 mm','125.5 mm','cover_roll_y+26.5 mm',z,label+' cuff ear tool','.8 mm');body=self.cut(body,self.four(tool,label+' cuff ear'),'Rounded '+label.lower()+' cuff mounting clearances')
  tool=self.cylinder('Y','-200 mm','cover_hip_x','0 mm','67 mm','400 mm','Hip pitch motion clearance');body=self.cut(body,[tool,self.reflected(tool,c.yZConstructionPlane,'Opposite hip pitch clearance')],'Pitch freedom below the shoulders');return body
 def current(self):
  body=self.roof(self.base());return SensorBodyDeltaIntent(self.g).apply(body)
