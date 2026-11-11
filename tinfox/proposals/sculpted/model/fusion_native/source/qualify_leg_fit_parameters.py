"""Exercise native fit bindings without changing the nominal migration shape."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json,math,time

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);components={c.partNumber:c for c in d.allComponents if c.partNumber};physical={key:c for key,c in components.items() if c.bRepBodies.count};assert len(physical)==44;started=time.monotonic();rows=[]
 def mm(name):return d.userParameters.itemByName(name).value*10
 def state(c):return {'bounds':[[*b.boundingBox.minPoint.asArray(),*b.boundingBox.maxPoint.asArray()] for b in c.bRepBodies],'volume':[b.volume for b in c.bRepBodies]}
 before={key:state(c) for key,c in physical.items()};names=['fit_bearing_seat_diametral_allowance','fit_print_hole_compensation','fit_cnc_hole_compensation','fit_process_cnc','fit_fork_total_side_clearance','fit_shell_total_seam_gap','fit_spacer_length_adjustment'];baseline={name:d.userParameters.itemByName(name).expression for name in names}
 cases=[('Bearing seat allowance',{'fit_bearing_seat_diametral_allowance':'0.1 mm'}),('Printed shell compensation only',{'fit_print_hole_compensation':'0.1 mm'}),('CNC part compensation only',{'fit_cnc_hole_compensation':'0.04 mm'}),('Select CNC shells',{'fit_print_hole_compensation':'0.1 mm','fit_cnc_hole_compensation':'0.04 mm','fit_process_cnc':'1'}),('Tight fork exercise',{'fit_fork_total_side_clearance':'0.2 mm'}),('Loose fork exercise',{'fit_fork_total_side_clearance':'0.6 mm'}),('Relieve both seam faces',{'fit_shell_total_seam_gap':'0.2 mm'}),('Axial spacer adjustment',{'fit_spacer_length_adjustment':'0.1 mm'})]
 def check():
  seat=mm('lc_bearing_seat_radius');bearing_checks=[]
  for side in ['', '_right']:
   sign=-1 if side else 1
   for half,y,shoulder in [('inner',57,64),('outer',81,75)]:
    key='shin_'+half+side;b=physical[key].bRepBodies.item(0)
    inside=int(b.pointContainment(core.Point3D.create((seat+.02)/10,sign*y/10,0)));outside=int(b.pointContainment(core.Point3D.create((seat-.02)/10,sign*y/10,0)));land=int(b.pointContainment(core.Point3D.create(0,sign*shoulder/10,-1.3)));assert inside==0 and outside==2 and land==0,(key,seat,inside,outside,land);bearing_checks.append({'part':key,'finished_seat_diameter_mm':seat*2,'seat_bracket_pass':True,'axial_land_witness_pass':True})
  gap=mm('lc_drive_fork_gap');center=mm('fit_fork_center_y');near=mm('lc_drive_near_ear_y')+mm('lc_drive_near_ear_depth');far=mm('lc_drive_far_ear_y');assert abs(far-near-gap)<1e-8 and abs((far+near)/2-center)<1e-8;assert abs(mm('lc_rod_y')+mm('lc_rod_thickness')/2-center)<1e-8
  c=components['shin_design_master'];plane=next(p for p in c.constructionPlanes if p.name=='Bushing flange clearance datum');feature=next(f for f in c.features.extrudeFeatures if f.name.startswith('Bushing flange clearance'));assert abs(plane.definition.offset.value*10-(center-gap/2))<1e-8;assert abs(feature.extentOne.distance.value*10-gap)<1e-8
  seams=[];total=mm('fit_shell_total_seam_gap')+mm('fit_seam_compensation')
  for limb in ['shin','thigh']:
   for side in ['', '_right']:
    sign=-1 if side else 1
    for half in ['inner','outer']:
     key=limb+'_'+half+side;y=sign*(mm('lc_shin_split_y')+(1 if half=='outer' else -1)*total/2);faces=[]
     for face in physical[key].bRepBodies.item(0).faces:
      plane=core.Plane.cast(face.geometry)
      if plane and abs(abs(plane.normal.y)-1)<1e-8 and abs(plane.origin.y*10-y)<1e-6 and face.area>.001:faces.append(face.area*100)
     assert faces,(key,y);seams.append({'part':key,'mating_face_y_mm':y,'planar_faces_verified':len(faces)})
  for key,c in physical.items():assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),(key,[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState])
  for c in components.values():assert all(j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for j in c.joints),c.name
  spacer=physical['knee_inner_spacer'].bRepBodies.item(0).boundingBox;length=(spacer.maxPoint.y-spacer.minPoint.y)*10;assert abs(length-mm('lc_knee_spacer_length'))<.001
  return {'bearing_checks':bearing_checks,'seams':seams,'fork_gap_mm':gap,'fork_total_nominal_side_clearance_mm':gap-mm('lc_rod_thickness')-2*mm('fit_bushing_flange_thickness'),'fixed_rod_center_mm':center,'spacer_length_mm':length,'shell_pin_bore_diameter_mm':2*mm('lc_pin_shoulder_clearance'),'crank_pin_bore_diameter_mm':2*mm('fit_crank_pin_shoulder_radius'),'carrier_motor_case_diameter_mm':2*mm('lc_carrier_shell_inner')}
 baseline_checks=check()
 try:
  for label,edits in cases:
   tick=time.monotonic()
   for name,expression in baseline.items():
    desired=edits.get(name,expression);p=d.userParameters.itemByName(name)
    if p.expression!=desired:p.expression=desired
   assert d.computeAll();record=check()
   if label=='Printed shell compensation only':assert abs(record['shell_pin_bore_diameter_mm']-6.2)<1e-8 and abs(record['crank_pin_bore_diameter_mm']-6.1)<1e-8
   if label=='CNC part compensation only':assert abs(record['shell_pin_bore_diameter_mm']-6.1)<1e-8 and abs(record['crank_pin_bore_diameter_mm']-6.14)<1e-8
   if label=='Select CNC shells':assert abs(record['shell_pin_bore_diameter_mm']-6.14)<1e-8
   rows.append({'case':label,'edits':edits,'geometry_checks':record,'passed':True,'seconds':time.monotonic()-tick})
 finally:
  for name,expression in baseline.items():d.userParameters.itemByName(name).expression=expression
  assert d.computeAll()
 restored=check();error=max(abs(a-b) for key,c in physical.items() for aa,bb in zip(before[key]['bounds'],state(c)['bounds']) for a,b in zip(aa,bb));assert error<1e-7,error
 for key,c in physical.items():assert max(abs(a-b) for a,b in zip(before[key]['volume'],state(c)['volume']))<1e-5,key
 print(json.dumps({'passed':True,'saved':False,'cases':rows,'baseline':baseline_checks,'restored':restored,'baseline_geometry_restored':True,'maximum_restored_bound_error_cm':error,'elapsed_seconds':time.monotonic()-started,'physical_fit_qualified':False,'scope':'Deterministic CAD edit exercises and complete seat/land witnesses. Manufacturing variation is not yet measured; these are not production fit profiles or loaded strength tests.'}))
'''
r=rpc(s,'native-leg-fit-qualification',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/native-leg-fit-qualification.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'cases':len(record['cases']),'seconds':record['elapsed_seconds']})
