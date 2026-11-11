"""Construct the V0 sensor bezel from compact functional native features."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
file_id=json.loads((ROOT/'manifests/subsystems.json').read_text())['subsystems']['head']['file_id']
script=(ROOT/'source/intent_geometry.py').read_text()+'''

def run(_context: str):
 import os,tempfile,json
 app=core.Application.get();doc=next(d for d in app.documents if d.isSaved and d.dataFile.id==HEAD_ID);doc.activate()
 d=fusion.Design.cast(app.activeProduct);root=d.rootComponent
 if doc.isModified:assert root.occurrences.count==1 and root.occurrences.item(0).component.partNumber=='sensor_bezel' and d.timeline.count==1 and not any(p.name.startswith('bezel_') or p.name.startswith('head_face_') for p in d.userParameters),'Unknown modified Head state'
 assert not any(o.component.partNumber=='CANDIDATE_sensor_bezel' for o in root.occurrences)
 occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Sensor bezel - native construction review';c.partNumber='CANDIDATE_sensor_bezel';c.attributes.add('Tinfox','ConstructionStatus','Pending fidelity and parameter-edit audit')
 g=IntentGeometry(d,c)
 settings={'bezel_outer_width':174,'bezel_outer_height':46,'bezel_outer_radius':12,'bezel_inner_width':162,'bezel_inner_height':34,'bezel_inner_radius':8,'bezel_center_z':5,'bezel_front_recess':.7,'bezel_axial_thickness':2.8,'bezel_pocket_depth':1.7,'bezel_tool_start_x':239,'bezel_tool_depth':40}
 for name,value in settings.items():g.parameter(name,value,comment='V0 sensor bezel dimension; independent of motor fits and robot scale')
 outer=g.face_sweep('bezel_front_recess','Outer compound face')
 normal=c.yZConstructionPlane.geometry.normal;plane=g.plane(c.yZConstructionPlane,'bezel_tool_start_x' if normal.x>0 else '-bezel_tool_start_x','Bezel back datum')
 temp=c.sketches.add(plane);p0=temp.modelToSketchSpace(core.Point3D.create(23.9,0,0));pz=temp.modelToSketchSpace(core.Point3D.create(23.9,0,.1));z_is_u=abs(pz.x-p0.x)>.05;zsign=1 if (pz.x-p0.x if z_is_u else pz.y-p0.y)>0 else -1;assert temp.deleteMe()
 center='bezel_center_z' if zsign>0 else '-bezel_center_z'
 def contour(width,height,radius,name):return g.rounded_rectangle(plane,height if z_is_u else width,width if z_is_u else height,radius,'0 mm' if z_is_u else center,name,center if z_is_u else '0 mm')
 sk=contour('bezel_outer_width','bezel_outer_height','bezel_outer_radius','Outside bezel contour')
 mask=g.extrude(sk,'bezel_tool_depth' if normal.x>0 else '-bezel_tool_depth','Outside contour stock').bodies.item(0)
 body=g.combine(mask,[outer],fusion.FeatureOperations.IntersectFeatureOperation,'Trim outer compound face')
 inner=g.face_sweep('bezel_front_recess + bezel_axial_thickness','Inner compound face')
 body=g.combine(body,[inner],fusion.FeatureOperations.CutFeatureOperation,'Set front-to-back bezel thickness')
 opening=contour('bezel_inner_width','bezel_inner_height','bezel_inner_radius','Optical window opening')
 pocket=g.extrude(opening,'bezel_tool_depth' if normal.x>0 else '-bezel_tool_depth','Recess stock').bodies.item(0)
 floor=g.face_sweep('bezel_front_recess + bezel_pocket_depth','Recess floor')
 pocket=g.combine(pocket,[floor],fusion.FeatureOperations.CutFeatureOperation,'Limit recess depth')
 body=g.combine(body,[pocket],fusion.FeatureOperations.CutFeatureOperation,'Cut sensor recess')
 computed=d.computeAll();assert c.bRepBodies.count==1,('body_count',c.bRepBodies.count,'computed',computed,[(b.name,b.volume*1000,b.boundingBox.minPoint.asArray(),b.boundingBox.maxPoint.asArray()) for b in c.bRepBodies],[(f.name,f.errorOrWarningMessage) for f in c.features]);body=c.bRepBodies.item(0);body.name='Sensor bezel'
 issues=[f.name+': '+f.errorOrWarningMessage for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues
 def volume():return c.bRepBodies.item(0).getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000
 before=volume();parameter=d.userParameters.itemByName('head_face_horizontal_crown');old=parameter.expression
 try:parameter.expression='9 mm';d.computeAll();changed=volume();changed_issues=[f.name for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]
 finally:parameter.expression=old;d.computeAll()
 restored=volume();assert abs(changed-before)>.001 and abs(restored-before)<.001 and not changed_issues,(before,changed,restored,changed_issues)
 path=os.path.join(tempfile.gettempdir(),'tinfox-native');step=os.path.join(path,'sensor_bezel-intent.step');stl=os.path.join(path,'sensor_bezel-intent.stl');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(step,c));options=d.exportManager.createSTLExportOptions(c,stl);options.unitType=fusion.DistanceUnits.MillimeterDistanceUnits;options.meshRefinement=fusion.MeshRefinementSettings.MeshRefinementHigh;assert d.exportManager.execute(options)
 occ.isLightBulbOn=False
 print(json.dumps({'part':'sensor_bezel','candidate_part_number':c.partNumber,'head_file_id':doc.dataFile.id,'saved':False,'features':c.features.count,'feature_names':[f.name for f in c.features],'sketches':c.sketches.count,'sketch_entities':sum(s.sketchCurves.count for s in c.sketches),'fitted_spline_count':sum(s.sketchCurves.sketchFittedSplines.count for s in c.sketches),'control_point_spline_count':sum(s.sketchCurves.sketchControlPointSplines.count for s in c.sketches),'faces':body.faces.count,'edges':body.edges.count,'parameter_edit':{'name':parameter.name,'before_mm3':before,'changed_mm3':changed,'restored_mm3':restored,'passed':True},'paths':[step,stl],'source_of_truth_changed':False}))
'''.replace('HEAD_ID',repr(file_id))
r=rpc(script,'sensor-bezel-intent-build',timeout=120);assert r[0].get('success'),r
record=json.loads(r[0]['message']);(ROOT/'audits/sensor-bezel-intent-build.json').write_text(json.dumps(record,indent=2))
for path in record['paths']:fetch(path,Path(path).name)
print(json.dumps(record,indent=2))
