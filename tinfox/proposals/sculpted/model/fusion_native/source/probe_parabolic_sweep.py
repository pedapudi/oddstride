"""Prove an editable native sweep for the exact V0 compound face equation.

The study lives temporarily inside the existing Head design and is removed after
measurement. It does not create a cloud document or replace accepted geometry.
"""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
file_id=json.loads((ROOT/'manifests/subsystems.json').read_text())['subsystems']['head']['file_id']
script='''import adsk.core as core,adsk.fusion as fusion,json,math

def run(_context: str):
 app=core.Application.get();doc=next(d for d in app.documents if d.isSaved and d.dataFile.id==HEAD_ID);doc.activate();assert not doc.isModified and not doc.dataFile.isReadOnly
 d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Temporary compound-crown sweep proof';c.partNumber='STUDY_CROWN_SWEEP'
 created_parameters=[]
 def param(name,value):
  full='crown_proof_'+name;assert d.userParameters.itemByName(full) is None
  p=d.userParameters.add(full,core.ValueInput.createByString(str(value)+' mm'),'mm','Temporary exact-paraboloid construction proof');created_parameters.append(p);return full
 def point(x,y,z):return core.Point3D.create(x*.1,y*.1,z*.1)
 def val(expr):return core.ValueInput.createByString(expr)
 xref=param('reference_x',245.4);hc=param('horizontal_crown',8);vc=param('vertical_crown',10);halfwidth=param('half_width',98);halfheight=param('half_height',42);span=param('half_span',110);zhalf=param('vertical_half_span',55);zc=param('center_z',2);back=param('back_x',180);offset=param('offset',2.1)
 def constrain(sk,p,xexpr,yexpr):
  q=p.geometry
  for axis,expr in [(1,yexpr),(0,xexpr)]:
   if expr is None:continue
   value=q.x if axis==0 else q.y
   if abs(value)<1e-7:continue
   orientation=fusion.DimensionOrientations.HorizontalDimensionOrientation if axis==0 else fusion.DimensionOrientations.VerticalDimensionOrientation
   first,second=(sk.originPoint,p) if value>0 else (p,sk.originPoint)
   try:dim=sk.sketchDimensions.addDistanceDimension(first,second,orientation,core.Point3D.create(q.x+.25,q.y+.25,0))
   except Exception as error:raise RuntimeError(json.dumps({'sketch':sk.name,'axis':axis,'expression':expr,'point_xy':[q.x,q.y],'existing_dimensions':sk.sketchDimensions.count,'point_fixed':p.isFixed,'points':[[pp.geometry.x,pp.geometry.y,pp.isFullyConstrained] for pp in sk.sketchPoints],'dimensions':[{'name':dd.parameter.name,'expression':dd.parameter.expression,'value':dd.parameter.value} for dd in sk.sketchDimensions],'constraints':[co.objectType for co in sk.geometricConstraints]})) from error
   dim.parameter.expression=expr if value>0 else '-('+expr+')'
 def free_automatic_axes(sk):
  for constraint in list(sk.geometricConstraints):
   if constraint.objectType in ['adsk::fusion::HorizontalConstraint','adsk::fusion::VerticalConstraint']:assert constraint.deleteMe()
 def cubic_controls(C,A,L,zc_value=0):return [(C-A*L*L,-L+zc_value),(C+A*L*L/3,-L/3+zc_value),(C+A*L*L/3,L/3+zc_value),(C-A*L*L,L+zc_value)]
 def perform():
  plane_in=c.constructionPlanes.createInput();plane_in.setByOffset(c.xYConstructionPlane,val(zc+' - '+zhalf));plane=c.constructionPlanes.add(plane_in);plane.name='Face lower section datum'
  sk=c.sketches.add(plane);sk.name='Horizontal parabolic crown';sk.isComputeDeferred=False
  C=245.4+8+10*(1-(55/42)**2)-2.1;A=8/98**2;controls=cubic_controls(C,A,110)
  cp=[sk.sketchPoints.add(sk.modelToSketchSpace(point(x,y,-53))) for x,y in controls]
  Cexpr=xref+' + '+hc+' + '+vc+' * (1 - ('+zhalf+' / '+halfheight+')^2) - '+offset
  edge=Cexpr+' - '+hc+' * ('+span+' / '+halfwidth+')^2';middle=Cexpr+' + '+hc+' * ('+span+' / '+halfwidth+')^2 / 3'
  for p,xe,ye in zip(cp,[edge,middle,None,None],['-'+span,'-'+span+'/3',span+'/3',span]):constrain(sk,p,xe,ye)
  sk.geometricConstraints.addVerticalPoints(cp[0],cp[3]);sk.geometricConstraints.addVerticalPoints(cp[1],cp[2])
  cps=sk.sketchCurves.sketchControlPointSplines.add(cp,fusion.SplineDegrees.SplineDegreeThree)
  profile_reused=[p.entityToken==q.entityToken for p,q in zip(cps.controlPoints,cp)]
  for p,q,reused in zip(cps.controlPoints,cp,profile_reused):
   if not reused:sk.geometricConstraints.addCoincident(p,q)
  rear_top=sk.sketchPoints.add(sk.modelToSketchSpace(point(180,110,-53)));rear_bottom=sk.sketchPoints.add(sk.modelToSketchSpace(point(180,-110,-53)));constrain(sk,rear_top,back,span);constrain(sk,rear_bottom,None,'-'+span);sk.geometricConstraints.addVerticalPoints(rear_top,rear_bottom)
  sk.sketchCurves.sketchLines.addByTwoPoints(cp[-1],rear_top);sk.sketchCurves.sketchLines.addByTwoPoints(rear_top,rear_bottom);sk.sketchCurves.sketchLines.addByTwoPoints(rear_bottom,cp[0])
  sk.isComputeDeferred=False;assert sk.profiles.count==1
  pin=c.constructionPlanes.createInput();pin.setByOffset(c.xZConstructionPlane,val(span if c.xZConstructionPlane.geometry.normal.y<0 else '-'+span));pp=c.constructionPlanes.add(pin);pp.name='Vertical crown path datum'
  pathsk=c.sketches.add(pp);pathsk.name='Vertical parabolic crown';pathsk.isComputeDeferred=False
  Cpath=245.4+8*(1-(110/98)**2)+10-2.1;control_path=cubic_controls(Cpath,10/42**2,55,2)
  path_points=[pathsk.sketchPoints.add(pathsk.modelToSketchSpace(point(x,-110,z))) for x,z in control_path]
  q0=pathsk.modelToSketchSpace(point(0,-110,0));qz=pathsk.modelToSketchSpace(point(0,-110,1));zsign=1 if qz.y>q0.y else -1
  Cpath_expr=xref+' + '+hc+' * (1 - ('+span+' / '+halfwidth+')^2) + '+vc+' - '+offset
  path_edge=Cpath_expr+' - '+vc+' * ('+zhalf+' / '+halfheight+')^2';path_middle=Cpath_expr+' + '+vc+' * ('+zhalf+' / '+halfheight+')^2 / 3'
  for p,xe,ze in zip(path_points,[path_edge,path_middle,None,None],[zc+' - '+zhalf,zc+' - '+zhalf+'/3',zc+' + '+zhalf+'/3',zc+' + '+zhalf]):constrain(pathsk,p,xe,ze if zsign>0 else '-('+ze+')')
  pathsk.geometricConstraints.addVerticalPoints(path_points[0],path_points[3]);pathsk.geometricConstraints.addVerticalPoints(path_points[1],path_points[2])
  pathcurve=pathsk.sketchCurves.sketchControlPointSplines.add(path_points,fusion.SplineDegrees.SplineDegreeThree)
  path_reused=[p.entityToken==q.entityToken for p,q in zip(pathcurve.controlPoints,path_points)]
  for p,q,reused in zip(pathcurve.controlPoints,path_points,path_reused):
   if not reused:pathsk.geometricConstraints.addCoincident(p,q)
  pathsk.isComputeDeferred=False
  path=c.features.createPath(pathcurve,False)
  inp=c.features.sweepFeatures.createInput(sk.profiles.item(0),path,fusion.FeatureOperations.NewBodyFeatureOperation);inp.orientation=fusion.SweepOrientationTypes.ParallelOrientationType
  f=c.features.sweepFeatures.add(inp);f.name='Compound crown from two parabolas';assert f.bodies.count==1;body=f.bodies.item(0)
  def volume():return c.bRepBodies.item(0).getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000
  before=volume();p=d.userParameters.itemByName(hc);old=p.expression;p.expression='9 mm';d.computeAll();changed=volume();p.expression=old;d.computeAll();restored=volume()
  body=c.bRepBodies.item(0);measurement_body=body.createForAssemblyContext(occ)
  points=[]
  for y in [-89,-40,0,40,89]:
   for z in [-27,2,27]:
    x=245.4+8*(1-(y/98)**2)+10*(1-((z-2)/42)**2)-2.1
    measure=app.measureManager.measureMinimumDistance(point(x,y,z),measurement_body);points.append({'point_mm':[x,y,z],'distance_mm':measure.value*10})
  errors=[f.name+': '+f.errorOrWarningMessage for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]
  return {'profile_points_reused':profile_reused,'path_points_reused':path_reused,'features':c.features.count,'sketches':c.sketches.count,'sketch_entities':sum(s.sketchCurves.count for s in c.sketches),'control_points':8,'profile_control_world_mm':[[v*10 for v in sk.sketchToModelSpace(p.geometry).asArray()] for p in cps.controlPoints],'path_control_world_mm':[[v*10 for v in pathsk.sketchToModelSpace(p.geometry).asArray()] for p in pathcurve.controlPoints],'faces':body.faces.count,'edges':body.edges.count,'baseline_volume_mm3':before,'changed_volume_mm3':changed,'restored_volume_mm3':restored,'surface_samples':points,'feature_errors':errors,'passed':not errors and abs(changed-before)>.1 and abs(restored-before)<.001 and max(p['distance_mm'] for p in points)<.001,'scope':'Exact analytic V0 face equation; finite surface checks and a horizontal-crown edit/restore in an internal temporary Head component.'}
 try:result=perform()
 finally:
  assert occ.deleteMe()
  for p in reversed(created_parameters):
   if p.isValid:assert p.deleteMe()
  assert doc.save('Remove temporary crown primitive proof; Head geometry unchanged.')
 assert not any(o.component.partNumber=='STUDY_CROWN_SWEEP' for o in root.occurrences)
 assert doc.save('Remove temporary native crown proof; keep accepted Head geometry unchanged.')
 result['temporary_component_removed']=True;result['head_version_after_cleanup']=doc.dataFile.versionNumber;print(json.dumps(result))
'''.replace('HEAD_ID',repr(file_id))
r=rpc(script,'parabolic-sweep-proof',timeout=120);assert r[0].get('success'),r
record=json.loads(r[0]['message']);(ROOT/'audits/parabolic-sweep-proof.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
