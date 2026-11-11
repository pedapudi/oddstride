"""Cut the folded-foot swept volume using a native circular sweep and end caps."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text() for p in ['intent_geometry.py','cohesive_limb_intent.py','cohesive_thigh_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);c=next(o.component for o in d.rootComponent.occurrences if o.component.partNumber=='CANDIDATE_cohesive_thigh_master');assert c.features.count==23;g=IntentGeometry(d,c);g.parameter('lc_folded_foot_clearance_radius',23.5);body=c.bRepBodies.item(0)
 plane=g.plane(c.xZConstructionPlane,'lc_shin_split_y','Foot sweep center plane');path_sk=c.sketches.add(plane);path_sk.name='Knee range and foot-center orbit';center=g.skeleton_point(path_sk,'0 mm','lc_thigh_length');g.point_dimensions(path_sk,center,'0 mm','lc_thigh_length');arc,start,end=g.driven_arc(path_sk,center,'lc_shank_foot_center','lc_knee_min+90 deg','lc_knee_max+90 deg','Folded foot orbit');path=c.features.createPath(arc,False)
 inp=c.constructionPlanes.createInput();assert inp.setByPath(path,fusion.PathDistanceTypes.ProportionalPathDistanceType,core.ValueInput.createByReal(0));normal=c.constructionPlanes.add(inp);normal.name='Foot section normal to orbit';sk=c.sketches.add(normal);sk.name='Foot clearance section';p=sk.project2([start],True);assert len(p)==1;p=p[0];circle=sk.sketchCurves.sketchCircles.addByCenterRadius(p.geometry,g.mm('lc_folded_foot_clearance_radius')/10);sk.geometricConstraints.addCoincident(circle.centerSketchPoint,p);dim=sk.sketchDimensions.addRadialDimension(circle,core.Point3D.create(p.geometry.x+.5,p.geometry.y+.5,0));dim.parameter.expression='lc_folded_foot_clearance_radius';assert sk.profiles.count==1
 inp=c.features.sweepFeatures.createInput(sk.profiles.item(0),path,fusion.FeatureOperations.NewBodyFeatureOperation);inp.orientation=fusion.SweepOrientationTypes.PerpendicularOrientationType;f=c.features.sweepFeatures.add(inp);f.name='Continuous folded-foot clearance sweep';tools=[f.bodies.item(0)];sk.isLightBulbOn=False;path_sk.isLightBulbOn=False
 for bound in ['min','max']:
  sk=c.sketches.add(plane);sk.name='Foot '+bound+' endpoint cap';x='-lc_shank_foot_center*sin(lc_knee_'+bound+')';z='lc_thigh_length+lc_shank_foot_center*cos(lc_knee_'+bound+')';p=g.skeleton_point(sk,x,z);g.point_dimensions(sk,p,x,z);arc,first,last=g.driven_arc(sk,p,'lc_folded_foot_clearance_radius','-90 deg','90 deg','Foot cap');axis=sk.sketchCurves.sketchLines.addByTwoPoints(first,last);assert sk.profiles.count==1;inp=c.features.revolveFeatures.createInput(sk.profiles.item(0),axis,fusion.FeatureOperations.NewBodyFeatureOperation);inp.setAngleExtent(False,g.value('360 deg'));f=c.features.revolveFeatures.add(inp);f.name='Spherical foot '+bound+' endpoint';tools.append(f.bodies.item(0));sk.isLightBulbOn=False
 body=g.combine(body,tools,fusion.FeatureOperations.CutFeatureOperation,'Folded foot clearance');assert c.bRepBodies.count==1;path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-thigh-master.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));print(json.dumps({'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'paths':[path],'saved':False}))
'''
r=rpc(s,'cohesive-thigh-foot-sweep',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-thigh-foot-sweep.json').write_text(json.dumps(record,indent=2));print(record)
for path in record['paths']:fetch(path,Path(path).name)
