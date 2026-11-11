"""Extend the native rounded cover with the qualified low sensor service cuts.

Run in a component that already owns the rounded cover's native history. The
independent local replay is recorded in current-low-cover-delta-replay.json.
"""
class SensorBodyDeltaIntent:
 def __init__(self,geometry):self.g=geometry;self.c=geometry.component

 def cut(self,body,tool,name,remove_source_remnants=False):
  objects=core.ObjectCollection.create();objects.add(tool)
  inp=self.c.features.combineFeatures.createInput(body,objects)
  inp.operation=fusion.FeatureOperations.CutFeatureOperation;inp.isKeepToolBodies=False
  feature=self.c.features.combineFeatures.add(inp);feature.name=name
  bodies=list(feature.bodies)
  assert bodies,(name,'No cover material remains')
  if len(bodies)>1:
   assert remove_source_remnants,(name,len(bodies))
   ranked=sorted(bodies,key=lambda b:b.volume,reverse=True)
   assert ranked[0].volume/sum(b.volume for b in ranked)>.99
   body=ranked[0]
   for remnant in ranked[1:]:self.g.remove(remnant,'Remove disconnected obsolete lip')
   return body
  return bodies[0]

 def apply(self,body):
  g=self.g;c=self.c
  settings={'saddle_cover_old_seat_x':82,'saddle_cover_crossmember_x':121,
   'saddle_cover_rail_y':99.5,'saddle_cover_service_x':149,
   'saddle_cover_service_length':150,'saddle_cover_service_width':92,
   'saddle_cover_service_radius':8,'saddle_cover_roof_z':55.5,
   'saddle_cover_roof_patch_thickness':3}
  for name,value in settings.items():g.parameter(name,value,comment='Low sensor saddle cover interface; independent of fastener dimensions')
  tool=g.box('18 mm','204 mm','18 mm','122 mm','0 mm','44 mm','Obsolete front lip relief')
  body=self.cut(body,tool,'Remove obsolete front lip',True)
  tool=g.box('24 mm','62 mm','70 mm','138 mm','0 mm','60 mm','Former cradle relief')
  body=self.cut(body,tool,'Open former cradle region',True)
  def cylinder(x,z,radius,depth,name):
   plane=g.plane(c.xYConstructionPlane,z,name+' datum');sk=c.sketches.add(plane);sk.name=name
   point=g.skeleton_point(sk,x,'0 mm');g.point_dimensions(sk,point,x,'0 mm')
   circle=sk.sketchCurves.sketchCircles.addByCenterRadius(point.geometry,g.mm(radius)*.1)
   sk.geometricConstraints.addCoincident(circle.centerSketchPoint,point)
   sk.sketchDimensions.addRadialDimension(circle,core.Point3D.create(point.geometry.x+.4,.4,0)).parameter.expression=radius
   return g.extrude(sk,depth,name).bodies.item(0)
  tool=cylinder('saddle_cover_old_seat_x','45 mm','35 mm','15 mm','Obsolete lidar seat tool')
  body=self.cut(body,tool,'Remove old roof seat')
  patch=cylinder('saddle_cover_old_seat_x','saddle_cover_roof_z-saddle_cover_roof_patch_thickness','36 mm','saddle_cover_roof_patch_thickness','Close obsolete roof opening')
  body=g.combine(body,[patch],fusion.FeatureOperations.JoinFeatureOperation,'Continuous roof over old sensor opening')
  plane=g.plane(c.xYConstructionPlane,'-70 mm','Sensor service opening datum')
  sk=g.rounded_rectangle(plane,'saddle_cover_service_length','saddle_cover_service_width','saddle_cover_service_radius','0 mm','Rounded sensor service opening','saddle_cover_service_x')
  tool=g.extrude(sk,'200 mm','Sensor service opening tool').bodies.item(0)
  body=self.cut(body,tool,'Open sensor service aperture')
  for sign,label in [('-','Left'),('','Right')]:
   tool=g.box('264 mm','15 mm','100 mm','0 mm',sign+'saddle_cover_rail_y','-14.5 mm',label+' rail release tool')
   body=self.cut(body,tool,label+' open rail service path')
   tool=g.box('14 mm','206 mm','100 mm',sign+'saddle_cover_crossmember_x','0 mm','-6.7 mm',label+' crossmember release tool')
   body=self.cut(body,tool,label+' open crossmember service path')
  return body
