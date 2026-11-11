"""Rebuild the V0 service face from its lip, compound crown and fastener seats."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
script=(ROOT/'source/intent_geometry.py').read_text()+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent
 assert not any(o.component.partNumber=='CANDIDATE_front_fascia' for o in root.occurrences)
 occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Front fascia - native construction review';c.partNumber='CANDIDATE_front_fascia';g=IntentGeometry(d,c)
 for name,value in {'nose_fascia_thickness':2.1,'nose_post_half_y':89,'nose_post_half_z':27,'nose_post_radius':3.5,'fascia_pilot_clearance_radius':1.7,'fascia_screw_seat_radius':2.7,'fascia_screw_seat_recess':.6,'fascia_back_trim_x':'head_face_reference_x - 2.4 mm'}.items():g.parameter(name,value,comment='V0 service-face interface or dimension')
 g.face_parameters()
 def blank(inset,label):
  profiles=[]
  for index,(dx,w,h,r) in enumerate([(-4.1,200.3,87.7,18),(-1.9,196.5,83.5,17),(30.6,192.5,80,16)]):
   prefix='fascia_'+label.lower()+'_'+str(index+1)+'_'
   for key,expr in {'x':'head_face_reference_x + '+str(dx)+' mm','width':'body_envelope_width - '+str(222.4-w)+' mm - 2*('+inset+')','height':str(h)+' mm - 2*('+inset+')','radius':str(r)+' mm - ('+inset+')'}.items():g.parameter(prefix+key,expr,comment='Derived fascia lip station')
   profiles.append(g.yz_contour(prefix+'x',prefix+'width',prefix+'height',prefix+'radius','2 mm',label+' lip profile '+str(index+1)))
  first=g.loft(profiles[:2],label+' rear lip');second=g.loft(profiles[1:],label+' forward taper');return g.combine(first,[second],fusion.FeatureOperations.JoinFeatureOperation,label+' lip envelope')
 outer=blank('0 mm','Outer');inner=blank('nose_fascia_thickness','Inner')
 front=g.face_sweep('0 mm','Fascia compound front');back=g.face_sweep('nose_fascia_thickness','Fascia compound inside')
 face=g.combine(outer,[front],fusion.FeatureOperations.IntersectFeatureOperation,'Trim compound front');inner=g.combine(inner,[back],fusion.FeatureOperations.IntersectFeatureOperation,'Trim compound inside');face=g.combine(face,[inner],fusion.FeatureOperations.CutFeatureOperation,'Hollow service face')
 aperture=g.yz_contour('head_face_reference_x - 5.4 mm','168 mm','40 mm','10 mm','5 mm','Sensor opening');g.extrude(aperture,'40 mm','Cut sensor opening',fusion.FeatureOperations.CutFeatureOperation,[face]);face=next(b for b in c.bRepBodies if b.entityToken==face.entityToken)
 pilots=g.circle_grid_yz('head_face_reference_x - 6.4 mm','nose_post_half_y','nose_post_half_z','fascia_pilot_clearance_radius','0 mm','Four fascia screw clearances');g.extrude_all(pilots,'30 mm','Clear fascia screws',fusion.FeatureOperations.CutFeatureOperation,[face])
 for sign,label in [(-1,'Lower'),(1,'Upper')]:
  zexpr=('' if sign>0 else '-')+'nose_post_half_z';xexpr='head_face_reference_x + head_face_horizontal_crown*(1-(nose_post_half_y/head_face_half_width)^2) + head_face_vertical_crown*(1-(('+zexpr+'-head_face_center_z)/head_face_half_height)^2) - fascia_screw_seat_recess'
  g.parameter('fascia_'+label.lower()+'_seat_x',xexpr,comment='Screw seat follows the actual compound front crown')
  plane=g.plane(c.yZConstructionPlane,'fascia_'+label.lower()+'_seat_x',label+' screw seat datum');sk=c.sketches.add(plane);sk.name=label+' screw seats'
  points=[g.skeleton_point(sk,'-('+zexpr+')','-nose_post_half_y'),g.skeleton_point(sk,'-('+zexpr+')','nose_post_half_y')];g.point_dimensions(sk,points[0],'-('+zexpr+')','-nose_post_half_y');g.point_dimensions(sk,points[1],None,'nose_post_half_y');sk.geometricConstraints.addVerticalPoints(*points)
  circles=[]
  for point in points:
   circle=sk.sketchCurves.sketchCircles.addByCenterRadius(point.geometry,g.mm('fascia_screw_seat_radius')*.1);sk.geometricConstraints.addCoincident(circle.centerSketchPoint,point)
   if circles:sk.geometricConstraints.addEqual(circles[0],circle)
   else:sk.sketchDimensions.addRadialDimension(circle,core.Point3D.create(point.geometry.x+.4,point.geometry.y+.4,0)).parameter.expression='fascia_screw_seat_radius'
   circles.append(circle)
  g.extrude_all(sk,'1.8 mm',label+' flush screw seats',fusion.FeatureOperations.CutFeatureOperation,[face])
 plane=g.plane(c.yZConstructionPlane,'head_face_reference_x - 45.4 mm','Rear service seam cut datum');sk=g.rectangle(plane,'150 mm','300 mm','0 mm','0 mm','Rear seam trim');g.extrude(sk,'fascia_back_trim_x - (head_face_reference_x - 45.4 mm)','Trim rear service seam',fusion.FeatureOperations.CutFeatureOperation,[face])
 assert d.computeAll();assert c.bRepBodies.count==1;body=c.bRepBodies.item(0);body.name='Front fascia'
 issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','front_fascia-intent.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));occ.isLightBulbOn=False
 print(json.dumps({'part':'front_fascia','features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'fitted_splines':sum(s.sketchCurves.sketchFittedSplines.count for s in c.sketches),'path':path,'saved':False}))
'''
r=rpc(script,'front-fascia-intent-build',timeout=180);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/front-fascia-intent-build.json').write_text(json.dumps(record,indent=2));fetch(record['path'],Path(record['path']).name);print(json.dumps(record))
