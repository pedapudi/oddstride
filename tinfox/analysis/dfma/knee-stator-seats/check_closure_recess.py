"""Read-only analysis of a common-button-screw closure recess proposal."""
from pathlib import Path
import hashlib,json,math,sys
import cadquery as cq
H=Path(__file__).resolve().parent;R=H.parents[2]/'proposals/sculpted/model'
sys.path.insert(0,str(R));import build as b
N=R/'fusion_native';D=H/'closure-input';D.mkdir(exist_ok=True)
specs={'cup':('paired-native-motor_carrier_1.step','b4d3fa0141de0d3b877e1bfaaff0440a3edf00a92207b44899f0f57a88b3c721'),
 'closure':('paired-native-hip_stator_closure_1.step','4bbb56e2125b9e9a440a9a4149f3d2f8caed3f888ddaf21eae2655cc5f84f634')}
shapes={};inputs={}
for key,(name,expected) in specs.items():
 p=N/'exports'/name;raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==expected
 q=D/name;q.write_bytes(raw);shapes[key]=cq.importers.importStep(str(q)).val().translate((-5,0,0));inputs[key]=dict(path=str(p),sha256=expected)
cup,closure=shapes['cup'],shapes['closure'];newcup=cup;newclosure=closure;rows=[]
def polar(r,a):return r*math.cos(math.radians(a)),r*math.sin(math.radians(a))
def v(s):return max(0,sum(q.Volume() for q in s.Solids()))
for a in (90,215,325):
 x,z=polar(47,a)
 # Fill the old recess while extending only the three lug backs.
 newclosure=newclosure.fuse(b.cyl(6,2.2,(x,-5.1,z)))
 newclosure=newclosure.cut(b.cyl(2.4,10,(x,-6,z)))
 newclosure=newclosure.cut(b.cyl(4.95,1.1,(x,-5.1,z)))
 newclosure=newclosure.cut(b.cyl(4.1,30,(x,-2.2,z)))
 # Open front-facing cup pocket and replacement locating boss.
 newcup=newcup.cut(b.cyl(6.1,5,(x,-5.1,z)))
 newcup=newcup.fuse(b.ring(4.8,2.2,1.1,-5.2,z,x))
# Retain the valid unrefined Boolean result. Optional coplanar-face cleanup
# invalidates this independently cut native export; it is not a fit gate.
newclosure=newclosure.clean()
for a in (90,215,325):
 x,z=polar(47,a)
 old=b.cyl(2,16,(x,-16.1,z)).fuse(b.cyl(3.8,2.2,(x,-.1,z)))
 new=b.cyl(2,16,(x,-18.2,z)).fuse(b.cyl(3.8,2.2,(x,-2.2,z)))
 # Original contact at hip -10 degrees; tie210 moves to220 degrees.
 tie_x,tie_z=polar(43.5,210)
 tie=b.cyl(1.5,60,(tie_x,1,tie_z)).fuse(b.cyl(2.75,3,(tie_x,61,tie_z))).rotate((0,0,0),(0,1,0),-10)
 nut=b.hex_nut(7,3.2,0,-15.1,0,2).rotate((0,0,0),(0,1,0),-a).translate((x,0,z))
 overlap=v(new.intersect(newclosure));cupoverlap=v(new.intersect(newcup))
 land=v(new.translate((0,-.02,0)).intersect(newclosure))/.02
 driver=b.cyl(1.6,40,(x,0,z))
 # Probe the remaining annular floor between the rear pilot pocket and
 # front head recess, with the newly enlarged local fillet-clearance pilot.
 annulus=b.ring(3.8,2.4,.02,-2.22,z,x)
 floor=v(annulus.intersect(newclosure))/.02
 # A nut is intentionally allowed to touch its bearing floor at -11.9.
 nutintersect=v(nut.intersect(newcup))
 rows.append(dict(angle_deg=a,old_bolt_tie210_intersection_at_hip_minus10_mm3=v(old.intersect(tie)),new_bolt_tie210_gap_at_hip_minus10_mm=new.distance(tie),new_screw_closure_overlap_mm3=overlap,new_screw_cup_overlap_mm3=cupoverlap,projected_head_seating_area_mm2=land,full_floor_support_mm2=floor,nominal_nut_engagement_mm=3.2,tip_projection_mm=3.1,nut_cup_overlap_mm3=nutintersect,straight_driver_closure_overlap_mm3=v(driver.intersect(newclosure)),passed=overlap<1e-5 and cupoverlap<1e-5 and land>20 and nutintersect<1e-5))
out=dict(status='analysis_proposal_not_native_authored',passed=newcup.isValid() and newclosure.isValid() and len(newcup.Solids())==len(newclosure.Solids())==1 and all(r['passed'] for r in rows),inputs=inputs,
 actual_original_dimensions=dict(plate_y_mm=[-4,-.9],base_thickness_mm=3.1,rear_register_pocket_depth_mm=1.1,proposed_front_recess_depth_mm=1.3,web_if_only_front_recess_added_mm=.7),
 proposal=dict(front_counterbore_diameter_mm=8.2,front_floor_y_mm=-2.2,closure_pilot_diameter_mm=4.8,back_lug_y_mm=-5.1,old_pocket_filled=True,new_rear_register_pocket_y_mm=[-5.1,-4],rear_register_diameter_mm=9.9,cup_locating_boss_y_mm=[-5.1,-4.1],cup_locating_boss_diameter_mm=9.6,cup_lug_relief_diameter_mm=12.2,residual_web_mm=1.8,minimum_plan_lug_edge_land_mm=1.9,radial_head_clearance_mm=.3,maximum_head_top_y_mm=0,rotation_independent_axial_tie_gap_mm=1,common_screw='M4 x16 ISO7380-1 button head, no separate closure washer',screw_tip_y_mm=-18.2),
 proposed_solid_validity=dict(cup=newcup.isValid(),closure=newclosure.isValid(),cup_solids=len(newcup.Solids()),closure_solids=len(newclosure.Solids()),excluded_prior_optional_coplanar_cleanup_valid=False),checks=rows,
 machining=dict(closure_front='+Y: counterbore and through pilot using straight tools.',closure_back='-Y: open locating pockets. Local back extensions are in the external profile.',cup_front='+Y: open12.2mm lug recess; no roof or reverse-facing ledge.',assembly='Seat closure screws and hold ordinary7mm nuts through existing radial cup slots before installing the hip output hub.'),
 primary_screw_dimensions=dict(source='https://www.fastenal.com/content/product_specifications/M.BHSCS.73801.10.9.BO.04.pdf',head_diameter_mm=[7.24,7.6],height_mm=[1.95,2.2],fillet_diameter_max_mm=4.7,drive_AF_mm=2.5,inventory_verified=False),
 limitations=['Proposed analysis geometry only. Native features, handed copies and whole-robot motion must be checked after authoring.','Localized cup relief can intersect the existing cup-to-journal web near the215degree lug. Retained web and new lug support need structural review before powered use.','Thin printed floor, preload, polymer creep, impact and loaded tolerances remain unqualified.','The primary standard bounds head dimensions; purchased underhead fillet and printed hole clearance still require measurement.','The1mm rigid axial gap is nominal. Screw/tube length, floor position, printed shrinkage and loaded deflection are not included.'])
(H/'closure-recess-proposal.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
