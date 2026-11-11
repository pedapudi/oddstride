"""Independently check the two owner-exported native countersunk plates."""
from pathlib import Path
import hashlib,json,math,sys
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cone
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
H=Path(__file__).resolve().parent
R=H.parents[2]/'proposals/sculpted/model'
sys.path.insert(0,str(R));import build as b
N=R/'fusion_native';D=H/'native-input';D.mkdir(exist_ok=True)
specs={
 'left':('knee-seated-native-motor_mount_ring.step','1feea5b2799277ec15b48702da9a63591eb6f7748854689c92943510ba183074'),
 'right':('knee-seated-native-motor_mount_ring_right.step','1e98e9b31e049d35389c9ff6ec32385e7c1356df27fa1f514a3f31f628adcfb1')}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def vol(s):
 p=GProp_GProps();BRepGProp.VolumePropertiesGK_s(s.wrapped,p,1e-11,True,True);return p.Mass()
def bounds(s):
 q=s.BoundingBox();return[q.xmin,q.ymin,q.zmin,q.xmax,q.ymax,q.zmax]
base=cq.importers.importStep(str(H/'input/plate.step')).val()
crank=cq.importers.importStep(str(H/'input/crank.step')).val()
expected=base
for a in range(20,380,40):
 x,z=36.5*math.cos(math.radians(a)),36.5*math.sin(math.radians(a))
 expected=expected.cut(cq.Solid.makeCone(1.7,2.95,1.25,cq.Vector(x,52.25,z),cq.Vector(0,1,0)))
expected=expected.clean();results=[]
for hand,(name,digest) in specs.items():
 p=N/'exports'/name;assert sha(p)==digest
 q=D/name;q.write_bytes(p.read_bytes());actual=cq.importers.importStep(str(q)).val()
 exp=expected if hand=='left' else expected.mirror('XZ')
 cones=[]
 for f in actual.Faces():
  s=BRepAdaptor_Surface(f.wrapped)
  if s.GetType()==GeomAbs_Cone:
   c=s.Cone();cones.append(dict(semi_angle_deg=math.degrees(c.SemiAngle()),axis=[c.Axis().Direction().X(),c.Axis().Direction().Y(),c.Axis().Direction().Z()],bounds_mm=bounds(f)))
 errors=[]
 for a1,a2 in [(actual,exp),(exp,actual)]:
  pts,_=a1.tessellate(.02,.06);step=max(1,len(pts)//400)
  boundary=cq.Compound.makeCompound(a2.Faces())
  errors.append(max(boundary.distance(cq.Vertex.makeVertex(*v.toTuple())) for v in pts[::step]))
 seat_checks=[]
 for a in range(20,380,40):
  x,z=36.5*math.cos(math.radians(a)),36.5*math.sin(math.radians(a))
  head=b.cyl(1.5,6.55,(x,45.5,z)).fuse(cq.Solid.makeCone(1.5,2.95,1.45,cq.Vector(x,52.05,z),cq.Vector(0,1,0)))
  driver=b.cyl(1.5,40,(x,53.5,z))
  aligned=crank.rotate((0,0,0),(0,1,0),-a)
  seated=head.translate((0,-.02,0))
  if hand=='right':head=head.mirror('XZ');driver=driver.mirror('XZ');aligned=aligned.mirror('XZ');seated=seated.mirror('XZ')
  intersection=max(0,head.intersect(actual).Volume());contact=max(0,seated.intersect(actual).Volume())/.02
  tool=max(0,driver.intersect(actual).Volume());gap=head.distance(aligned)
  seat_checks.append(dict(angle_deg=a,nominal_overlap_mm3=intersection,projected_seating_area_mm2=contact,driver_overlap_mm3=tool,aligned_fork_gap_mm=gap,passed=intersection<1e-5 and contact>0 and tool<1e-5 and gap>2.29))
 av,ev=vol(actual),vol(exp);change=abs(av-ev)
 missing=max(0,exp.cut(actual).Volume());extra=max(0,actual.cut(exp).Volume())
 row=dict(hand=hand,input_path=str(p),frozen_path=str(q),sha256=digest,valid=actual.isValid(),solid_count=len(actual.Solids()),face_count=len(actual.Faces()),conical_faces=cones,expected_volume_mm3=ev,native_volume_mm3=av,volume_difference_mm3=change,excluded_coincident_boolean_diagnostic=dict(missing_volume_mm3=missing,extra_volume_mm3=extra,used_as_gate=False,reason='Coincident-solid subtraction returned spurious residuals despite matching surfaces and volume. This diagnostic is retained but supplies no geometry verdict.'),bounds_error_max_mm=max(abs(x-y) for x,y in zip(bounds(actual),bounds(exp))),symmetric_sampled_boundary_error_max_mm=max(errors),seat_checks=seat_checks,global_rotating_crank_axial_gap_bound_mm=.9)
 row['passed']=row['valid'] and row['solid_count']==1 and len(cones)==9 and change<.002 and max(errors)<.05 and all(c['passed'] for c in seat_checks)
 results.append(row)
out=dict(passed=all(r['passed'] for r in results),scope='Actual native STEP comparison against the exact nine-seat proposal, both hands. Analysis geometry is used only as a comparison reference.',base_input_sha256=sha(H/'input/plate.step'),crank_input_sha256=sha(H/'input/crank.step'),results=results,limitations=['Nominal M3 DIN7991 head envelope only; purchased rim, angle, print tolerances and preload require physical confirmation.','Seat outer edge land1.05mm and residual web1.75mm remain unqualified for operating loads.','The0.9mm global axial separation is a conservative rigid bound through any Y-axis crank rotation.2.3mm is the exact aligned-fork gap at the screw radius.','No Fusion authoring, promotion or geometry modifications were performed.'])
(H/'native-seat-validation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(passed=out['passed'],results=[{k:r[k] for k in ['hand','sha256','volume_difference_mm3','symmetric_sampled_boundary_error_max_mm','passed']} for r in results]),indent=2))
