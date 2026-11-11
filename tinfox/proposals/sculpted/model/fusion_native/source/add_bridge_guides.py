"""Preserve the V0 bridge's quintic shape with four editable planar guide curves."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
weights=json.loads((ROOT/'snapshots/design-intent/nose-bridge-bezier.json').read_text())['control_point_weights']
script=(ROOT/'source/intent_geometry.py').read_text()+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;occ=next(o for o in root.occurrences if o.component.partNumber=='CANDIDATE_body_nose_surround');c=occ.component;g=IntentGeometry(d,c)
 feature=next(f for f in c.features if f.name=='Continuous mounting bridge');assert feature.centerLineOrRails.count==0;feature.timelineObject.rollTo(True)
 station_x=['nose_mount_x + 5 mm','body_hip_x - 43 mm','body_hip_x - 20 mm','body_hip_x + 10 mm','body_hip_x + 35 mm','nose_end_start_x + 1 mm']
 widths=['nose_mount_lap_width','nose_bridge_width','nose_bridge_width','nose_bridge_width','nose_bridge_width','80 mm'];heights=['10 mm','nose_bridge_depth - 8 mm','nose_bridge_depth','nose_bridge_depth','nose_bridge_depth - 6 mm','12 mm'];centers=['body_mid_roof_z - 5.5 mm','body_mid_roof_z - .5 mm','body_mid_roof_z - .5 mm','body_mid_roof_z - .5 mm','body_mid_roof_z - 2.5 mm','body_mid_roof_z - 6.5 mm']
 data={'x':station_x,'half_width':['('+w+')/2' for w in widths],'roof':['('+z+')+('+h+')/2' for z,h in zip(centers,heights)],'floor':['('+z+')-('+h+')/2' for z,h in zip(centers,heights)]}
 for role,values in data.items():
  for i,row in enumerate(WEIGHTS):
   expression=' + '.join('('+str(float(v))+')*('+value+')' for v,value in zip(row,values) if abs(v)>1e-10);g.parameter('nose_bridge_guide_'+role+'_'+str(i+1),expression,comment='Derived quintic bridge guide; edit bridge stations or envelope dimensions')
 def curve(label,base,offset,ordinates):
  plane=g.plane(base,offset,label+' guide plane');sk=c.sketches.add(plane);sk.name=label+' shape guide';xs=['nose_bridge_guide_x_'+str(i+1) for i in range(6)];points=[g.skeleton_point(sk,x,y) for x,y in zip(xs,ordinates)];g.point_dimensions(sk,points[0],xs[0],ordinates[0])
  for i in range(1,6):
   for axis,expressions in [(0,xs),(1,ordinates)]:
    p,q=points[i-1],points[i];delta=(q.geometry.x-p.geometry.x) if axis==0 else (q.geometry.y-p.geometry.y);assert abs(delta)>1e-8,(label,i,axis)
    a,b=(p,q) if delta>0 else (q,p);orientation=fusion.DimensionOrientations.HorizontalDimensionOrientation if axis==0 else fusion.DimensionOrientations.VerticalDimensionOrientation
    dim=sk.sketchDimensions.addDistanceDimension(a,b,orientation,core.Point3D.create(q.geometry.x+.5,q.geometry.y+.5,0));expression='('+expressions[i]+') - ('+expressions[i-1]+')';dim.parameter.expression=expression if delta>0 else '-('+expression+')'
  spline=sk.sketchCurves.sketchControlPointSplines.add(points,fusion.SplineDegrees.SplineDegreeFive)
  for driver,control in zip(points,spline.controlPoints):
   if driver.entityToken!=control.entityToken:sk.geometricConstraints.addCoincident(driver,control)
  sk.isVisible=False;return spline
 rails=[curve('Roof',c.xZConstructionPlane,'0 mm',['-nose_bridge_guide_roof_'+str(i+1) for i in range(6)]),curve('Floor',c.xZConstructionPlane,'0 mm',['-nose_bridge_guide_floor_'+str(i+1) for i in range(6)]),curve('Right flank',c.xYConstructionPlane,'body_mid_roof_z - 5.5 mm',['nose_bridge_guide_half_width_'+str(i+1) for i in range(6)]),curve('Left flank',c.xYConstructionPlane,'body_mid_roof_z - 5.5 mm',['-nose_bridge_guide_half_width_'+str(i+1) for i in range(6)])]
 feature.timelineObject.rollTo(True)
 for rail in rails:assert feature.centerLineOrRails.addRail(rail)
 d.timeline.moveToEnd();assert d.computeAll();issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues;assert c.bRepBodies.count==1
 body=c.bRepBodies.item(0);occ.isLightBulbOn=True;body.isLightBulbOn=True;folder=os.path.join(tempfile.gettempdir(),'tinfox-native');step=os.path.join(folder,'body_nose_surround-guided.step');stl=os.path.join(folder,'body_nose_surround-guided.stl');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(step,c));opt=d.exportManager.createSTLExportOptions(c,stl);opt.unitType=fusion.DistanceUnits.MillimeterDistanceUnits;opt.meshRefinement=fusion.MeshRefinementSettings.MeshRefinementHigh;assert d.exportManager.execute(opt);occ.isLightBulbOn=False
 print(json.dumps({'features':c.features.count,'sketches':c.sketches.count,'rails':feature.centerLineOrRails.count,'guide_control_points':24,'faces':body.faces.count,'edges':body.edges.count,'volume_mm3':body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000,'paths':[step,stl],'saved':False}))
'''.replace('WEIGHTS',repr(weights))
r=rpc(script,'nose-bridge-guide-revision',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/nose-bridge-guide-revision.json').write_text(json.dumps(record,indent=2))
for path in record['paths']:fetch(path,Path(path).name)
print(json.dumps(record,indent=2))
