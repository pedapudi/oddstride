"""Record layer directions and nominal loads without claiming print qualification."""
import hashlib,json,math,html
import numpy as np
from kinematics import ROOT,P
out=ROOT/'output';raw=(out/'model.json').read_bytes();stamp=hashlib.sha256(raw).hexdigest()
plan=json.loads((out/'manufacturing-plan.json').read_text());eng=json.loads((out/'engineering.json').read_text());joint=json.loads((out/'integration-audit.json').read_text());audit=json.loads((out/'mounting-audit.json').read_text())
assert all(v['model_sha256']==stamp for v in [plan,eng,joint,audit])
rows=[]
for part in plan['parts']:
 if part['id'].removesuffix('_right') not in ['thigh_inner','thigh_outer','shin_inner','shin_outer']:continue
 rotation=np.array(part['transform'])[:3,:3]
 long=rotation@np.array([0,0,1]);shaft=rotation@np.array([0,1,0])
 angle=math.degrees(math.asin(min(1,abs(long[2]))))
 assert angle<.01,(part['id'],angle)
 rows.append({'part':part['id'],'long_axis_above_bed_deg':angle,'bearing_axis_from_vertical_deg':math.degrees(math.acos(min(1,abs(shaft[2])))),'print_bounds_mm':part['print_bounds_mm'],'orientation':part['orientation_note']})
lever=P['crank_radius']/1000*min(abs(math.cos(math.radians(k+P['crank_phase_deg']))) for k in range(-156,-47))
force=17/lever;continuous=6/lever
report={'model_sha256':stamp,'status':'Unqualified structural prototype','orientations':rows,'transmission_screen':{'minimum_moment_arm_mm':lever*1000,'peak_motor_torque_Nm':17,'rated_motor_torque_Nm':6,'rod_force_at_peak_N':force,'rod_force_at_rated_N':continuous,'outer_fork_ear_thickness_mm':7.8,'hypothetical_average_pin_bearing_pressure_MPa':force/(2*6*7.8),'scope':'Quasi-static linkage equilibrium over modeled knee range. Equal reactions assumed for the two fork ears. External impact can exceed this load. Pin bearing pressure is not a tensile stress or a failure prediction.'},'minimum_shin_section_modulus_y_mm3':audit['minimum_shin_section_modulus_y_mm3'],'material_reference':{'name':'Bambu PETG HF TDS V1.0','source':'https://store.bblcdn.com/3a230e260a3a47c2b0db0156e07eef91.pdf','tensile_XY_MPa':34,'tensile_Z_MPa':23,'HDT_at_1_8_MPa_C':62,'coupon_conditions':'100% infill, 255 C nozzle, 70 C bed, 200 mm/s; specimens annealed and dried at 75 C for 8 h. Manufacturer discourages annealing complex PETG HF parts because of deformation.','use':'Illustrates anisotropy. Not a material allowable for these parts, another PETG formulation or an unannealed print.'},'qualification_required':['Same-filament coupons printed with the actual profile, dry material and expected motor-adjacent temperature','Full leg static tests in forward/back bending, lateral bending, torsion and pushrod load; measure residual deformation and bearing alignment','Sustained-load creep and clamp-retention tests at service temperature','Repeated gait loads, controlled impacts and post-test inspection of hole edges, root fillets and layers'],'scope':'Orientation and analytical load screen. No orthotropic FEA, slicer toolpath inspection, destructive tests or lifetime qualification.'}
(out/'print-strength-audit.json').write_text(json.dumps(report,indent=2))
text=f'''TINFOX — PRINT ORIENTATION AND KNEE STRENGTH

STATUS
The printed knee and limb structure is not strength-qualified. A 100% infill
PETG print does not establish survival during loaded stairs, self-righting or
landing. The main CAD shows the hybrid: printed shells with integral forks, metal cranks and shoulder screws,
shaft and bearings. The separate printed variant replaces custom joint parts
with printed parts for unloaded fit and hand-articulation checks. It is not a
release for standing or dynamic operation.

LAYER DIRECTION
Both thigh halves and both shin halves lie lengthwise in the bed plane.
The thigh split lies in local X/Z, and its pitch axis prints vertically. The shin
split lies in local Y/Z, and its bearing axis prints horizontally. Both orientations
keep the long load path within layers. The shin bearing seats are open semicircles
at the split face; inspect their perimeters and fit after printing.

Print each structural half with its split face and open cavity upward.
The motor cradle needs accessible support beneath its offset web. Local supports
under curved exterior surfaces remain necessary. The actual oriented STL files
were checked: every structural limb length is parallel to the bed. They are not
sliced, and perimeter continuity and support removal still require layer preview.

Loads that open a fork, pry a washer ledge or pull a motor-retaining web apart can
act across layers in this orientation. No orientation makes the whole knee
isotropic. The motor tie preload must pass through metal compression hardware;
the printed service-ring webs must not be treated as proven axial ties.

CONCENTRATED KNEE LOAD
The 22 mm cranks have a minimum effective moment arm of {lever*1000:.2f} mm over
the modeled knee range. Rod force equals torque divided by that moment arm:
6 N m gives {continuous:.0f} N; 17 N m gives {force:.0f} N. External impacts can
exceed the motor-driven load. Bearings, bushings and the pin carry concentrated
forces even when the robot's total weight seems modest.

For the current 7.8 mm outer fork ear in PETG, a simplified equal-share
model gives {force/(2*6*7.8):.1f} MPa average pin bearing pressure at 17 N m.
This is a local contact-pressure screen, not tensile stress or a failure limit.
It excludes hole-edge concentration, ear bending, uneven sharing and fatigue.
The hybrid also uses printed shin forks. Both printed-shell routes remain unloaded prototypes until tested.

STRUCTURAL SHELL
The shin uses two structural halves with broad mating lands, continuous clamp
rails and full-width fastening ribs. Two M4 screws and captive compression sleeves
join the halves. The assembled section encloses a cavity;
its torsional stiffness depends on joint preload, fit and slip. Both halves are
required. The sampled minimum sagittal section modulus is {audit['minimum_shin_section_modulus_y_mm3']:.0f} mm3.
The uniform-bending screen gives {eng['structure']['gross_bending_stress_MPa']:.1f} MPa nominal stress;
a factor of two would require {eng['structure']['coupon_strength_needed_for_factor_2_MPa']:.1f} MPa before local effects. This does not
establish a PETG margin. The screen omits local bearing-seat stresses and the actual variation of moment
along the shin.
That single measure cannot qualify lateral loading, torsion, clamp seats or the
3 mm bearing-retaining shoulders. The separate motor and knee cosmetic caps are
integral with the outer thigh. No separate thin cap needs to be printed.


SOLID PETG
More walls and dense local material help distribute loads. Solid infill does not
remove interlayer weakness, creep or hole-edge stress concentration. The mass
estimate already uses solid CAD volume, without an infill weight discount.
Bambu's PETG HF data reports 34 MPa XY and 23 MPa Z tensile strength from 100%
infill specimens. Those specimens were annealed/dried; the values are not design
allowables for an arbitrary PETG print. Its reported HDT at 1.8 MPa is 62 C,
which is not a safe continuous service-temperature limit near a motor.
Source: https://store.bblcdn.com/3a230e260a3a47c2b0db0156e07eef91.pdf

PROTOTYPE AND TEST PLAN
Start with six to eight perimeters and dense local zones at clamp seats and
bearing supports. These are trial settings, not a qualified print recipe. Verify
wall count in narrow webs; do not assume an infill percentage creates continuous
fibers along the limb. Use the filament manufacturer's dry-material profile.

Test the actual material/profile at operating temperature, then test a complete
leg in bending, lateral loading, torsion and sustained pushrod loading. Record
permanent deflection, bearing alignment, cracking and fastener relaxation.
Choose proof and fatigue loads from measured duty and impact loads. A static
screen alone does not authorize running or jumping. Revisit metal reinforcement
if the tests show excessive strain or creep. Inspect the three fabrication variants in variants.html.
'''
(out/'print-strength-review.txt').write_text(text)
trs=''.join('<tr><td>'+html.escape(r['part'])+'</td><td>'+f"{r['long_axis_above_bed_deg']:.1f}°"+'</td><td>'+html.escape(r['orientation'])+'</td></tr>' for r in rows)
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tinfox · print strength</title><style>body{background:#eeeee7;color:#293b30;font:16px/1.65 system-ui;margin:0}main{max-width:1050px;margin:auto;padding:40px}h1{font-weight:500}a{color:inherit;margin-right:24px}pre{white-space:pre-wrap;font:inherit}table{border-collapse:collapse}td,th{padding:14px;border-bottom:1px solid #c4cebf;text-align:left}.notice{background:#dfe5d7;padding:20px;border-left:4px solid #ef803b}</style><main><nav><a href="./">CAD</a><a href="manufacturing.html">Print layouts</a><a href="hardware.html">Hardware</a><a href="../output/print-strength-audit.json">Measured directions and loads</a></nav><h1>Layer direction and the knee load path.</h1><p class="notice">The limb lengths lie in the print bed plane. Loaded locomotion remains unqualified; solid PETG alone does not establish knee strength.</p><table><tr><th>Printed part</th><th>Length above bed</th><th>Orientation</th></tr>'''+trs+'''</table><pre>'''+html.escape(text)+'''</pre></main></html>'''
(ROOT/'review/strength.html').write_text(page)
print('Structural limb orientations checked; strength limitations and qualification plan published.')
