"""Write the qualitative visual review alongside measured CAD results."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
proposals={
 'compact':{
  'label':'PROPOSAL A','title':'Compact package','image':'compact/design/12-studio-view.png',
  'description':'A narrower chassis and inward hip placement reduce the shoulder span. Controlled roof bevels, fine service-panel seams and recessed joint details give the body and limbs a common visual language.',
  'changes':['Hip roll axes move inward by 5 mm per side; the frame and body are repackaged around them.','Broad center panels blend into smoother end transitions. Rounded shoulder openings and fine panel seams frame the moving joints.','The nose face sits inside a continuous rounded wrap, with recessed optics. Metal caps have dark rim details and diagonal engraving.','A clean circular knee transition replaces the cosmetic inserts. The single pushrod and structural thigh halves remain accessible.'],
  'links':[{'label':'Open interactive CAD','href':'http://127.0.0.1:8767/review/'},{'label':'Individual parts','href':'http://127.0.0.1:8767/review/parts.html'},{'label':'STEP assembly ↓','href':'compact/model/output/tinfox-assembly.step'},{'label':'Full-size render ↗','href':'compact/design/12-studio-view.png'}],
  'iterations':[
   {'image':'compact/design/iterations/01-studio.png','title':'First geometry pass · nominal stance','correction':'Introduced the narrower package, faceted body and initial service details.','remaining':'Review found tilted flat soles, square shoulder openings and an underdeveloped sensor face.'},
   {'image':'compact/design/iterations/02-studio.png','title':'Rounded joints and contact soles','correction':'Replaced the flat foot with a rounded sole, shaped the shoulder reliefs and added limb detailing.','remaining':'The panel seams were too wide, the nose face stood proud and the knee insert ended abruptly.'},
   {'image':'compact/design/iterations/03-studio.png','title':'Integrated nose · studio stance','correction':'Recessed the nose panel within a continuous rim, rounded the knee insert and added cap rim detail.','remaining':'A stale neutral-cover clipping boundary still left a wide seam; the final pass corrected that boundary.'},
   {'image':'compact/design/12-studio-view.png','title':'Final CAD · studio stance','correction':'Fine panel seams, a seated nose face and coherent shoulder-to-knee detailing complete the exterior pass. Motion-driven motor-cover corrections are included in the final solid assembly.','remaining':'The tool-battery cassette remains more visible than in the concept. Flexible covers and loaded performance remain unqualified.'}
  ]},
 'sculpted':{
  'label':'PROPOSAL B','title':'Panelled body','image':'sculpted/design/12-studio-view.png',
  'description':'A broader recessed sensor face, local shoulder crowns and wraparound rotating cowlings follow the studio more closely. This proposal retains the wider hip spacing and gives the feet a larger rounded support surface.',
  'changes':['Local shoulder crowns frame real roll-carried cowlings around the proximal actuator assemblies. The covers retain separate rotating and fixed surfaces.','A wider front service face sits within a lofted nose surround, with a recessed camera bezel and accessible fasteners.','Side panels, a shaped battery access panel, surface markings and a forward lidar mount reproduce the reference’s panel hierarchy.','Simplified knee surrounds and continuously tapered shins join the larger boots. The thigh and effective knee-to-contact lengths remain approximately 170 mm each.'],
  'links':[{'label':'Open interactive CAD','href':'http://127.0.0.1:8768/review/'},{'label':'Individual parts','href':'http://127.0.0.1:8768/review/parts.html'},{'label':'STEP assembly ↓','href':'sculpted/model/output/tinfox-assembly.step'},{'label':'Full-size render ↗','href':'sculpted/design/12-studio-view.png'}],
  'iterations':[
   {'image':'sculpted/design/iterations/01-studio.png','title':'First panel construction · nominal stance','correction':'Built the planar/chamfered torso, service fascia, fasteners and shin channels.','remaining':'Review exposed an inverted battery panel on the roof, flat tilted soles and a proud nose plate.'},
   {'image':'sculpted/design/iterations/02-studio.png','title':'Battery panel and rounded soles','correction':'Corrected the battery-panel placement, introduced rounded contact soles and added the knee-edge insert.','remaining':'The nose still needed integration; shoulder framing and foot proportions remained too close to the old CAD.'},
   {'image':'sculpted/design/iterations/03-studio.png','title':'Recessed fascia and curved detail','correction':'Set the fascia into a rounded surround, corrected the cap engraving and radiused the shin-channel ends.','remaining':'The following pass broadened the fascia, raised the local shoulder crowns and redesigned the rotating cowling.'},
   {'image':'sculpted/design/12-studio-view.png','title':'Final CAD · studio stance','correction':'A wider inset face, raised shoulder crowns, real wraparound cowlings and larger rounded boots establish the final design. Rail and cowling clearances are checked in the final geometry.','remaining':'The broader nose adds length. Flexible covers, exact sensors and loaded performance remain development tasks.'}
  ]},
 'baseline':{
  'label':'PREVIOUS CAD','title':'Previous assembly','image':'baseline-studio-view.png',
  'description':'The preceding solid assembly, rendered from the same camera and at the same studio stance as both proposals. This isolates geometry changes from pose and framing changes.',
  'changes':['Continuous rounded torso with largely undecorated side surfaces.','Exposed cylindrical shoulder stacks and a narrow front sensor face.','Plain shin surfaces and small rounded feet.','The mechanical core provides the baseline for both proposals.'],
  'links':[{'label':'Open previous CAD','href':'http://127.0.0.1:8765/review/'},{'label':'Previous STEP ↓','href':'../model/output/tinfox-assembly.step'},{'label':'Full-size render ↗','href':'baseline-studio-view.png'}],
  'iterations':[]}}
for key,previous in [('compact','05'),('sculpted','06')]:
 p=proposals[key]
 p['iterations'][-1]['image']=f'{key}/design/iterations/{previous}-studio.png'
 p['iterations'][-1]['title']='Exterior refinement · before shin correction'
 p['iterations'][-1]['remaining']='The shin still bowed opposite to the studio reference. The next pass corrects that direction and the ankle transition.'
 p['iterations'].append({'image':f'{key}/design/iterations/07-studio.png','title':'Forward sweep · previous limb',
  'correction':'The structural shin now sweeps forward from the knee, narrows through the middle and returns toward the ankle. Its cavity, fastening bosses and surface channel follow the curve; knee and foot centers stay fixed.',
  'remaining':'The pronounced sweep and lower return made the shin visually complex and required local folding relief. The following pass simplifies the whole limb.'})
 p['iterations'].append({'image':p['image'],'title':'Continuous taper · current limb',
  'correction':'A smoother thigh transition, compact knee surround and restrained shin profile replace the deep waist and ankle return. Structural halves and their internal features are revised together.',
  'remaining':'The design is compared through sampled clearances, moving mass and section properties. Printed strength and dynamic locomotion still require physical validation.'})
 p['changes'].append('The whole limb uses a continuous taper and a shallow shin sweep, preserving motor mounts, joint centers and the single pushrod.')
for key in ['compact','sculpted']:
 proposals[key]['links'].append({'label':'Whole-limb profile comparison ↗','href':f'{key}/design/14-limb-profile.svg'})
for key,name in [('compact','limb-profile-comparison.json'),('sculpted','limb-revision-comparison.json')]:
 proposals[key]['links'].append({'label':'Movement and section comparison ↗','href':f'{key}/model/output/{name}'})
for key,previous in [('compact','09'),('sculpted','08')]:
 p=proposals[key]
 p['previous_image']=f'{key}/design/iterations/{previous}-studio.png'
 p['detail_image']=f'{key}/design/15-body-detail.png'
 p['iterations'][-1]['image']=p['previous_image']
 p['iterations'][-1]['title']='Continuous taper · limb refinement'
 p['iterations'].append({'image':p['image'],'title':'Integrated nose · current body',
  'correction':'The front surround, sensor face and shoulder crown are shaped together. Rounded edges and smoother body transitions replace the sharp station breaks and projecting nose rim.',
  'remaining':'The approved limb geometry is retained. Final camera modules, seals and manufacturing tolerances still require detail design.'})
 p['changes'].append('A wider recessed sensor face and rounded nose wrap soften the front while preserving service access and articulated shoulders.')
 p['links'].append({'label':'Front detail ↗','href':p['detail_image']})
 p['links'].append({'label':'Body revision measurements ↗','href':f'{key}/model/output/body-revision-comparison.json'})
p=proposals['sculpted']
p['previous_image']='sculpted/design/iterations/refinement-baseline/12-studio-view.png'
p['description']='A gently convex fascia and curved sensor recess continue the studio direction. Separate roof and side panels, rounder thighs and a shallow shin arc give the solid assembly a more consistent shape and a practical print breakdown.'
p['iterations'][-1]['image']=p['previous_image']
p['iterations'][-1]['title']='Rounded body · previous face'
p['iterations'].append({'image':p['image'],'title':'Convex face · print preparation','correction':'The fascia and sensor bezel now bow together. The center roof separates from its side panels. Thigh edges are rounder and the shin keeps one shallow arc.','remaining':'Unsliced plate files still need support and filament setup. Loaded performance, foot retention and final electronics interfaces remain unqualified.'})
p['changes']=['The face has a shallow compound crown that flattens toward its perimeter; the sensor recess follows the same curve.','The center roof and two side panels separate along a fine service seam, allowing broad faces to lie on the print bed.','A fuller thigh web, rounder edges and a single shallow shin arc retain the existing joint centers and motor transmission.','Individual STL and STEP parts include quantities, manufacturing routes, support notes and unsliced H2D plate layouts.']
p['links'].insert(1,{'label':'Print plates and fabrication kit','href':'http://127.0.0.1:8768/review/manufacturing.html'})
p['links'].append({'label':'Measured face curvature ↗','href':'sculpted/design/17-face-curvature.svg'})
p['iterations'][-1]['image']='sculpted/design/iterations/vertical-face-baseline/12-studio-view.png'
p['previous_image']=p['iterations'][-1]['image']
p['description']='A fuller compound-curved face follows the studio proportions. The roof lifts clear of the locating side panels, and the removable electronics tray shares four side-access screws with an underside cassette containing integral pack guides.'
p['iterations'].append({'image':p['image'],'title':'Two-axis convex face and accessible motor cradle','correction':'An independent 10 mm vertical crown adds top-to-bottom curvature while retaining the 8 mm horizontal bow. Revised roof bosses clear the panels during lifting; the battery module withdraws through a wider belly opening.','remaining':'The shared tray/cassette screws require supporting the battery module during service. Wiring, final purchased components and retention details remain unqualified.'})
p['links'].insert(1,{'label':'Hardware research and limb assembly','href':'http://127.0.0.1:8768/review/hardware.html'})
p['changes']=['The face and bezel have independent 8 mm horizontal and 10 mm vertical crowns.','Four upper cover screws replace eight; integral tabs locate the side panels.','Battery guides become part of the cassette. Four shared screws connect the cassette and electronics tray to the chassis.','A removable motor service ring opens the captive stator-plate recess. Bearing-seat lead-ins and a dimensional fit coupon support print preparation.']
p['links'].insert(1,{'label':'Interactive assembly access','href':'http://127.0.0.1:8768/review/assembly.html'})
p=proposals['sculpted']
p['previous_image']='sculpted/design/iterations/integration-baseline/12-studio-view.png'
p['description']='A removable top-and-side clamshell opens the electronics bay around an independent metal motor frame. Ribbed end modules retain the curved studio exterior. Integrated knee heads and stepped input cranks reduce custom joint parts.'
p['changes']=['A 2.8 mm nominal-wall central clamshell replaces the separate roof and side panels. Four side screws release it for upward removal.','Two metal rails and two transverse ties connect the motor cartridges independently of the covers. Front and rear caps attach to this frame.','One metal knee head combines both bearing seats, the pushrod fork and the keyed shin attachment. The motor coupling is integral with the input crank.','Replaceable 6001 bearings, flanged bushes, shoulder pins and shin clamp hardware are explicitly modeled. Fixed shaft and motor tie retention still need detail design.']
p['iterations'].append({'image':p['image'],'title':'Integrated joints and service shell','correction':'Consolidated joint components and body shells, with measured removal paths and an isolated frame view.','remaining':'Frame strength, printed lip fatigue, fixed shaft retention, motor tie stacks and real wiring remain unqualified.'})
p['links'].append({'label':'Frame and assembly stages','href':'http://127.0.0.1:8768/review/assembly.html'})
p['description']='A curved face and removable body clamshell surround an independent metal frame. Rounded shoulder openings stay visible through hip roll. Two printed thigh halves and a continuous shin shell surround the metal actuator and knee interfaces.'
p['changes']=['The rigid shoulder openings remain visible at every roll angle; provisional gaiters are removed.','The outer thigh includes the motor service ring, giving two printed structural halves.','One printed shin U-shell replaces two separate cheeks; its metal knee head retains the pushrod fork and bearing seats.','Layer directions, approximately 1.31 kN peak rod force, and unqualified PETG strength are documented in the print review.']
p['links'].append({'label':'Print direction and knee strength','href':'http://127.0.0.1:8768/review/strength.html'})
p['iterations'].append({'image':p['image'],'title':'Continuous limb shells and roll openings','correction':'Integrated the thigh service ring and shin walls, retained a metal knee head, and removed disappearing shoulder skins.','remaining':'Open-shin torsion, printed clamp creep, bearing-lip strength and loaded locomotion remain unqualified.'})
# Current manufacturing routes share the exterior and joint centers.
p['iterations'][-1]['image']='sculpted/design/iterations/broad-root-baseline/12-studio-view.png'
p['description']='A curved removable body shell surrounds an independent motor frame. Each thigh and shin uses two structural halves with broad joint roots. Separate printed, hybrid and metal limb sets preserve the articulated studio silhouette.'
p['changes']=['Two open structural halves form each thigh and shin, exposing the interior for printing, machining and assembly.','A broad collar joins the outer thigh to the motor service ring. Three-millimetre shoulders retain the knee bearing outer races.','The first printed prototype includes printed custom joint blocks and captive M5 nuts. Standard bearings, pins, shafts and compression sleeves remain metal.','The hybrid and CNC variants include material-specific relief pockets. All three routes have individual STEP files, material inventories and torque estimates.']
p['links'].insert(1,{'label':'Printed, hybrid and CNC limbs','href':'http://127.0.0.1:8768/review/variants.html'})
p['iterations'].append({'image':p['image'],'title':'Two-piece limbs and broad joint roots','correction':'Split each shin into two structural halves, widened the fork and clamp roots, and integrated the motor face into the outer thigh.','remaining':'The printed set is for unloaded fit checks. Bearing tolerances, fixed shaft retention, motor clamp hardware and load qualification remain unresolved.'})
p['iterations'][-1]['image']='sculpted/design/iterations/integrated-rocker-baseline/12-studio-view.png'
p['description']='A curved removable body clamshell surrounds an independent motor frame. Two structural halves form each thigh and shin. Integral shin rockers and direct split bearing seats remove the separate knee head.'
p['changes']=['The two shin halves directly contain the bearing seats, axial retaining shoulders and pushrod rocker. Opening the fore/aft split releases the bearings radially.','Two M4 clamps, captive nuts and compression sleeves close each shin. A recessed M8 axle bolt and outboard nut retain the removable sleeve.','The printed perpendicular motor carrier has two keyed parts with a 5 mm hip flange. The hip shroud is integral with that flange.','US hardware research prioritizes Amazon for ordinary hardware and precision suppliers for fitted parts; Lowe’s is a local fallback.']
p['iterations'].append({'image':p['image'],'title':'Direct bearing seats and integrated rockers','correction':'Removed the separate knee head and shoulder cover. Added two-part printed carriers and accessible axle retention.','remaining':'Printed parts are unloaded prototypes. Fits, preload, exact screw engagement, roll retention, motor ties and fatigue require qualification.'})
p['iterations'][-1]['image']='sculpted/design/iterations/electronics-deck-baseline/12-studio-view.png'
p['changes'].append('A flat 4 mm PETG electronics deck lifts on four top-access screws. A separate flat lower brace stays in the frame, and the battery cassette has independent retention.')
p['links'].insert(1,{'label':'Flat electronics deck','href':'http://127.0.0.1:8768/review/parts.html#electronics_shelf'})
p['iterations'].append({'image':p['image'],'title':'Flat electronics deck and independent battery service','correction':'Replaced the thin tray and downward ears with a flat printed deck, top screws and a fixed lower frame brace.','remaining':'Actual computer standoffs, cooling, connectors and frame stiffness remain unqualified.'})
(ROOT/'review-notes.json').write_text(json.dumps(proposals,indent=2,ensure_ascii=False))
print('Wrote qualitative comparison notes.')
