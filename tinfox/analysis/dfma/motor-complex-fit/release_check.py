"""Release check for a detached, unpowered three-motor fit assembly only."""
from pathlib import Path
import argparse,hashlib,json,math,shutil,sys
import cadquery as cq
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]/'proposals/sculpted/model'
sys.path.insert(0,str(ROOT));import build as b
BASE=ROOT/'fusion_native/snapshots/paired-bearing-target/b968fea927022ba467e05eb52ab602a680e14fd7295c263eefcb95a58a90cdc6'
CORRECTED=ROOT/'output/print-handoff/Tinfox-Motor-Complex-20261029T045513Z/reference-step'
parser=argparse.ArgumentParser();parser.add_argument('--outer-step');parser.add_argument('--outer-sha');parser.add_argument('--crank-step');parser.add_argument('--crank-sha');args=parser.parse_args()
EXPECTED={'thigh_outer':args.outer_sha or '28e49d8e38c3d75233eeea3e8bdd8927e92fb8ebbf60c6e5c39618dc6a996c19',
          'input_crank':args.crank_sha or 'f207fda710a287a74df9a5a864500737c50de6e25fa377909b8d2995a418b60f'}
INPUT=HERE/'release-input';INPUT.mkdir(exist_ok=True)
shapes={};hashes={};checks=[]
def read(key):
 if key not in shapes:
  p=Path(args.outer_step) if key=='thigh_outer' and args.outer_step else Path(args.crank_step) if key=='input_crank' and args.crank_step else CORRECTED/(key+'.step') if key in EXPECTED else BASE/'step'/(key+'.step')
  if not p.exists():p=HERE/'input-step'/(key+'.step')
  stamp=hashlib.sha256(p.read_bytes()).hexdigest()
  if key in EXPECTED:assert stamp==EXPECTED[key],(key,stamp)
  shutil.copy2(p,INPUT/p.name);hashes[key]=stamp;shapes[key]=cq.importers.importStep(str(INPUT/p.name)).val()
 return shapes[key]
def volume(s):return max(0,sum(x.Volume() for x in s.Solids()))
def intersect(a,c):
 aa,bb=a.BoundingBox(),c.BoundingBox()
 if any(getattr(aa,k+'max')<getattr(bb,k+'min')+1e-7 or getattr(bb,k+'max')<getattr(aa,k+'min')+1e-7 for k in ('x','y','z')):return 0
 return volume(a.intersect(c))
def clear(label,a,c,service_only=False):
 v=intersect(a,c);checks.append(dict(check=label,overlap_mm3=v,passed=v<1e-4,required_for_staged_assembly=not service_only))
def contact(label,a,c,axis):
 v=intersect(a.translate(tuple(.02*v for v in axis)),c);checks.append(dict(check=label,footprint_mm2=v/.02,passed=v>1e-6))
hub=read('hip_hub');plate=read('motor_mount_ring');inner=read('thigh_inner');outer=read('thigh_outer');crank=read('input_crank')
hip_motor=b.motor_envelope();knee_motor=b.motor_envelope((0,54.4,0))
closure=read('hip_stator_closure_1').translate((-5,0,0))
cup=read('motor_carrier_1').translate((-5,0,0))
housing=read('roll_cartridge_1').translate((-5,0,0))
retainer=read('roll_outer_retainer_1').translate((-5,0,0))
body=[('hip hub',hub),('stator plate',plate),('inner thigh',inner),('outer thigh',outer),('hip motor',hip_motor),('knee motor',knee_motor),('hip closure',closure),('cup',cup),('roll housing',housing),('retainer',retainer)]
assembly=[(name,s) for name,s in body if name!='outer thigh']+[('input crank',crank)]

for angle in (90,210,330):
 a=math.radians(angle);x,z=43.5*math.cos(a),43.5*math.sin(a)
 sleeve=read(f'pod_sleeve_{angle}')
 bolt=b.cyl(1.5,60,(x,1,z)).fuse(b.cyl(2.75,3,(x,61,z)))
 nut=b.hex_nut(5.5,2.4,x,2.6,z,1.5)
 assembly += [(f'tie{angle} sleeve',sleeve),(f'tie{angle} screw',bolt),(f'tie{angle} nut',nut)]
 contact(f'tie{angle} head to metal sleeve',bolt,sleeve,(0,-1,0))
 contact(f'tie{angle} nut to hub underside',nut,hub,(0,1,0))
 for name,s in body+[('metal sleeve',sleeve)]:
  clear(f'tie{angle} M3x60 / {name}',bolt,s)
  clear(f'tie{angle} M3 nut / {name}',nut,s)
 for travel in (0,3,8,20,40,60):
  head=b.cyl(2.75,3,(x,61+travel,z));clear(f'tie{angle} axial head entry {travel}',head,outer)
 clear(f'tie{angle} straight3mm driver',b.cyl(1.5,70,(x,64,z)),outer)
 # Nut-wrench access is tested at the seated plane with the motor complex
 # supported on the bench. The ordinary nut can be clocked freely.
 wrench_results=[]
 for clock in (0,15,30,45,60):
  head=b.cyl(7.25,3.4,(0,1.3,0));handle=b.box(80,3.4,6,(44,3,0)).rotate((0,0,0),(0,1,0),-15)
  mouth=b.box(20,6,5.6,(-6,3,0));w=head.fuse(handle).cut(mouth)
  w=w.rotate((0,0,0),(0,1,0),-(angle+clock)).translate((x+math.cos(a),0,z+math.sin(a)))
  hits={name:intersect(w,s) for name,s in body};wrench_results.append(dict(jaw_clock_from_radial_deg=clock,maximum_overlap_mm3=max(hits.values()),hits={k:v for k,v in hits.items() if v>1e-4}))
 checks.append(dict(check=f'tie{angle} ordinary5_5mm holding wrench seated',
                    tool=dict(head_width_mm=14.5,thickness_mm=3.4,jaw_opening_mm=5.6,handle_mm=80),
                    configurations=wrench_results,passed=any(r['maximum_overlap_mm3']<1e-4 for r in wrench_results)))

for angle in range(0,360,60):
 a=math.radians(angle);x,z=12*math.cos(a),12*math.sin(a)
 hip=b.cyl(2,8,(x,-4.3,z)).fuse(b.cyl(3.5,4,(x,3.7,z)))
 knee=b.cyl(2,12,(x,49,z)).fuse(b.cyl(3.5,4,(x,61,z)))
 assembly += [(f'hip output{angle} screw',hip),(f'knee output{angle} screw',knee)]
 contact(f'hip output{angle} M4x8 seat',hip,hub,(0,-1,0))
 contact(f'knee output{angle} M4x12 seat',knee,crank,(0,-1,0))
 for name,s in [('hub',hub),('cup',cup),('closure',closure),('knee motor',knee_motor)]:clear(f'hip output{angle} screw / {name}',hip,s)
 for name,s in [('crank',crank),('inner thigh',inner),('outer thigh',outer)]:clear(f'knee output{angle} screw / {name}',knee,s)
 for travel in (0,1,5,10,25):clear(f'knee output{angle} head entry {travel}',b.cyl(3.5,4,(x,61+travel,z)),crank)
 clear(f'knee output{angle} 4mm driver / crank',b.cyl(2,65,(x,65,z)),crank)
 clear(f'knee output{angle} 4mm driver / closed outer thigh',b.cyl(2,65,(x,65,z)),outer,service_only=True)
 # The hip output screws must be installed before the knee motor obstructs
 # their direct tool path. That obstruction is an assembly-order condition.
 clear(f'hip output{angle} driver before knee motor / hub',b.cyl(2,80,(x,7.7,z)),hub)

for angle in range(20,380,40):
 a=math.radians(angle);x,z=36.5*math.cos(a),36.5*math.sin(a)
 screw=b.cyl(1.5,8,(x,45.5,z)).fuse(b.cyl(2.75,3,(x,53.5,z)))
 assembly.append((f'knee stator{angle} screw',screw))
 contact(f'knee stator{angle} M3x8 seat',screw,plate,(0,-1,0))
 for name,s in [('plate',plate),('inner thigh',inner),('outer thigh',outer)]:clear(f'knee stator{angle} screw / {name}',screw,s)
 clear(f'knee stator{angle} 3mm driver / closed outer thigh',b.cyl(1.5,70,(x,56.5,z)),outer,service_only=True)

for dy in (0,.1,.25,.5,1,2,3,5,10,20,30,40,60):
 for name,s in assembly:clear(f'outer shell staged insertion Y+{dy} / {name}',outer.translate((0,dy,0)),s)

hardware=[
 dict(item='Pod through ties',specification='M3x60 socket-head cap screws, ordinary5.5AF M3 nuts; no washers in the preserved metal stack',quantity=3,nut_quantity=3,seating_position='Head undersideY61; nut bearingfaceY5, nutY2.6..5',nut_engagement_mm=2.4,tip_projection_mm=1.6,remaining_physical_checks='Measure actual60mm screw,2.4mm nut and41/6mm metal tube lengths; keep full nut engagement. Do not substitute65mm.'),
 dict(item='Hip-pitch output to hub',specification='M4x8 socket-head cap screw',quantity=6,seating_position='UnderheadY3.7; motoroutputY0',thread_penetration_mm=4.3,remaining_physical_checks='Install before knee motor; confirm motor output step and actual screwhead.'),
 dict(item='Knee-pitch output to crank',specification='M4x12 socket-head cap screw',quantity=6,seating_position='UnderheadY61; motoroutputY54.4',thread_penetration_mm=5.4,remaining_physical_checks='Use corrected through-open crank; measure blind-hole depth before final tightening.'),
 dict(item='Knee stator to plate',specification='M3x8 socket-head cap screw',quantity=9,seating_position='UnderheadY53.5; motorstatorY50.4',thread_penetration_mm=4.9,remaining_physical_checks='Install before crank. Nominal0.1mm plate/motorface gap means actual seated engagement may approach5.0mm.'),
 dict(item='Hip stator to removable closure',specification='M3x8 countersunk socket screw; prefer specified DIN7991 head dimensions',quantity=9,seating_position='Nominal topY−0.9; reference envelope draws down0.20mm to seat',thread_penetration_reference_mm=5.1,remaining_physical_checks='Check selected head standard/rim and actual conical seating; keep penetration≤6mm. Ordinary screw references are not proof of final seated position.'),
 dict(item='Roll output coupling',specification='M4x25 countersunk socket screw',quantity=6,seating_position='Nominal topX−52.5; reference envelope draws down0.20mm',thread_penetration_reference_mm=4.2,remaining_physical_checks='Check selected DIN7991/ISO10642 head; expected penetration about4.0–4.5mm,≤6mm.'),
 dict(item='Roll motor stator/body stack',specification='M3x30 button-head socket screw',quantity=9,seating_position='UnderheadX−50.5; motorstatorX−77.5',thread_penetration_mm=3.0,remaining_physical_checks='Confirm actual motorstatorface. Do not substitute35mm; it would reach8mm.'),
 dict(item='Roll outer bearing retainer',specification='M3x25 button-head socket screw plus ordinary5.5AF M3 nut',quantity=3,nut_quantity=3,seating_position='UnderheadX−48.5; nutX−73..−70.6',nut_engagement_mm=2.4,tip_projection_mm=.5,remaining_physical_checks='Keep nut at front pocketfloor while starting screw; current rearplate hex openings do not axially retain it there.'),
 dict(item='Cup closure',specification='M4x16 button-head socket screw; ordinary7AF M4 nut;4.3IDx9ODx0.8mm washer',quantity=3,nut_quantity=3,washer_quantity=3,seating_position='Head undersideY−0.1; washerY−0.9..−0.1; nutY−15.1..−11.9',nut_engagement_mm=3.2,tip_projection_mm=1.0,remaining_physical_checks='Use documented7mm holding-wrench route; do not force larger tools.'),
 dict(item='Two structural thigh clamps',specification='M4x25 button-head screw, ordinary M4 nut, two4.3IDx12ODx1mm washers and18mm compression sleeve per screw',quantity=2,nut_quantity=2,washer_quantity=4,seating_position='Existing corrected clampfloorsY58 and76; washers57..58/76..77',remaining_physical_checks='Use metal sleeves for clamping; printed sleeve copies are fit-only. Preload/creep not qualified.'),
]
hardware += [dict(item='Roll bearings',specification='6810-2RS, 50 x 65 x 7 mm sealed ball bearing',quantity=2,remaining_physical_checks='Select actual bearing brand; confirm race faces, fit and measured width. No preload qualification.'),
 dict(item='Pod compression tubes',specification='Metal tube, 5 mm OD / 3.4 mm ID: three at 41 mm and three at 6 mm length',quantity=6,remaining_physical_checks='Square, deburr and measure both ends. Optional printed copies are fit-only.'),
 dict(item='Thigh clamp compression tubes',specification='Metal tube, 8 mm OD / 4.4 mm ID, 18 mm length',quantity=2,remaining_physical_checks='Square ends and measured length; do not tighten printed substitute tubes structurally.')]
report=dict(overall_passed=all(r['passed'] for r in checks if r.get('required_for_staged_assembly',True)),scope='Detached, unpowered three-RS02 proximal complex fit assembly. Not a release for powered or loaded operation, CNC production, or structural polymer substitution.',
 source_model_sha256=BASE.name,corrected_target_sha256=EXPECTED,input_step_sha256=hashes,
 manufacturer_reference=dict(path=str(ROOT/'references/rs02-manual.pdf'),sha256=hashlib.sha256((ROOT/'references/rs02-manual.pdf').read_bytes()).hexdigest(),drawing='9M3depth8 onPCD73±0.2;6M4depth7MIN onPCD24±0.2. Prototype penetration≤6mm;7MIN is not a maximum. Pilot3.5(+0/−0.3) plus0.5 frontstep; case41.5 versus modeled41.4mm.'),
 checks=checks,failed_checks=[r for r in checks if not r['passed'] and r.get('required_for_staged_assembly',True)],
 service_order_limitations=[r for r in checks if not r['passed'] and not r.get('required_for_staged_assembly',True)],hardware=hardware,
 assembly_sequence=['Fit bearings/spacers and the outer retainer in the main housing with the rear plate and motor absent; start three M3 x 25 screws and accessible M3 nuts before closing the rear.',
 'Position the inner backplate, fit the rear stator plate and roll motor, then install the nine M3 x 30 stator screws.',
 'Fit the cup/journal and tighten the six M4 x 25 output screws through the empty cup before installing the perpendicular hip motor.',
 'Install the hip motor and its removable closure. Install the hip output hub with six M4 x 8 screws before the knee motor blocks those tool paths.',
 'Fit the knee motor to its plate with nine M3 x 8 screws; install the input crank with six M4 x 12 screws before closing the outer thigh.',
 'Assemble the three M3 x 60 pod ties, six metal sleeves and three M3 nuts; slide the corrected outer thigh axially over the preassembled module.',
 'Tighten the three long ties through their open channels and close the two structural thigh clamps. Accessing the fifteen knee-motor screws later requires removing the outer shell.'],
 ordinary_nut_totals=dict(M3=6,M4=5),
 limits=['Verify physical motor-hole depth, face datums and purchased fastener/head tolerances before tightening.',
 'Some fasteners need a staged assembly order: hipoutput before knee motor; kneestator before crank; outer shell head-entry cuts are required.',
 'Tube stack is9.5..50.5 and55..61; bare tie head clamps the metal sleeve, not the outer polymer. Two existingM4 shell clamps retain the structural halves.',
 'No knee axle,6001bearings,pushrod or shoulder pins required for this proximal assembly.',
 'Metal sleeve/spacer substitution and structural strength remain separate from the printed fit test.'])
(HERE/'release-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=report['overall_passed'],checks=len(checks),failures=report['failed_checks']),indent=2))
