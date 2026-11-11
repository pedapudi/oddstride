"""Native eye link and cut-stock sleeves driven by shared limb assembly datums."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text() for p in ['intent_geometry.py','cohesive_limb_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;rows=[];paths=[];made=[]
 def component(key,name):
  assert not any(o.component.partNumber=='CANDIDATE_'+key for o in root.occurrences);occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.partNumber='CANDIDATE_'+key;c.name=name;return c,IntentGeometry(d,c),CohesiveLimbIntent(IntentGeometry(d,c))
 c,g,n=component('pushrod','Parallel knee linkage eye rod');g.parameter('lc_rod_length','lc_thigh_length');d.userParameters.itemByName('lc_rod_length').expression='lc_thigh_length'
 for key,value in {'lc_rod_eye_radius':7.5,'lc_rod_eye_bore':4,'lc_rod_stem_half_width':3,'lc_rod_eye_transition':12,'lc_rod_thickness':6,'lc_compression_sleeve_outer_radius':4,'lc_rear_sleeve_inner_radius':2.15,'lc_front_sleeve_inner_radius':2.2,'lc_axle_outer_radius':6,'lc_axle_inner_radius':4.2,'lc_axle_outer_overhang':9.5}.items():g.parameter(key,value)
 g.parameter('lc_rod_y','lc_drive_near_ear_y+lc_drive_near_ear_depth+lc_drive_fork_gap/2-lc_rod_thickness/2');g.parameter('lc_axle_end_y','lc_bearing_outer_y+lc_bearing_width+lc_axle_outer_overhang')
 plane=g.plane(c.xZConstructionPlane,'lc_rod_y','Rod center plane datum');sk=c.sketches.add(plane);sk.name='Two circular eyes with tapered six millimeter web';origin=g.skeleton_point(sk,'0 mm','0 mm');sk.geometricConstraints.addCoincident(origin,sk.originPoint);end=g.skeleton_point(sk,'0 mm','lc_rod_length');g.point_dimensions(sk,end,'0 mm','lc_rod_length');upper,left,right=g.driven_arc(sk,origin,'lc_rod_eye_radius','-180 deg','0 deg','Motor eye');lower,lower_right,lower_left=g.driven_arc(sk,end,'lc_rod_eye_radius','0 deg','180 deg','Knee eye')
 for sign,start,finish in [(1,right,lower_right),(-1,lower_left,left)]:
  expressions=[(f'{sign}*lc_rod_stem_half_width','lc_rod_eye_transition'),(f'{sign}*lc_rod_stem_half_width','lc_rod_length-lc_rod_eye_transition')]
  if sign<0:expressions.reverse()
  points=[start]
  for x,y in expressions:p=g.skeleton_point(sk,x,y);g.point_dimensions(sk,p,x,y);points.append(p)
  points.append(finish)
  for a,b in zip(points,points[1:]):sk.sketchCurves.sketchLines.addByTwoPoints(a,b)
 assert sk.profiles.count==1;body=g.extrude(sk,'lc_rod_thickness','Integral eye-ended link').bodies.item(0);bores=n.circles('lc_rod_y-1 mm',[('0 mm','0 mm','lc_rod_eye_bore'),('0 mm','-lc_rod_length','lc_rod_eye_bore')],'Paired replaceable bushing seats');n.extrude_all(bores,'lc_rod_thickness+2 mm','Two eight millimeter bushing bores',fusion.FeatureOperations.CutFeatureOperation,body);made.append(c)
 definitions=[('sleeve_0','Rear thigh compression sleeve','lc_thigh_clamp_rear_x','lc_thigh_clamp_rear_z','lc_thigh_rear_sleeve_start','lc_thigh_rear_sleeve_end-lc_thigh_rear_sleeve_start','lc_compression_sleeve_outer_radius','lc_rear_sleeve_inner_radius'),('sleeve_1','Front thigh compression sleeve','lc_thigh_clamp_front_x','lc_thigh_clamp_front_z','lc_thigh_front_sleeve_start','lc_thigh_front_sleeve_end-lc_thigh_front_sleeve_start','lc_compression_sleeve_outer_radius','lc_front_sleeve_inner_radius'),('knee_axle','Removable knee axle sleeve','0 mm','-lc_thigh_length','lc_axle_head_end_y','lc_axle_end_y-lc_axle_head_end_y','lc_axle_outer_radius','lc_axle_inner_radius')]
 for key,name,x,z,y,depth,outer,inner in definitions:
  c,g,n=component(key,name);plane=g.plane(c.xZConstructionPlane,y,name+' datum');sk=c.sketches.add(plane);sk.name=name+' section';center=g.skeleton_point(sk,x,'-('+z+')');g.point_dimensions(sk,center,x,'-('+z+')')
  for radius in [outer,inner]:
   circle=sk.sketchCurves.sketchCircles.addByCenterRadius(center.geometry,g.mm(radius)/10);sk.geometricConstraints.addCoincident(circle.centerSketchPoint,center);dim=sk.sketchDimensions.addRadialDimension(circle,core.Point3D.create(.7,17.7,0));dim.parameter.expression=radius
  profile=next(p for p in sk.profiles if p.profileLoops.count==2);inp=c.features.extrudeFeatures.createInput(profile,fusion.FeatureOperations.NewBodyFeatureOperation);inp.setDistanceExtent(False,g.value(depth));f=c.features.extrudeFeatures.add(inp);f.name='Cut stock to assembly spacing';sk.isLightBulbOn=False;made.append(c)
 for source in list(made):
  occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.partNumber=source.partNumber+'_right';c.name='Right '+source.name.lower();objects=core.ObjectCollection.create();objects.add(source.bRepBodies.item(0));f=c.features.copyPasteBodies.add(objects);f.name='Linked assembly-driven native part';original=f.bodies.item(0);objects=core.ObjectCollection.create();objects.add(original);inp=c.features.mirrorFeatures.createInput(objects,c.xZConstructionPlane);inp.isCombine=False;c.features.mirrorFeatures.add(inp).name='Right-hand reflection';c.features.removeFeatures.add(original).name='Keep handed part';made.append(c)
 assert d.computeAll()
 for c in made:
  assert c.bRepBodies.count==1;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);b=c.bRepBodies.item(0);label='cohesive-'+c.partNumber.replace('CANDIDATE_','').replace('_','-');path=os.path.join(tempfile.gettempdir(),'tinfox-native',label+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));paths.append(path);rows.append({'part':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'faces':b.faces.count,'edges':b.edges.count})
 before={c.partNumber:c.bRepBodies.item(0).boundingBox.minPoint.z for c in made};p=d.userParameters.itemByName('lc_thigh_length');old=p.expression
 try:
  p.expression='180 mm';assert d.computeAll()
  for c in made:assert c.bRepBodies.count==1 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);assert c.bRepBodies.item(0).boundingBox.minPoint.z<before[c.partNumber]-.1
 finally:p.expression=old;assert d.computeAll()
 for c in made:assert abs(c.bRepBodies.item(0).boundingBox.minPoint.z-before[c.partNumber])<1e-7
 print(json.dumps({'passed':True,'parts':rows,'paths':paths,'thigh_length_edit_restored':True,'saved':False}))
'''
r=rpc(s,'cohesive-link-sleeves',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-link-sleeves.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k!='parts'})
for path in record['paths']:fetch(path,Path(path).name)
