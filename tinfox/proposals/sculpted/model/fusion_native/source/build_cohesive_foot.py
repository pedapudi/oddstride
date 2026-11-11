"""A native hemispherical sole and ruled neck tied to the shin's foot datum."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/intent_geometry.py').read_text()+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert not any(o.component.partNumber=='CANDIDATE_foot' for o in root.occurrences);occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.partNumber='CANDIDATE_foot';c.name='Rounded compliant foot';g=IntentGeometry(d,c)
 for name,value in {'lc_foot_radius':22,'lc_foot_neck_radius':9,'lc_foot_neck_height':20}.items():g.parameter(name,value)
 g.parameter('lc_foot_tilt',30,'deg');g.parameter('lc_foot_center_y','lc_shin_split_y');plane=g.plane(c.xZConstructionPlane,'lc_foot_center_y','Foot center lateral datum');sk=c.sketches.add(plane);sk.name='Tilted hemispherical sole section';center=g.skeleton_point(sk,'0 mm','lc_shank_foot_center');g.point_dimensions(sk,center,'0 mm','lc_shank_foot_center');arc,start,end=g.driven_arc(sk,center,'lc_foot_radius','lc_foot_tilt','lc_foot_tilt+90 deg','Spherical sole');axis=sk.sketchCurves.sketchLines.addByTwoPoints(end,center);sk.sketchCurves.sketchLines.addByTwoPoints(center,start);assert sk.profiles.count==1;inp=c.features.revolveFeatures.createInput(sk.profiles.item(0),axis,fusion.FeatureOperations.NewBodyFeatureOperation);inp.setAngleExtent(False,g.value('360 deg'));f=c.features.revolveFeatures.add(inp);f.name='Compliant spherical contact surface';body=f.bodies.item(0);sk.isLightBulbOn=False;face=next(f for f in body.faces if f.geometry.objectType==core.Plane.classType());base=c.sketches.add(face);base.name='Linked sole rim'
 if base.profiles.count==0:base.project2([face.edges.item(0)],True)
 assert base.profiles.count==1;plane=g.plane(c.xYConstructionPlane,'-lc_shank_foot_center+lc_foot_neck_height','Shin neck datum');neck=c.sketches.add(plane);neck.name='Nine millimeter neck radius';center=g.skeleton_point(neck,'0 mm','lc_foot_center_y');g.point_dimensions(neck,center,'0 mm','lc_foot_center_y');circle=neck.sketchCurves.sketchCircles.addByCenterRadius(center.geometry,g.mm('lc_foot_neck_radius')/10);neck.geometricConstraints.addCoincident(circle.centerSketchPoint,center);dim=neck.sketchDimensions.addRadialDimension(circle,core.Point3D.create(.5,6.7,0));dim.parameter.expression='lc_foot_neck_radius';inp=c.features.loftFeatures.createInput(fusion.FeatureOperations.JoinFeatureOperation);inp.loftSections.add(base.profiles.item(0));inp.loftSections.add(neck.profiles.item(0));f=c.features.loftFeatures.add(inp);f.name='Continuous boot neck';base.isLightBulbOn=False;neck.isLightBulbOn=False;assert c.bRepBodies.count==1;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features)
 original=c.bRepBodies.item(0);right_occ=root.occurrences.addNewComponent(core.Matrix3D.create());right=right_occ.component;right.partNumber='CANDIDATE_foot_right';right.name='Right rounded compliant foot';objects=core.ObjectCollection.create();objects.add(original);copy=right.features.copyPasteBodies.add(objects);original=copy.bodies.item(0);objects=core.ObjectCollection.create();objects.add(original);inp=right.features.mirrorFeatures.createInput(objects,right.xZConstructionPlane);inp.isCombine=False;right.features.mirrorFeatures.add(inp).name='Right foot reflection';right.features.removeFeatures.add(original).name='Keep handed foot'
 p=d.userParameters.itemByName('lc_shank_foot_center');old=p.expression;before=[part.bRepBodies.item(0).boundingBox.minPoint.z for part in [c,right]]
 try:
  p.expression='158 mm';assert d.computeAll()
  for i,part in enumerate([c,right]):assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in part.features);assert abs(part.bRepBodies.item(0).boundingBox.minPoint.z-before[i]+1)<1e-7
 finally:p.expression=old;assert d.computeAll()
 paths=[];rows=[]
 for i,part in enumerate([c,right]):
  assert abs(part.bRepBodies.item(0).boundingBox.minPoint.z-before[i])<1e-7;body=part.bRepBodies.item(0);label='cohesive-'+part.partNumber.replace('CANDIDATE_','').replace('_','-');path=os.path.join(tempfile.gettempdir(),'tinfox-native',label+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,part));paths.append(path);rows.append({'part':part.partNumber,'features':part.features.count,'sketches':part.sketches.count,'faces':body.faces.count,'edges':body.edges.count})
 print(json.dumps({'passed':True,'parts':rows,'paths':paths,'foot_datum_edit_restored':True,'saved':False,'scope':'Source boot envelope; retaining fastener and attachment cavity remain unresolved source design limitations.'}))
'''
r=rpc(s,'cohesive-foot-family',timeout=240);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-foot-family.json').write_text(json.dumps(record,indent=2));print(record)
for path in record['paths']:fetch(path,Path(path).name)
