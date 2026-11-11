"""Small native Fusion constructions driven by named design dimensions.

These helpers author sketches and features. They do not import geometry or replay
sampled solid operations. Sketch control points are explicitly constrained to
their dimensional skeleton; passing points to a spline does not link them.
"""
import math
import adsk.core as core
import adsk.fusion as fusion

class IntentGeometry:
 def __init__(self,design,component):self.design=design;self.component=component
 def parameter(self,name,value,units='mm',comment='Independent design dimension'):
  p=self.design.userParameters.itemByName(name)
  if p is None:p=self.design.userParameters.add(name,core.ValueInput.createByString(str(value)+(' '+units if isinstance(value,(float,int)) else '')),units,comment)
  return name
 def mm(self,expression):return self.design.unitsManager.evaluateExpression(expression,'mm')*10
 def value(self,expression):return core.ValueInput.createByString(expression)
 def plane(self,base,offset,name):
  inp=self.component.constructionPlanes.createInput();inp.setByOffset(base,self.value(offset));p=self.component.constructionPlanes.add(inp);p.name=name;return p
 def point_dimensions(self,sketch,point,xexpr=None,yexpr=None):
  q=point.geometry
  for axis,expression in [(1,yexpr),(0,xexpr)]:
   if expression is None:continue
   coordinate=q.x if axis==0 else q.y
   if abs(coordinate)<1e-8:
    if axis==0:sketch.geometricConstraints.addVerticalPoints(sketch.originPoint,point)
    else:sketch.geometricConstraints.addHorizontalPoints(sketch.originPoint,point)
    continue
   first,second=(sketch.originPoint,point) if coordinate>0 else (point,sketch.originPoint)
   orientation=fusion.DimensionOrientations.HorizontalDimensionOrientation if axis==0 else fusion.DimensionOrientations.VerticalDimensionOrientation
   dim=sketch.sketchDimensions.addDistanceDimension(first,second,orientation,core.Point3D.create(q.x+.25,q.y+.25,0))
   dim.parameter.expression=expression if coordinate>0 else '-('+expression+')'
 def skeleton_point(self,sketch,xexpr,yexpr):return sketch.sketchPoints.add(core.Point3D.create(self.mm(xexpr)*.1,self.mm(yexpr)*.1,0))
 def symmetric_cubic(self,sketch,xexpressions,yexpressions):
  points=[self.skeleton_point(sketch,x,y) for x,y in zip(xexpressions,yexpressions)]
  for i,p in enumerate(points):self.point_dimensions(sketch,p,xexpressions[i] if i<2 else None,yexpressions[i])
  sketch.geometricConstraints.addVerticalPoints(points[0],points[3]);sketch.geometricConstraints.addVerticalPoints(points[1],points[2])
  spline=sketch.sketchCurves.sketchControlPointSplines.add(points,fusion.SplineDegrees.SplineDegreeThree)
  for control,driver in zip(spline.controlPoints,points):
   if control.entityToken!=driver.entityToken:sketch.geometricConstraints.addCoincident(control,driver)
  return spline,points
 def face_parameters(self):
  definitions={'head_face_reference_x':245.4,'head_face_horizontal_crown':8,'head_face_vertical_crown':10,'head_face_half_width':98,'head_face_half_height':42,'head_face_center_z':2,'head_face_tool_half_width':110,'head_face_tool_half_height':55,'head_face_tool_back_x':180}
  for name,value in definitions.items():self.parameter(name,value,comment='V0 compound face datum or crown; independent of motor and bearing fits')
 def face_sweep(self,offset,name):
  self.face_parameters();c=self.component
  x='head_face_reference_x';hc='head_face_horizontal_crown';vc='head_face_vertical_crown';w='head_face_half_width';h='head_face_half_height';span='head_face_tool_half_width';zh='head_face_tool_half_height';zc='head_face_center_z';back='head_face_tool_back_x'
  plane=self.plane(c.xYConstructionPlane,zc+' - '+zh,name+' lower datum');sk=c.sketches.add(plane);sk.name=name+' horizontal crown'
  center=x+' + '+hc+' + '+vc+' * (1 - ('+zh+' / '+h+')^2) - ('+offset+')'
  edge=center+' - '+hc+' * ('+span+' / '+w+')^2';middle=center+' + '+hc+' * ('+span+' / '+w+')^2 / 3'
  curve,points=self.symmetric_cubic(sk,[edge,middle,middle,edge],['-'+span,'-'+span+'/3',span+'/3',span])
  top=self.skeleton_point(sk,back,span);bottom=self.skeleton_point(sk,back,'-'+span);self.point_dimensions(sk,top,back,span);self.point_dimensions(sk,bottom,None,'-'+span);sk.geometricConstraints.addVerticalPoints(top,bottom)
  sk.sketchCurves.sketchLines.addByTwoPoints(points[-1],top);sk.sketchCurves.sketchLines.addByTwoPoints(top,bottom);sk.sketchCurves.sketchLines.addByTwoPoints(bottom,points[0]);assert sk.profiles.count==1
  plane=self.plane(c.xZConstructionPlane,span if c.xZConstructionPlane.geometry.normal.y<0 else '-'+span,name+' vertical datum');path_sk=c.sketches.add(plane);path_sk.name=name+' vertical crown'
  q0=path_sk.modelToSketchSpace(core.Point3D.create(0,-11,0));qz=path_sk.modelToSketchSpace(core.Point3D.create(0,-11,.1));zsign=1 if qz.y>q0.y else -1
  center=x+' + '+hc+' * (1 - ('+span+' / '+w+')^2) + '+vc+' - ('+offset+')';edge=center+' - '+vc+' * ('+zh+' / '+h+')^2';middle=center+' + '+vc+' * ('+zh+' / '+h+')^2 / 3'
  zexpr=[zc+' - '+zh,zc+' - '+zh+'/3',zc+' + '+zh+'/3',zc+' + '+zh]
  path_curve,_=self.symmetric_cubic(path_sk,[edge,middle,middle,edge],[z if zsign>0 else '-('+z+')' for z in zexpr]);path=c.features.createPath(path_curve,False)
  inp=c.features.sweepFeatures.createInput(sk.profiles.item(0),path,fusion.FeatureOperations.NewBodyFeatureOperation);inp.orientation=fusion.SweepOrientationTypes.ParallelOrientationType
  feature=c.features.sweepFeatures.add(inp);feature.name=name;sk.isVisible=False;path_sk.isVisible=False;assert feature.bodies.count==1
  return feature.bodies.item(0)
 def rounded_rectangle(self,plane,width,height,radius,center_v,name,center_u='0 mm'):
  """Eight analytic edges controlled by width, height, radius and center."""
  c=self.component;sk=c.sketches.add(plane);sk.name=name;sk.isComputeDeferred=True
  right='('+center_u+') + ('+width+')/2 - ('+radius+')';left='('+center_u+') - ('+width+')/2 + ('+radius+')';top='('+center_v+') + ('+height+')/2 - ('+radius+')';bottom='('+center_v+') - ('+height+')/2 + ('+radius+')'
  expr=[(right,top),(left,top),(left,bottom),(right,bottom)];points=[self.skeleton_point(sk,*pair) for pair in expr]
  self.point_dimensions(sk,points[0],right,top);self.point_dimensions(sk,points[1],left,None);sk.geometricConstraints.addHorizontalPoints(points[0],points[1]);self.point_dimensions(sk,points[2],None,bottom);sk.geometricConstraints.addVerticalPoints(points[1],points[2]);sk.geometricConstraints.addVerticalPoints(points[0],points[3]);sk.geometricConstraints.addHorizontalPoints(points[2],points[3])
  arcs=[];r=self.mm(radius)*.1
  for i,(center,start_angle) in enumerate(zip(points,[0,math.pi/2,math.pi,3*math.pi/2])):
   p=center.geometry;start=core.Point3D.create(p.x+r*math.cos(start_angle),p.y+r*math.sin(start_angle),0);arc=sk.sketchCurves.sketchArcs.addByCenterStartSweep(p,start,math.pi/2);sk.geometricConstraints.addCoincident(arc.centerSketchPoint,center)
   dim=sk.sketchDimensions.addRadialDimension(arc,core.Point3D.create(p.x+r*1.3,p.y+r*1.3,0));dim.parameter.expression=radius
   if i%2==0:sk.geometricConstraints.addHorizontalPoints(arc.centerSketchPoint,arc.startSketchPoint);sk.geometricConstraints.addVerticalPoints(arc.centerSketchPoint,arc.endSketchPoint)
   else:sk.geometricConstraints.addVerticalPoints(arc.centerSketchPoint,arc.startSketchPoint);sk.geometricConstraints.addHorizontalPoints(arc.centerSketchPoint,arc.endSketchPoint)
   arcs.append(arc)
  for i,arc in enumerate(arcs):sk.sketchCurves.sketchLines.addByTwoPoints(arc.endSketchPoint,arcs[(i+1)%4].startSketchPoint)
  sk.isComputeDeferred=False;assert sk.profiles.count==1,(name,sk.profiles.count)
  return sk
 def extrude(self,sketch,distance,name,operation=fusion.FeatureOperations.NewBodyFeatureOperation,bodies=None):
  inp=self.component.features.extrudeFeatures.createInput(sketch.profiles.item(0),operation);inp.setDistanceExtent(False,self.value(distance))
  if bodies is not None:inp.participantBodies=bodies
  feature=self.component.features.extrudeFeatures.add(inp);feature.name=name;sketch.isVisible=False;return feature
 def combine(self,target,tools,operation,name,keep=False):
  collection=core.ObjectCollection.create()
  for tool in tools:collection.add(tool)
  inp=self.component.features.combineFeatures.createInput(target,collection);inp.operation=operation;inp.isKeepToolBodies=keep;feature=self.component.features.combineFeatures.add(inp);feature.name=name
  if keep:
   tool_tokens={b.entityToken for b in tools};results=[b for b in feature.bodies if b.entityToken not in tool_tokens]
  else:results=[b for b in feature.bodies]
  assert len(results)==1,(name,len(results),[(b.name,b.entityToken) for b in feature.bodies]);return results[0]
 def yz_contour(self,x,width,height,radius,center_z,name):
  plane=self.plane(self.component.yZConstructionPlane,x,name+' datum')
  # Fusion's native YZ basis is (-Z,Y), preserving orientation.
  return self.rounded_rectangle(plane,height,width,radius,'0 mm',name,'-('+center_z+')')
 def rounded_octagon(self,plane,side,roof,floor,top_bevel,bottom_bevel,radius,name):
  """A rounded eight-sided envelope with analytic lines and circular arcs.

  Each arc center follows the six envelope dimensions. Radial and endpoint
  constraints preserve the 45-degree corner tangencies during dimensional edits.
  """
  sk=self.component.sketches.add(plane);sk.name=name;sk.isComputeDeferred=False
  t='(sqrt(2)-1)';a='('+side+') - ('+top_bevel+') - ('+radius+')*'+t;b='('+side+') - ('+radius+')';c='('+side+') - ('+bottom_bevel+') - ('+radius+')*'+t
  za='('+roof+') - ('+radius+')';zb='('+roof+') - ('+top_bevel+') - ('+radius+')*'+t;zc='('+floor+') + ('+bottom_bevel+') + ('+radius+')*'+t;zd='('+floor+') + ('+radius+')'
  centers=[(a,za),(b,zb),(b,zc),(c,zd),('-('+c+')',zd),('-('+b+')',zc),('-('+b+')',zb),('-('+a+')',za)]
  points=[self.skeleton_point(sk,'-('+z+')',y) for y,z in centers]
  self.point_dimensions(sk,points[1],'-('+zb+')',b)
  for index,z in [(0,za),(2,zc),(3,zd)]:self.point_dimensions(sk,points[index],'-('+z+')',None)
  sk.geometricConstraints.addHorizontalPoints(points[1],points[2])
  for low,high,bevel in [(0,1,top_bevel),(3,2,bottom_bevel)]:
   dim=sk.sketchDimensions.addDistanceDimension(points[low],points[high],fusion.DimensionOrientations.VerticalDimensionOrientation,core.Point3D.create(0,10,0));dim.parameter.expression='('+bevel+') - ('+radius+') + ('+radius+')*'+t
  axis=sk.sketchCurves.sketchLines.addByTwoPoints(core.Point3D.create(0,0,0),core.Point3D.create(1,0,0));axis.isConstruction=True;axis.isFixed=True
  for i in range(4):sk.geometricConstraints.addSymmetry(points[i],points[7-i],axis)
  ends=[];r=self.mm(radius)*.1
  for i,center in enumerate(points):
   q=center.geometry;angle=math.pi-i*math.pi/4
   start=core.Point3D.create(q.x+r*math.cos(angle),q.y+r*math.sin(angle),0);arc=sk.sketchCurves.sketchArcs.addByCenterStartSweep(q,start,-math.pi/4);sk.geometricConstraints.addCoincident(arc.centerSketchPoint,center)
   dim=sk.sketchDimensions.addRadialDimension(arc,core.Point3D.create(q.x+r*1.3,q.y+r*1.3,0));dim.parameter.expression=radius
   for endpoint in [arc.startSketchPoint,arc.endSketchPoint]:
    dx=endpoint.geometry.x-q.x;dy=endpoint.geometry.y-q.y
    if abs(dx)<1e-7:sk.geometricConstraints.addVerticalPoints(center,endpoint)
    elif abs(dy)<1e-7:sk.geometricConstraints.addHorizontalPoints(center,endpoint)
    else:
     first,second=(center,endpoint) if dx>0 else (endpoint,center);d=sk.sketchDimensions.addDistanceDimension(first,second,fusion.DimensionOrientations.HorizontalDimensionOrientation,core.Point3D.create(q.x+r,q.y+r,0));d.parameter.expression='('+radius+') / sqrt(2)'
   first,last=(arc.startSketchPoint,arc.endSketchPoint) if arc.startSketchPoint.geometry.distanceTo(start)<1e-6 else (arc.endSketchPoint,arc.startSketchPoint)
   ends.append((first,last))
  for i,(_,last) in enumerate(ends):sk.sketchCurves.sketchLines.addByTwoPoints(last,ends[(i+1)%len(ends)][0])
  sk.isComputeDeferred=False;assert sk.profiles.count==1,(name,sk.profiles.count)
  return sk
 def loft(self,sketches,name,operation=fusion.FeatureOperations.NewBodyFeatureOperation,ruled=False):
  inp=self.component.features.loftFeatures.createInput(operation);inp.isSolid=True
  for sk in sketches:inp.loftSections.add(sk.profiles.item(0))
  if ruled:inp.isRuled=True
  feature=self.component.features.loftFeatures.add(inp);feature.name=name
  for sk in sketches:sk.isVisible=False
  return feature.bodies.item(0)
 def end_fillet(self,body,x,radius,name):
  value=self.mm(x)*.1;edges=core.ObjectCollection.create()
  for edge in body.edges:
   b=edge.boundingBox
   if abs(b.minPoint.x-value)<1e-5 and abs(b.maxPoint.x-value)<1e-5:edges.add(edge)
  assert edges.count>0,(name,value)
  inp=self.component.features.filletFeatures.createInput();inp.edgeSetInputs.addConstantRadiusEdgeSet(edges,self.value(radius),False);feature=self.component.features.filletFeatures.add(inp);feature.name=name;return feature.bodies.item(0)
 def driven_arc(self,sk,center,radius,start_angle,end_angle,name):
  """An analytic arc whose center, radius and end directions remain editable."""
  rad=self.mm(radius)*.1;sa=self.design.unitsManager.evaluateExpression(start_angle,'rad');ea=self.design.unitsManager.evaluateExpression(end_angle,'rad');p=center.geometry
  start=core.Point3D.create(p.x+rad*math.cos(sa),p.y+rad*math.sin(sa),0);arc=sk.sketchCurves.sketchArcs.addByCenterStartSweep(p,start,ea-sa);sk.geometricConstraints.addCoincident(arc.centerSketchPoint,center)
  dim=sk.sketchDimensions.addRadialDimension(arc,core.Point3D.create(p.x+rad*.6,p.y+rad*.6,0));dim.parameter.expression=radius
  first,last=(arc.startSketchPoint,arc.endSketchPoint) if arc.startSketchPoint.geometry.distanceTo(start)<1e-6 else (arc.endSketchPoint,arc.startSketchPoint)
  for point,angle in [(first,start_angle),(last,end_angle)]:
   dx=point.geometry.x-p.x
   if abs(dx)<1e-7:sk.geometricConstraints.addVerticalPoints(center,point)
   elif abs(point.geometry.y-p.y)<1e-7:sk.geometricConstraints.addHorizontalPoints(center,point)
   else:
    a,b=(center,point) if dx>0 else (point,center);dim=sk.sketchDimensions.addDistanceDimension(a,b,fusion.DimensionOrientations.HorizontalDimensionOrientation,core.Point3D.create(p.x+rad*.8,p.y+rad*.8,0));expr='('+radius+') * cos('+angle+')';dim.parameter.expression=expr if dx>0 else '-('+expr+')'
  return arc,first,last
 def rectangle(self,plane,width,height,cx,cy,name):
  sk=self.component.sketches.add(plane);sk.name=name;sk.isComputeDeferred=True
  x0='('+cx+')-('+width+')/2';x1='('+cx+')+('+width+')/2';y0='('+cy+')-('+height+')/2';y1='('+cy+')+('+height+')/2'
  lines=sk.sketchCurves.sketchLines.addTwoPointRectangle(core.Point3D.create(self.mm(x0)*.1,self.mm(y0)*.1,0),core.Point3D.create(self.mm(x1)*.1,self.mm(y1)*.1,0))
  p0=min([p for line in lines for p in [line.startSketchPoint,line.endSketchPoint]],key=lambda p:(p.geometry.x-self.mm(x0)*.1)**2+(p.geometry.y-self.mm(y0)*.1)**2)
  p1=min([p for line in lines for p in [line.startSketchPoint,line.endSketchPoint]],key=lambda p:(p.geometry.x-self.mm(x1)*.1)**2+(p.geometry.y-self.mm(y1)*.1)**2)
  self.point_dimensions(sk,p0,x0,y0);self.point_dimensions(sk,p1,x1,y1);sk.isComputeDeferred=False;assert sk.profiles.count==1;return sk
 def box(self,width,depth,height,cx,cy,cz,name):
  plane=self.plane(self.component.xYConstructionPlane,'('+cz+')-('+height+')/2',name+' datum');sk=self.rectangle(plane,width,depth,cx,cy,name+' rectangle');return self.extrude(sk,height,name).bodies.item(0)
 def round_edges(self,body,radius,name):
  edges=core.ObjectCollection.create()
  for e in body.edges:edges.add(e)
  inp=self.component.features.filletFeatures.createInput();inp.edgeSetInputs.addConstantRadiusEdgeSet(edges,self.value(radius),False);feature=self.component.features.filletFeatures.add(inp);feature.name=name;return feature.bodies.item(0)
 def pattern_yz(self,body,dy,dz,name):
  entities=core.ObjectCollection.create();entities.add(body);c=self.component;before={b.entityToken for b in c.bRepBodies}
  inp=c.features.rectangularPatternFeatures.createInput(entities,c.yConstructionAxis,self.value('2'),self.value(dy),fusion.PatternDistanceType.SpacingPatternDistanceType);assert inp.setDirectionTwo(c.zConstructionAxis,self.value('2'),self.value(dz));feature=c.features.rectangularPatternFeatures.add(inp);feature.name=name
  return [body]+[b for b in c.bRepBodies if b.entityToken not in before]
 def circle_grid_yz(self,x,half_y,half_z,radius,center_z,name):
  plane=self.plane(self.component.yZConstructionPlane,x,name+' datum');sk=self.component.sketches.add(plane);sk.name=name;sk.isComputeDeferred=True
  coordinates=[('-('+center_z+')-('+half_z+')','-('+half_y+')'),('-('+center_z+')-('+half_z+')',half_y),('-('+center_z+')+('+half_z+')',half_y),('-('+center_z+')+('+half_z+')','-('+half_y+')')]
  points=[self.skeleton_point(sk,*p) for p in coordinates];self.point_dimensions(sk,points[0],*coordinates[0]);self.point_dimensions(sk,points[1],None,coordinates[1][1]);sk.geometricConstraints.addVerticalPoints(points[0],points[1]);self.point_dimensions(sk,points[2],coordinates[2][0],None);sk.geometricConstraints.addHorizontalPoints(points[1],points[2]);sk.geometricConstraints.addVerticalPoints(points[2],points[3]);sk.geometricConstraints.addHorizontalPoints(points[0],points[3])
  circles=[]
  for p in points:
   circle=sk.sketchCurves.sketchCircles.addByCenterRadius(p.geometry,self.mm(radius)*.1);sk.geometricConstraints.addCoincident(circle.centerSketchPoint,p)
   if circles:sk.geometricConstraints.addEqual(circles[0],circle)
   else:
    dim=sk.sketchDimensions.addRadialDimension(circle,core.Point3D.create(p.geometry.x+.5,p.geometry.y+.5,0));dim.parameter.expression=radius
   circles.append(circle)
  sk.isComputeDeferred=False;assert sk.profiles.count==4;return sk
 def profiles(self,sketch):
  collection=core.ObjectCollection.create()
  for profile in sketch.profiles:collection.add(profile)
  return collection
 def extrude_to_face(self,sketch,face,name,operation=fusion.FeatureOperations.NewBodyFeatureOperation,bodies=None):
  inp=self.component.features.extrudeFeatures.createInput(self.profiles(sketch),operation);extent=fusion.ToEntityExtentDefinition.create(face,False);assert inp.setOneSideExtent(extent,fusion.ExtentDirections.PositiveExtentDirection)
  if bodies is not None:inp.participantBodies=bodies
  feature=self.component.features.extrudeFeatures.add(inp);feature.name=name;sketch.isVisible=False;return feature
 def extrude_all(self,sketch,distance,name,operation=fusion.FeatureOperations.NewBodyFeatureOperation,bodies=None):
  inp=self.component.features.extrudeFeatures.createInput(self.profiles(sketch),operation);inp.setDistanceExtent(False,self.value(distance))
  if bodies is not None:inp.participantBodies=bodies
  feature=self.component.features.extrudeFeatures.add(inp);feature.name=name;sketch.isVisible=False;return feature
 def remove(self,body,name):
  feature=self.component.features.removeFeatures.add(body);feature.name=name;return feature
 def control_spline_3d(self,coordinate_expressions,name,degree=5,internal_knots=None):
  """Editable Bezier poles, each driven by orthogonal coordinate dimensions."""
  sk=self.component.sketches.add(self.component.xYConstructionPlane);sk.name=name;sk.isComputeDeferred=True;origin=sk.originPoint;axes=[]
  for vector in [(1,0,0),(0,1,0),(0,0,1)]:
   line=sk.sketchCurves.sketchLines.addByTwoPoints(origin,core.Point3D.create(*vector));line.isConstruction=True;line.isFixed=True;axes.append(line)
  points=[]
  for expressions in coordinate_expressions:
   xyz=[self.mm(e)*.1 for e in expressions];previous=origin
   for axis in range(3):
    coordinates=[xyz[i] if i<=axis else 0 for i in range(3)];point=sk.sketchPoints.add(core.Point3D.create(*coordinates));line=sk.sketchCurves.sketchLines.addByTwoPoints(previous,point);line.isConstruction=True;sk.geometricConstraints.addParallel(line,axes[axis]);dim=sk.sketchDimensions.addDistanceDimension(previous,point,fusion.DimensionOrientations.AlignedDimensionOrientation,core.Point3D.create(coordinates[0]+.5,coordinates[1]+.5,coordinates[2]+.5));dim.parameter.expression=expressions[axis] if xyz[axis]>=0 else '-('+expressions[axis]+')';previous=point
   points.append(previous)
  if internal_knots is not None:
   assert degree==3
   spline=native_nonuniform_cubic(sk,points,internal_knots);sk.isComputeDeferred=False;sk.isVisible=False;return spline
  if degree in [3,5]:spline=sk.sketchCurves.sketchControlPointSplines.add(points,fusion.SplineDegrees.SplineDegreeThree if degree==3 else fusion.SplineDegrees.SplineDegreeFive)
  else:
   assert degree in [7,9] and len(points)==degree+1
   seed=[core.Point3D.create(p.geometry.x+.123,p.geometry.y+.456,p.geometry.z+.789) for p in points[:6]];spline=sk.sketchCurves.sketchControlPointSplines.add(seed,fusion.SplineDegrees.SplineDegreeFive);spline.degree=fusion.SplineDegrees.SplineDegreeSeven if degree==7 else fusion.SplineDegrees.SplineDegreeNine;assert len(spline.controlPoints)==len(points)
  for driver,control in zip(points,spline.controlPoints):
   if driver.entityToken!=control.entityToken:sk.geometricConstraints.addCoincident(driver,control)
  sk.isComputeDeferred=False;sk.isVisible=False;return spline
