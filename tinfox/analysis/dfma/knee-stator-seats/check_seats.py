"""Read-only source and proposed countersink review; no native geometry writes."""
from pathlib import Path
import hashlib,json,math,shutil,sys
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Plane
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]/'proposals/sculpted/model'
sys.path.insert(0,str(ROOT));import build as b
N=ROOT/'fusion_native'
INPUT=HERE/'input';INPUT.mkdir(parents=True,exist_ok=True)
sources={'plate':(N/'exports/slim-native-motor_mount_ring-restored.step','f06bf3ee803e7e585ee79eace1fa6c2618d3d9bca1a0db0ae98276fc51462020'),
 'crank':(N/'exports/motor-complex-native-input_crank.step','277beedc5cd650be48df2acd5ad717aefb8fc3ea4a33e03fff6632eb419ccbb5')}
solids={};inputs={}
for key,(p,expected) in sources.items():
 raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==expected
 q=INPUT/(key+'.step');q.write_bytes(raw);solids[key]=cq.importers.importStep(str(q)).val();inputs[key]=dict(source_path=str(p),frozen_path=str(q),sha256=expected)
plate,crank=solids['plate'],solids['crank']
faces=[]
for face in plate.Faces():
 adaptor=BRepAdaptor_Surface(face.wrapped)
 if adaptor.GetType()==GeomAbs_Plane and abs(face.Center().y-53.5)<1e-6:
  normal=adaptor.Plane().Axis().Direction()
  if abs(normal.Y())>.999:faces.append(face)
top=max(faces,key=lambda f:f.Area());outer_boundary=top.outerWire()
proposed=plate;rows=[]
for angle in range(20,380,40):
 a=math.radians(angle);x,z=36.5*math.cos(a),36.5*math.sin(a)
 cone=cq.Solid.makeCone(1.7,2.95,1.25,cq.Vector(x,52.25,z),cq.Vector(0,1,0))
 proposed=proposed.cut(cone)
 edge=cq.Edge.makeCircle(2.95,cq.Vector(x,53.5,z),cq.Vector(0,1,0))
 rim=outer_boundary.distance(edge)
 annulus=b.ring(2.95,1.7,.02,53.48,z,x)
 supported=annulus.intersect(plate).Volume()/.02
 rows.append(dict(angle_deg=angle,center_xz_mm=[x,z],nominal_outer_edge_land_mm=rim,
  original_plate_support_footprint_mm2=supported,expected_full_annulus_mm2=math.pi*(2.95**2-1.7**2)))
proposed=proposed.clean();assert proposed.isValid() and len(proposed.Solids())==1
checks=[]
for row in rows:
 angle=row['angle_deg'];x,z=row['center_xz_mm']
 head=b.cyl(1.5,6.55,(x,45.5,z)).fuse(cq.Solid.makeCone(1.5,2.95,1.45,cq.Vector(x,52.05,z),cq.Vector(0,1,0)))
 initial=max(0,head.intersect(proposed).Volume())
 seated=max(0,head.translate((0,-.02,0)).intersect(proposed).Volume())/.02
 tool=b.cyl(1.5,45,(x,53.5,z))
 tool_overlap=max(0,tool.intersect(proposed).Volume())
 aligned=crank.rotate((0,0,0),(0,1,0),-angle)
 distance=head.distance(aligned)
 checks.append(dict(angle_deg=angle,nominal_screw_plate_intersection_mm3=initial,
  projected_seating_footprint_mm2=seated,straight3mm_driver_plate_overlap_mm3=tool_overlap,
  crank_distance_at_aligned_ear_mm=distance,passed=initial<1e-5 and seated>0 and tool_overlap<1e-5))
old=b.cyl(1.5,8,(36.5*math.cos(math.radians(140)),45.5,36.5*math.sin(math.radians(140)))).fuse(
 b.cyl(2.75,3,(36.5*math.cos(math.radians(140)),53.5,36.5*math.sin(math.radians(140)))))
stand=crank.rotate((0,0,0),(0,1,0),-138)
old_overlap=max(0,old.intersect(stand).Volume())
out=dict(status='proposal_numerically_reviewed_not_authored',inputs=inputs,
 old_stand_interference=dict(stator_angle_deg=140,crank_rotation_y_deg=-138,overlap_mm3=old_overlap),
 proposal=dict(through_diameter_mm=3.4,seat_top_y_mm=53.5,seat_top_diameter_mm=5.9,seat_bottom_y_mm=52.25,cut_depth_mm=1.25,included_angle_deg=90,
  plate_back_y_mm=50.5,base_thickness_mm=3,residual_web_mm=1.75,
  screw='Ordinary M3 x 8 DIN 7991 countersunk socket screw, specified head dimensions; modeled head diameter5.9mm and cone height1.45mm.',
  nominal_tip_y_mm=45.5,motor_stator_face_y_mm=50.4,nominal_penetration_mm=4.9,
  min_measured_outer_edge_land_mm=min(r['nominal_outer_edge_land_mm'] for r in rows),
  central_bore_radial_land_mm=36.5-2.95-30,
  valid_solid=proposed.isValid(),solid_count=len(proposed.Solids())),
 seat_land_measurements=rows,seat_checks=checks,
 tooling=dict(access='+Y with outer thigh removed; standard90degree countersink or straight end-mill interpolation.',print_orientation='Plate baseY50.5 on bed, countersinks face upward; cone walls45degrees to axis. No support needed inside the seats in this orientation.'),
 purchasing=dict(primary_source='https://www.fastenal.com/content/product_specifications/M.FHSCS.7991.FT.A4-70.02.pdf',DIN7991_M3_head_diameter_mm=[5.7,6.0],head_angle_deg=[90,92],hex_drive_AF_mm=2,stock_verified=False),
 limitations=['Proposed analysis solid only; native authoring, exported revised plate and full interference checks remain owner tasks.',
 'Seat model is nominal. Purchased head diameter, angle, rim, length and printed seat variation can change proud height and engagement.',
 '1.05mm nominal outer edge land is not a printed-strength or preload qualification. Countersunk heads apply a radial wedging load; use finger-tight fit assembly only until tested.',
 'No operating strength, fatigue or loaded collision claim. No plate/thigh envelope change is required for this nominal fit proposal.'])
(HERE/'review.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(old_overlap_mm3=old_overlap,valid=proposed.isValid(),edge_land_min_mm=out['proposal']['min_measured_outer_edge_land_mm'],seats_passed=all(r['passed'] for r in checks),crank_distance_min_mm=min(r['crank_distance_at_aligned_ear_mm'] for r in checks)),indent=2))
