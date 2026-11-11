"""Publish self-contained assembly instructions and dimensional source notes."""
import json,hashlib,html,zipfile
from pathlib import Path
import engineering as eng
from kinematics import ROOT
out=ROOT/'output/service-design';raw=(out/'model.json').read_bytes();data=json.loads(raw);stamp=hashlib.sha256(raw).hexdigest();audit=json.loads((out/'audit.json').read_text());assert audit['model_sha256']==stamp
eng.DATA=data;eng.PARTS=data['parts'];mass=eng.mass_budget();torques=eng.torques(mass['base_kg'])
report={'model_sha256':stamp,'mass':mass,'torque_cases':torques,'scope':'Prescribed foot-force and moving-link gravity screen using revised CAD mass. Same contact and 90 percent knee efficiency assumptions as the base design. Does not predict actuator temperature, gait dynamics or impact loads. Connector masses remain within the existing wiring allowance.'}
(out/'torques.json').write_text(json.dumps(report,indent=2))
old=json.loads((ROOT/'output/model.json').read_text());delta=sum(p['mass_kg'] for p in data['parts'])-sum(p['mass_kg'] for p in old['parts'])
rows=''.join(f'<tr><td>{r["case"].replace("_"," ")}</td><td>{r["payload_kg"]}</td><td>'+', '.join(f'{v:.2f}' for v in r['motor_Nm'])+'</td></tr>' for r in torques)
body=f'''<h1>Tinfox chassis-mounted head and service revision</h1>
<p>This CAD revision changes the shin split to two structural side halves. Each half contains a complete 28 mm bearing bore and an integral pushrod ear. The thigh cheeks provide backup axial stops. Motor connector envelopes and local housing openings are included in the robot view.</p>
<p><a href="../../review/service.html">Open interactive CAD</a> · <a href="../../review/service.html#extraction">Open bearing extraction view</a> · <a href="extraction.svg">Labeled bearing section</a> · <a href="updated-robot.step">Updated whole robot STEP</a> · <a href="updated-leg.step">Updated front-left leg STEP</a></p>
<h2>Chassis-mounted head; cosmetic rear cap removed</h2>
<p>The narrow lower strips beneath the head and tail have been removed. The front bridge attaches directly to the chassis crossmember through a 48 mm-wide mounting lap and two vertical M3 screws. Deep rounded shoulder sockets follow a conservative hip-roll envelope. Leg loads still pass through the independent motor cartridges and metal chassis.</p>
<p>The curved central bridge rises locally to about 68 mm above the hip-roll axis, compared with the earlier 55.5 mm shoulder crown. This extra depth preserves material above the sockets. The front retains a reinforced lower camera surround and removable curved fascia. The rear cap carries no equipment or chassis load and has been removed, together with its two screws and two nuts. The rear chassis crossmember remains to connect the motor rails. The head bridge is not a qualified lifting handle.</p>
<p>The provisional lidar moves 30 mm rearward onto the central cover to clear the front bridge. The two head nuts now sit below the front chassis crossmember; the earlier placement overlapped the metal. Existing screw locations remain unchanged.</p>
<p>For end-module service, remove the upper body cover, disconnect sensor wiring, undo the two cap screws and lift the module. The front fascia remains independently removable for camera service. Battery removal remains independent. Print the supplied oriented head bridge with removable supports beneath curved surfaces and local returns; it is not a support-free part. Inspect the sliced screw holes and narrowest bridge sections before printing.</p>
<p><a href="../../review/service.html#caps">Inspect the head bridge</a> · <a href="body-cap-audit.json">Fixed interfaces and removal-path checks</a></p>
<h2>Knee linkage display correction</h2>
<p>The isolated thigh view previously discarded the crank and rod transforms, incorrectly drawing the rod eye at the motor center. That view now preserves the assembled transforms. The rod attaches to a pin 22 mm from the motor axis, and its eyes are 170 mm apart. The dedicated linkage view exposes both connections. The geometry audit checks both eye-to-pin positions on all four legs in all 35 sampled poses.</p>
<p><a href="../../review/service.html#linkage">Inspect the knee linkage</a></p>
<h2>Native Fusion conversion</h2>
<p>A native-feature conversion is in progress. This revision remains the reference geometry until the Fusion parts pass shape, interface, assembly, motion and editability audits. STEP files below preserve solids but do not supply a native editable feature history.</p>
<h2>Removing a bearing</h2>
<ol><li>Support the leg. Disconnect the pushrod and remove the knee axle retention. Separate the shin from the thigh cheeks. The cheeks normally limit outward bearing movement, with 0.3 mm nominal axial clearance.</li>
<li>Remove the two M4 × 25 cross bolts and open the shin sideways. Bearings remain in their complete circular seats. The 18 mm compression sleeves and standard nuts are removable hardware.</li>
<li>Support the removed half close to its bearing housing with an opening beneath the bearing. Insert two blunt 2 mm service pins through the 2.6 mm holes behind the bearing outer ring.</li>
<li>Apply even force with a small press or suitable parallel tool so the bearing exits outward. Avoid loading the inner ring or seals. The pins are temporary tools, not installed leg components.</li></ol>
<p>The opposed inward shoulders locate the bearing outer rings. The thigh faces are backup stops and are not intended to rub continuously. The inner-race spacer stack must let normal axial loads pass through the bearings.</p>
<p>The access holes pass through the rear shoulder. They do not split the cylindrical seat. Their contact positions must be checked against the selected bearing's outer-ring face before pressing. The model uses nominal 12 × 28 × 8 mm bearing envelopes.</p>
<img src="extraction.svg" alt="Section through the bearing shoulder and two rear extraction holes" style="width:100%;max-width:1000px">
<h2>How the halves locate and clamp</h2>
<p>Broad mating faces and two alignment tongues locate the side halves. Two M4 cross bolts run parallel to the knee axle. Metal compression sleeves carry bolt preload. The shin retains the curved outer profile and internal cavity. Both halves are required for operation.</p>
<p>The complete bore improves repeatability relative to two semicircular seats, but two printed seats can still be misaligned. The nominal 28 mm CAD bore is not a specified interference fit. Print bearing-seat coupons in the same orientation and material before choosing hole compensation. Measure the assembled axle alignment and check running resistance before and after tightening.</p>
<h2>Principles carried into the thigh</h2>
<p>The thigh keeps its integrated motor cradle and removable outer structural half. The motor plate is accessible after opening the shell. Broad load paths, metal compression sleeves and open service access also apply to the shin. The revision adds knee outer-race backup stops to the existing thigh cheeks, avoiding another installed bearing cover.</p>
<p>The thigh does not need the same bearing-extraction holes at the knee: its knee interface holds the axle, while the rolling bearings live in the shin. The separate hip-roll bearing needs its own retention and extraction design.</p>
<h2>Connector geometry and assumptions</h2>
<p>The cached RobStride STEP contains two opposed radial ports near the rear cover. Both are represented on each of the twelve motors, for 24 reserved port positions. The housing envelope uses a 15.5 × 5.2 mm mouth; the cable plug uses the AMASS 12.3 × 4.2 × 11.8 mm outline. These are packaging solids, not contact-level connector CAD.</p>
<p>The provisional insertion overlap is 5 mm. Heat-shrink space, a 7 mm cable-bundle envelope and a straight 22 mm cable segment are included. The model reserves a 20 × 14 mm withdrawal corridor. These dimensions do not establish a cable bend radius or qualify flexing across hip roll and pitch. Harness anchor positions, slack loops, abrasion protection and fatigue life remain open.</p>
<p>The knee stator plate rotates its nine-hole pattern by 20 degrees while retaining the three structural tie positions. This gives the knee ports a different clocking from the hip and roll ports to clear the proximal carrier in the named poses. Socket position is measured approximately from the cached vendor STEP; final clocking and insertion depth require a fit check with the supplied motor and plug.</p>
<p>Housing windows and an underside-panel opening accommodate the modeled connectors. The cutouts remain unsealed. They do not establish an environmental protection rating. Local strength around the windows requires review.</p>
<h2>Measured checks and limits</h2>
<p>All 24 plug positions pass the sampled 25 mm withdrawal path in neutral with exterior body covers removed. Seven named poses clear the revised interfaces. The deep fold retains front-thigh contact with the underside panel. Additional combined-angle samples also contain collisions; the model does not establish an unrestricted joint range.</p>
<p>Exact-solid checks cover bearing withdrawal, shell separation, extraction-pin access, clamp hardware and nominal thigh-stop gaps. The browser highlights reported interference in the selected pose. Collision samples cover plugs, initial cable segments and revised structural parts; they do not model a deforming harness.</p>
<p>Estimated base mass is {mass['base_kg']:.3f} kg. The modeled change is {delta*1000:+.1f} g relative to the previous assembly. This remains a CAD estimate with battery, electronics and wiring allowances. It exceeds the 10 kg target.</p>
<p><a href="audit.json">Geometry checks</a> · <a href="torques.json">Recomputed torque screen</a> · <a href="parts.json">Export inventory</a></p>
<table><thead><tr><th>Load case</th><th>Payload kg</th><th>Roll, hip, knee motor torque N·m</th></tr></thead><tbody>{rows}</tbody></table>
<p>The torque screen uses prescribed foot forces and moving-link gravity. It does not certify stairs, running, jumping, thermal endurance or self-righting. Printed strength, creep, bearing fits, actual fastener lengths and cable life require physical testing.</p>
<h2>Printing and machining</h2>
<p>Orient the side halves with the open cavity upward and the long limb axis in the bed plane. The bearing axis then prints vertically. Rounded exterior surfaces still need local support review in the slicer. Check first-layer distortion, bearing bores and alignment tongues. Solid infill does not establish strength or eliminate creep.</p>
<p>For CNC, machine complete bearing seats from common datums and inspect the assembled coaxiality. The two rear access holes are straight drilling operations. The integral fork and cross-bolt pockets still require tool-reach and setup review. STEP files preserve solids but not a native Fusion feature timeline.</p>
<h2>Sources</h2>
<ul><li><a href="https://www.robstride.com/assets/product_manual_robStride02-e7f9f7c4.pdf">RobStride RS02 manual</a>: connector pair and motor interface.</li>
<li><a href="https://github.com/RobStride/Product_Information">RobStride product repository</a>: manufacturer CAD reference. This revision uses the previously cached RS02 STEP.</li>
<li><a href="https://www.china-amass.com/public/upload/20240723/c1ae9604bbe795ebfd366c9063019e3e.pdf">AMASS connector catalog, page 11</a>: XT30(2+2)-F plug outline.</li>
<li><a href="https://www.tme.eu/Document/127227924e5d7adc643d586e8218a55a/XT30PB-M.pdf">AMASS XT30 2+2 PB-M specification</a>: board connector outline.</li></ul>
'''
style='body{max-width:1000px;margin:48px auto;padding:0 24px;font:16px/1.6 system-ui;color:#26342d;background:#f4f5ed}h1{font-size:36px}h2{margin-top:36px}a{color:#236654}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:8px;text-align:left;border-bottom:1px solid #ccd1c5}'
extras=json.loads((out/'print-extras.json').read_text())
extra_html='<h2>Printed fit parts</h2><p>The keyed two-piece motor-carrier mockups include connector windows. These files are left-side fit mockups; right-side carriers require mirroring. They remain unloaded prototypes.</p><ul>'+''.join('<li><a href="'+q['print_stl']+'">'+q['id'].replace('_',' ')+' · STL</a></li>' for q in extras['parts'])+'</ul>'
body=body.replace('<h2>Sources</h2>',extra_html+'<h2>Sources</h2>')
(out/'README.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Tinfox chassis-mounted head and service revision</title><style>'+style+'</style>'+body+'</html>')
print('Published service notes, torque screen and mass',mass['base_kg'],'delta',delta,flush=True)
