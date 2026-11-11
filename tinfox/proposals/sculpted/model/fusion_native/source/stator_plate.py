"""Human-editable stator plate: annulus, two drilled seeds, two circular patterns."""
import adsk.core as core,adsk.fusion as fusion,math,json

def run(_context: str):
 app=core.Application.get();d=fusion.Design.cast(app.activeProduct)
 assert app.activeDocument.name.startswith('Tinfox - Native Master Assembly')
 group=next(o.component for o in d.rootComponent.occurrences if o.component.name=='Shared leg designs')
 old=[o for o in group.occurrences if o.component.partNumber=='motor_mount_ring']
 occ=group.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Knee motor stator plate';c.partNumber='motor_mount_ring'
 def parameter(name,value,units='mm'):
  n='stator_'+name;p=d.userParameters.itemByName(n)
  if not p:p=d.userParameters.add(n,core.ValueInput.createByString(str(value)+' '+units),units,'Knee stator plate: '+name.replace('_',' '))
  return n
 dims={k:parameter(k,v,u) for k,v,u in [('outer_diameter',96,'mm'),('bore',60,'mm'),('thickness',3,'mm'),('axial_datum',50.5,'mm'),('motor_pcd',73,'mm'),('motor_clock',20,'deg'),('motor_hole_count',9,''),('tie_pcd',87,'mm'),('tie_hole_count',3,''),('clearance',3.4,'mm')]}
 v=lambda x:core.ValueInput.createByString(x)
 inp=c.constructionPlanes.createInput();inp.setByOffset(c.xZConstructionPlane,v(dims['axial_datum']));plane=c.constructionPlanes.add(inp);plane.name='Stator mounting face · Y 50.5'
 s=c.sketches.add(plane);s.name='Annular plate · OD and bore'
 for name,r in [('outer_diameter',4.8),('bore',3)]:
  circle=s.sketchCurves.sketchCircles.addByCenterRadius(core.Point3D.create(),r)
  s.geometricConstraints.addCoincident(circle.centerSketchPoint,s.originPoint)
  dim=s.sketchDimensions.addDiameterDimension(circle,core.Point3D.create(r*1.3,0,0));dim.parameter.expression=dims[name]
 annulus=next(s.profiles.item(i) for i in range(s.profiles.count) if s.profiles.item(i).profileLoops.count==2)
 inp=c.features.extrudeFeatures.createInput(annulus,fusion.FeatureOperations.NewBodyFeatureOperation);inp.setDistanceExtent(False,v(dims['thickness']));ext=c.features.extrudeFeatures.add(inp);ext.name='Plate thickness';s.isVisible=False
 def holes(name,pcd,clock,count):
  sk=c.sketches.add(plane);sk.name=name+' seed · PCD, clock and clearance'
  a=math.radians(clock);p=sk.modelToSketchSpace(core.Point3D.create(pcd/20*math.cos(a),5.05,pcd/20*math.sin(a)))
  line=sk.sketchCurves.sketchLines.addByTwoPoints(sk.originPoint,p);line.isConstruction=True
  length=sk.sketchDimensions.addDistanceDimension(line.startSketchPoint,line.endSketchPoint,fusion.DimensionOrientations.AlignedDimensionOrientation,core.Point3D.create(p.x/2,p.y/2+.3,0));length.parameter.expression=dims['motor_pcd' if name=='Motor bolts' else 'tie_pcd']+'/2'
  if name=='Motor bolts':
   axis=sk.sketchCurves.sketchLines.addByTwoPoints(sk.originPoint,core.Point3D.create(1,0,0));axis.isConstruction=True;sk.geometricConstraints.addHorizontal(axis)
   angle=sk.sketchDimensions.addAngularDimension(axis,line,core.Point3D.create(2,p.y/2,0));angle.parameter.expression=dims['motor_clock']
  else:sk.geometricConstraints.addVertical(line)
  circle=sk.sketchCurves.sketchCircles.addByCenterRadius(p,.17);sk.geometricConstraints.addCoincident(circle.centerSketchPoint,line.endSketchPoint)
  dimension=sk.sketchDimensions.addDiameterDimension(circle,core.Point3D.create(p.x+.5,p.y+.3,0));dimension.parameter.expression=dims['clearance']
  inp=c.features.extrudeFeatures.createInput(sk.profiles.item(0),fusion.FeatureOperations.CutFeatureOperation);inp.setDistanceExtent(False,v(dims['thickness']));hole=c.features.extrudeFeatures.add(inp);hole.name=name+' · first clearance hole';sk.isVisible=False
  objects=core.ObjectCollection.create();objects.add(hole)
  inp=c.features.circularPatternFeatures.createInput(objects,c.yConstructionAxis);inp.quantity=v(dims['motor_hole_count' if name=='Motor bolts' else 'tie_hole_count']);inp.totalAngle=v('360 deg');inp.isSymmetric=False
  pattern=c.features.circularPatternFeatures.add(inp);pattern.name=name+' · '+str(count)+' around axis'
 holes('Motor bolts',73,20,9);holes('Structural ties',87,90,3)
 assert c.bRepBodies.count==1
 result=c.bRepBodies.item(0);result.name='motor_mount_ring';volume=result.physicalProperties.volume*1000
 assert abs(volume-12905.536957240713)<1e-5,volume
 for o in old:o.deleteMe()
 for p in list(d.userParameters):
  if p.name.startswith('motor_mount_ring_'):p.deleteMe()
 plane.isLightBulbOn=False
 app.activeDocument.save('Native stator plate simplified to three dimensioned sketches and two circular hole patterns.')
 print(json.dumps({'part':'motor_mount_ring','body_count':c.bRepBodies.count,'sketches':c.sketches.count,'features':[(f.name,f.objectType) for f in c.features],'volume_mm3':volume,'parameters':list(dims.values())}))
