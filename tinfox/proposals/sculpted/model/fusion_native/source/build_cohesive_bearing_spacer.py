"""Build a native spacer whose length follows the actual bearing stack."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/intent_geometry.py').read_text()+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert not any(o.component.partNumber=='CANDIDATE_knee_inner_spacer' for o in root.occurrences);occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.partNumber='CANDIDATE_knee_inner_spacer';c.name='Knee bearing spacer';g=IntentGeometry(d,c);g.parameter('lc_knee_spacer_outer_radius',7.75);g.parameter('lc_knee_spacer_start','lc_bearing_inner_y+lc_bearing_width');g.parameter('lc_knee_spacer_length','lc_bearing_span-lc_bearing_width');plane=g.plane(c.xZConstructionPlane,'lc_knee_spacer_start','Bearing inner-race stack datum');sk=c.sketches.add(plane);sk.name='Spacer outside diameter and sleeve clearance';center=g.skeleton_point(sk,'0 mm','lc_thigh_length');g.point_dimensions(sk,center,'0 mm','lc_thigh_length')
 for radius in ['lc_knee_spacer_outer_radius','lc_axle_fit_radius']:
  circle=sk.sketchCurves.sketchCircles.addByCenterRadius(center.geometry,g.mm(radius)/10);sk.geometricConstraints.addCoincident(circle.centerSketchPoint,center);dim=sk.sketchDimensions.addRadialDimension(circle,core.Point3D.create(.7,17.7,0));dim.parameter.expression=radius
 profile=next(p for p in sk.profiles if p.profileLoops.count==2);inp=c.features.extrudeFeatures.createInput(profile,fusion.FeatureOperations.NewBodyFeatureOperation);inp.setDistanceExtent(False,g.value('lc_knee_spacer_length'));f=c.features.extrudeFeatures.add(inp);f.name='Bearing inner-race spacing';sk.isLightBulbOn=False;assert c.bRepBodies.count==1;objects=core.ObjectCollection.create();objects.add(c.bRepBodies.item(0));right_occ=root.occurrences.addNewComponent(core.Matrix3D.create());right=right_occ.component;right.partNumber='CANDIDATE_knee_inner_spacer_right';right.name='Right knee bearing spacer';copy=right.features.copyPasteBodies.add(objects);copy.name='Linked bearing spacer';original=copy.bodies.item(0);objects=core.ObjectCollection.create();objects.add(original);inp=right.features.mirrorFeatures.createInput(objects,right.xZConstructionPlane);inp.isCombine=False;right.features.mirrorFeatures.add(inp).name='Right-hand reflection';right.features.removeFeatures.add(original).name='Keep right-hand spacer';assert right.bRepBodies.count==1
 # The outside cheek follows the bearing stack rather than leaving a partial seat
 # when a different bearing width or span is selected.
 width=d.userParameters.itemByName('lc_shin_width');old_width=width.expression;assert abs(width.value*10-34)<1e-8;width.expression='lc_inner_bearing_lead+lc_bearing_span+lc_bearing_width';assert d.computeAll();p=d.userParameters.itemByName('lc_bearing_span');old=p.expression
 try:
  p.expression='25 mm';assert d.computeAll();changed=c.bRepBodies.item(0).boundingBox;assert abs((changed.maxPoint.y-changed.minPoint.y)*10-17)<.001
  for key in ['shin_inner','shin_outer','shin_inner_right','shin_outer_right','thigh_inner','thigh_outer','thigh_inner_right','thigh_outer_right']:
   part=next(o.component for o in root.occurrences if o.component.partNumber==key);assert part.bRepBodies.count==1 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in part.features)
 finally:p.expression=old;assert d.computeAll()
 paths=[];rows=[]
 for part in [c,right]:
  body=part.bRepBodies.item(0);assert abs((body.boundingBox.maxPoint.y-body.boundingBox.minPoint.y)*10-16)<.001;label=part.partNumber.replace('CANDIDATE_','cohesive-').replace('_','-');path=os.path.join(tempfile.gettempdir(),'tinfox-native',label+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,part));paths.append(path);rows.append({'part':part.partNumber,'features':part.features.count,'sketches':part.sketches.count,'faces':body.faces.count,'edges':body.edges.count})
 print(json.dumps({'parts':rows,'paths':paths,'bearing_span_edit_restored':True,'shin_width_previous_expression':old_width,'shin_width_expression':width.expression,'saved':False}))
'''
r=rpc(s,'cohesive-bearing-spacer',timeout=240);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-bearing-spacer.json').write_text(json.dumps(record,indent=2));print(record)
for path in record['paths']:fetch(path,Path(path).name)
