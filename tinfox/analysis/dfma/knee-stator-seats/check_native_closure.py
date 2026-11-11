"""Read-only actual-native reinforced cup/closure comparison and service audit."""
from pathlib import Path
import contextlib,hashlib,io,json,math,sys
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
with contextlib.redirect_stdout(io.StringIO()):import check_closure_recess as p
b=p.b;N=p.N;D=H/'recessed-native-input';D.mkdir(exist_ok=True)
specs={
 'closure':('recessed-native-hip_stator_closure_1.step','62c564ec5ae214af874314ff593a52355f07c5efb2253ac88e152caaaa603ee2'),
 'front':('recessed-native-motor_carrier_1.step','7da3e8c1e56d3b5813aa9627c0f4eb071141e36205748be30af506cc60d95859'),
 'rear':('recessed-native-motor_carrier_-1.step','b1b1d74ab9c7bd042c40181e718e89e72e8e33d6b7cd76a0392c8c8b9c5cb8d4')}
actual={};inputs={}
for k,(name,digest) in specs.items():
 path=N/'exports'/name;raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==digest
 dst=D/name;dst.write_bytes(raw);actual[k]=cq.importers.importStep(str(dst)).val();inputs[k]=dict(path=str(path),sha256=digest,frozen_path=str(dst))
def volume(s):
 props=GProp_GProps();BRepGProp.VolumePropertiesGK_s(s.wrapped,props,1e-11,True,True);return props.Mass()
def overlap(a,c):return max(0,sum(s.Volume() for s in a.intersect(c).Solids()))
def bounds(s):
 q=s.BoundingBox();return[q.xmin,q.ymin,q.zmin,q.xmax,q.ymax,q.zmax]
comparisons=[]
references={'closure':p.newclosure.translate((5,0,0)),'front':p.newcup.translate((5,0,0))}
# Rear carrier has its independently mirrored journal but preserves the same
# cup port clocking. Build its comparison from its actual frozen parent.
rearpath=N/'exports/paired-native-motor_carrier_-1.step'
rear=cq.importers.importStep(str(rearpath)).val()
for a in (90,215,325):
 x,z=p.polar(47,a);x-=5
 rear=rear.cut(b.cyl(6.1,5,(x,-5.1,z)))
 rear=rear.fuse(b.ring(4.8,2.2,1.1,-5.2,z,x))
references['rear']=rear
inputs['rear_parent']=dict(path=str(rearpath),sha256=hashlib.sha256(rearpath.read_bytes()).hexdigest())
for key,expected in references.items():
 solid=actual[key];errors=[]
 for a,c in [(solid,expected),(expected,solid)]:
  points,_=a.tessellate(.02,.06);step=max(1,len(points)//500);target=cq.Compound.makeCompound(c.Faces())
  errors.append(max(target.distance(cq.Vertex.makeVertex(*v.toTuple())) for v in points[::step]))
 sv,ev=volume(solid),volume(expected)
 row=dict(part=key,valid=solid.isValid(),solids=len(solid.Solids()),faces=len(solid.Faces()),expected_volume_mm3=ev,native_volume_mm3=sv,absolute_volume_error_mm3=abs(sv-ev),relative_volume_error=abs(sv-ev)/ev,symmetric_sampled_surface_error_max_mm=max(errors),bounds_error_max_mm=max(abs(a-c) for a,c in zip(bounds(solid),bounds(expected))))
 row['passed']=row['valid'] and row['solids']==1 and row['relative_volume_error']<.001 and max(errors)<.05
 comparisons.append(row)
closure=actual['closure'].translate((-5,0,0));front=actual['front'].translate((-5,0,0));back=actual['rear'].translate((5,0,0))
service=[]
for name,cup in [('front',front),('rear',back)]:
 for delta in (0,.01,.05,.1,.25,.5,1,1.1,2,3,5,10,25):
  moved=closure.translate((0,delta,0));hit=overlap(moved,cup)
  service.append(dict(cup=name,closure_withdrawal_plusY_mm=delta,overlap_mm3=hit,passed=hit<1e-5))
seat=[]
interfaces=[]
for key in ('closure','front','rear'):
 rows=[]
 for face in actual[key].Faces():
  adaptor=BRepAdaptor_Surface(face.wrapped)
  if adaptor.GetType()!=GeomAbs_Cylinder:continue
  c=adaptor.Cylinder();radius=c.Radius();axis=c.Axis().Direction();loc=c.Location()
  if abs(axis.Y())>.999999 and any(abs(radius-r)<1e-6 for r in (2.4,4.1,4.8,4.95,6.1)):
   rows.append(dict(radius_mm=radius,axis_line_xz_mm=[loc.X(),loc.Z()],bounds_mm=bounds(face)))
 expected_radii=(2.4,4.1,4.95) if key=='closure' else (4.8,6.1)
 errors=[]
 for radius in expected_radii:
  for angle in (90,215,325):
   x,z=p.polar(47,angle);x+=-5 if key=='rear' else 5
   errors.append(min(max(abs(row['radius_mm']-radius),abs(row['axis_line_xz_mm'][0]-x),abs(row['axis_line_xz_mm'][1]-z)) for row in rows))
 interfaces.append(dict(part=key,relevant_y_axis_cylinders=rows,critical_radius_position_error_max_mm=max(errors),passed=max(errors)<1e-4 and len(rows)==len(expected_radii)*3))
for a in (90,215,325):
 x,z=p.polar(47,a)
 screw=b.cyl(2,16,(x,-18.2,z)).fuse(b.cyl(3.8,2.2,(x,-2.2,z)))
 hit=overlap(screw,closure);land=overlap(screw.translate((0,-.02,0)),closure)/.02
 driver=b.cyl(1.6,40,(x,0,z))
 seat.append(dict(kind='closure_button',angle_deg=a,seated_overlap_mm3=hit,seated_contact_area_mm2=land,driver_overlap_mm3=overlap(driver,closure),cup_overlap_mm3=overlap(screw,front),head_max_y_mm=0,passed=hit<1e-5 and land>27 and overlap(driver,closure)<1e-5 and overlap(screw,front)<1e-5))
for a in range(0,360,40):
 x,z=p.polar(36.5,a)
 screw=b.cyl(1.5,6.55,(x,-8.9,z)).fuse(cq.Solid.makeCone(1.5,2.95,1.45,cq.Vector(x,-2.35,z),cq.Vector(0,1,0)))
 before=overlap(screw.translate((0,-.02,0)),closure)/.02
 seated=screw.translate((0,-.2,0));hit=overlap(seated,closure);land=overlap(seated.translate((0,-.02,0)),closure)/.02
 seat.append(dict(kind='hip_stator',angle_deg=a,reference_shift_mm=[0,-.2,0],unshifted_002mm_down_contact_area_mm2=before,seated_overlap_mm3=hit,seated_contact_area_mm2=land,motor_thread_penetration_mm=5.1,conservative6mm_penetration_margin_mm=.9,passed=hit<1e-5 and land>0 and before<1e-5))
for hand,cup in [('front',actual['front']),('rear',actual['rear'])]:
 for a in range(0,360,60):
  y,z=p.polar(12,a)
  screw=b.cyl(2,22.7,(-77.5,y,z),(1,0,0)).fuse(cq.Solid.makeCone(2,4.3,2.3,cq.Vector(-54.8,y,z),cq.Vector(1,0,0)))
  if hand=='rear':screw=screw.mirror('YZ')
  d=-1 if hand=='front' else 1
  before=overlap(screw.translate((.02*d,0,0)),cup)/.02
  seated=screw.translate((.2*d,0,0));hit=overlap(seated,cup);land=overlap(seated.translate((.02*d,0,0)),cup)/.02
  seat.append(dict(kind='roll_output',hand=hand,angle_deg=a,reference_shift_mm=[.2*d,0,0],unshifted_002mm_down_contact_area_mm2=before,seated_overlap_mm3=hit,seated_contact_area_mm2=land,motor_thread_penetration_mm=4.2,conservative6mm_penetration_margin_mm=1.8,manufacturer7mm_minimum_depth_reserve_mm=2.8,passed=hit<1e-5 and land>0 and before<1e-5))
sections=[]
for hand,new,old,sign in [('front',front,p.cup,1),('rear',back,cq.importers.importStep(str(rearpath)).val().translate((5,0,0)),-1)]:
 region=b.box(120,21,60,(-55*sign,-14.5,0));old=old.intersect(region);new=new.intersect(region)
 for x in (-54,-52,-50,-48,-46,-45,-44.5,-44,-43.5,-43,-42.5,-42,-41.5,-41,-40.9):
  plane=cq.Face.makePlane(basePnt=(x*sign,0,0),dir=(1,0,0));properties=[]
  for s in (old,new):
   q=s.intersect(plane);props=GProp_GProps();BRepGProp.SurfaceProperties_s(q.wrapped,props,1e-10,True);matrix=props.MatrixOfInertia()
   properties.append(dict(area_mm2=props.Mass(),Iyy_mm4=matrix.Value(2,2),Izz_mm4=matrix.Value(3,3)))
  before,after=properties
  sections.append(dict(hand=hand,pitch_local_x_mm=x*sign,before=before,after=after,area_retained_fraction=after['area_mm2']/before['area_mm2'],Iyy_retained_fraction=after['Iyy_mm4']/before['Iyy_mm4'],Izz_retained_fraction=after['Izz_mm4']/before['Izz_mm4']))
out=dict(passed=all(r['passed'] for r in comparisons+interfaces+service+seat),scope='Actual native exports compared with independent reinforced-seat proposal; nominal contact and sampled axial service path.',inputs=inputs,comparisons=comparisons,critical_cylinder_interfaces=interfaces,closure_service_path=service,reference_seating_checks=seat,retained_native_web_sections=sections,section_summary=dict(minimum_native_area_mm2=min(s['after']['area_mm2'] for s in sections),minimum_area_retained_fraction=min(s['area_retained_fraction'] for s in sections),minimum_Iyy_retained_fraction=min(s['Iyy_retained_fraction'] for s in sections),minimum_Izz_retained_fraction=min(s['Izz_retained_fraction'] for s in sections)),reference_placement_decision='Seat only the existing hip references by−0.2Y and the front roll output references by−0.2X, reversedX for rear. Do not move the independent knee references or custom motor planes.',limitations=['Finite removal samples supplement the parallel coaxial open-pocket geometry; printed fits and deflection are not qualified.','The exact modeled cone references are nominal. Purchased head rim/angle/length tolerances need physical measurement.','Depth8mm M3 and7mmMIN M4 are manufacturer drawing values; physical motor-thread and tip-clearance confirmation remains required.','Native section properties are finite geometric measurements, not manufactured strength or stiffness qualification.','No native authoring, authority changes, release or powered actions were performed.'])
(H/'native-closure-validation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(passed=out['passed'],comparisons=comparisons,failed_service=[r for r in service if not r['passed']],failed_seat=[r for r in seat if not r['passed']]),indent=2))
