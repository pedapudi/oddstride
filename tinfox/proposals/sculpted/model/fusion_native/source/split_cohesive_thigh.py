"""Create linked thigh clamshell halves with simple integral revolved axle stops."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1];proof=json.loads((ROOT/'audits/cohesive-thigh-stop-equivalence.json').read_text());assert all(row['source_only_mm3']<.001 and row['native_only_mm3']<.001 for row in proof)
s='\n'.join((ROOT/'source'/p).read_text() for p in ['intent_geometry.py','cohesive_limb_intent.py','cohesive_thigh_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;master=next(o for o in root.occurrences if o.component.partNumber=='CANDIDATE_cohesive_thigh_master');assert master.component.features.count==27;rows=[];paths=[]
 for outer in [False,True]:
  side='outer' if outer else 'inner';key='CANDIDATE_cohesive_thigh_'+side;assert not any(o.component.partNumber==key for o in root.occurrences);occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.partNumber=key;c.name='Cohesive thigh '+side+' shell';g=IntentGeometry(d,c);objects=core.ObjectCollection.create();objects.add(master.component.bRepBodies.item(0));copy=c.features.copyPasteBodies.add(objects);copy.name='Linked shared structural thigh';assert copy.isParametric;body=copy.bodies.item(0);plane=g.plane(c.xZConstructionPlane,'lc_shin_split_y','Shared limb split datum');inp=c.features.splitBodyFeatures.createInput(body,plane,True);f=c.features.splitBodyFeatures.add(inp);f.name='Split thigh structural shell';assert c.bRepBodies.count==2;remove=next(b for b in c.bRepBodies if (b.boundingBox.maxPoint.y<g.mm('lc_shin_split_y')/10+1e-6)==outer);c.features.removeFeatures.add(remove).name='Keep '+side+' structural half';body=c.bRepBodies.item(0)
  for name,value in {'lc_stop_radial_gap':.3,'lc_stop_axial_gap':.3,'lc_stop_recess_depth':1,'lc_stop_race_land_width':1.3,'lc_stop_shaft_relief_radius':8.2,'lc_inner_stop_boss_radius':11.2,'lc_axle_fit_radius':6.1,'lc_outer_stop_overlap':3}.items():g.parameter(name,value)
  for name,value in {'lc_stop_outer_radius':'lc_bearing_od/2-lc_stop_radial_gap','lc_stop_recess_radius':'lc_stop_outer_radius-lc_stop_race_land_width','lc_inner_stop_end':'lc_bearing_inner_y-lc_stop_axial_gap','lc_outer_stop_start':'lc_bearing_outer_y+lc_bearing_width+lc_stop_axial_gap','lc_outer_stop_base_radius':'lc_bearing_od/2+2 mm','lc_outer_stop_base_y':'lc_knee_cavity_y+lc_knee_cavity_width'}.items():g.parameter(name,value)
  if outer:
   profile=[('lc_stop_outer_radius','lc_outer_stop_start'),('lc_stop_outer_radius','lc_outer_stop_base_y'),('lc_outer_stop_base_radius','lc_outer_stop_base_y'),('lc_outer_stop_base_radius','lc_thigh_outer_y-lc_outer_stop_overlap'),('lc_axle_fit_radius','lc_thigh_outer_y-lc_outer_stop_overlap'),('lc_axle_fit_radius','lc_outer_stop_base_y'),('lc_stop_shaft_relief_radius','lc_outer_stop_base_y'),('lc_stop_shaft_relief_radius','lc_outer_stop_start+lc_stop_recess_depth'),('lc_stop_recess_radius','lc_outer_stop_start+lc_stop_recess_depth'),('lc_stop_recess_radius','lc_outer_stop_start')]
  else:
   profile=[('lc_stop_outer_radius','lc_knee_cavity_y'),('lc_stop_outer_radius','lc_inner_stop_end'),('lc_stop_recess_radius','lc_inner_stop_end'),('lc_stop_recess_radius','lc_inner_stop_end-lc_stop_recess_depth'),('lc_inner_stop_boss_radius','lc_inner_stop_end-lc_stop_recess_depth'),('lc_inner_stop_boss_radius','lc_inner_stop_end-lc_stop_axial_gap'),('lc_axle_fit_radius','lc_inner_stop_end-lc_stop_axial_gap'),('lc_axle_fit_radius','lc_knee_cavity_y')]
  plane=g.plane(c.xYConstructionPlane,'-lc_thigh_length','Knee shaft center');sk=c.sketches.add(plane);sk.name='Integral '+side+' axial stop section';sk.isComputeDeferred=True;xs={};ys={};points=[]
  for x,y in profile:
   p=g.skeleton_point(sk,x,y);g.point_dimensions(sk,p,None if x in xs else x,None if y in ys else y)
   if x in xs:sk.geometricConstraints.addVerticalPoints(xs[x],p)
   if y in ys:sk.geometricConstraints.addHorizontalPoints(ys[y],p)
   xs[x]=p;ys[y]=p;points.append(p)
  for i,p in enumerate(points):sk.sketchCurves.sketchLines.addByTwoPoints(p,points[(i+1)%len(points)])
  axis=sk.sketchCurves.sketchLines.addByTwoPoints(sk.originPoint,core.Point3D.create(0,1,0));axis.isConstruction=True;sk.geometricConstraints.addVertical(axis);dim=sk.sketchDimensions.addDistanceDimension(axis.startSketchPoint,axis.endSketchPoint,fusion.DimensionOrientations.AlignedDimensionOrientation,core.Point3D.create(.5,.5,0));dim.parameter.expression='10 mm';sk.isComputeDeferred=False;assert sk.profiles.count==1,sk.profiles.count;inp=c.features.revolveFeatures.createInput(sk.profiles.item(0),axis,fusion.FeatureOperations.JoinFeatureOperation);inp.setAngleExtent(False,g.value('360 deg'));f=c.features.revolveFeatures.add(inp);f.name='Integral bearing backup and axle boss';assert c.bRepBodies.count==1;body=c.bRepBodies.item(0);sk.isLightBulbOn=False
  path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-thigh-'+side+'-stops.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));paths.append(path);rows.append({'part':key,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count})
 master.isLightBulbOn=False;print(json.dumps({'parts':rows,'paths':paths,'saved':False}))
'''
r=rpc(s,'cohesive-thigh-shell-splits',timeout=240);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-thigh-shell-splits.json').write_text(json.dumps(record,indent=2));print(record)
for path in record['paths']:fetch(path,Path(path).name)
