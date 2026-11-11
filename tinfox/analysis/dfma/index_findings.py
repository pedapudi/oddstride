"""Index the reviewed CAD families and evidence without changing their geometry."""
from pathlib import Path
import json
out=Path(__file__).resolve().parent
inventory=json.loads((out/'inventory.json').read_text());rows=[]
def plan(key):
 k=key.removesuffix('_right')
 if k.startswith('thigh_'):return 'Length near bed plane; exposed cavity upward; support accessible exterior.','Opposed Y faces and demonstrated motor-pocket access.','Clamp footprint and pocket access unresolved.'
 if k.startswith('shin_') and 'sleeve' not in k:return 'Length in bed plane; split face upward; Y bearing axis vertical.','Split-face cavity plus opposed outer bearing-seat setups.','Clamp footprint unresolved; fit/holder reach unqualified.'
 if k.startswith(('sleeve_','shin_clamp_sleeve_','pod_sleeve_')):return 'Retain metal for intended compression path.','Cut/face tubing; turn if required; inspect length and square ends.','Metal stock and stack tolerances require selection.'
 if k.startswith('motor_carrier_'):return 'Current metal shape is unloaded fit reference when printed.','Orthogonal X/Y interfaces, side relief setups; preserve datums.','Printed load route and finite cutter/holder access unqualified.'
 if k.startswith('roll_cartridge_'):return 'Unloaded bearing fit mockup.','Bore/face operations with selected bearing retention and preload.','Bearing and fit specification unfinished.'
 if k in ['hip_hub','motor_mount_ring']:return 'Polymer fit reference; intended route is metal.','Axial face/plate and reverse rib/pad setups.','Local mounting and preload strength unqualified.'
 if k in ['input_crank']:return 'Shape prototype only for current metal route.','Opposed faces and fork access with standard tools.','Loads, finish and fasteners unqualified.'
 if k=='body_center_0':return 'Roof-down candidate; open underside and inspect local supports.','Outer/inner surfacing and lateral screw holes.','Thin-wall fixture and print process review pending.'
 if k in ['body_nose_surround','front_fascia']:return 'Flat mounting lands; accessible open underside; inspect curved supports.','Surfacing and multiple hole directions; direct nut insertion.','Selected sensor retention and CAM setup incomplete.'
 if k.startswith('chassis_beam_'):return 'Unloaded frame fit mockup.','Opposed Y web/interfaces and top Z drilled/tapped pads.','Frame load and machining qualification pending.'
 if k.startswith('chassis_crossmember_'):return 'Unloaded fit mockup; preserve flat seats.','Folded profile, top countersinks; front underside M4 bosses.','Purchased screw seat and frame strength pending.'
 if k=='chassis_lower_brace':return 'Unloaded metal-frame reference if printed.','Flat profile/drill/tap from Z; inspect 3mm thread engagement.','Repeated-service torque and frame strength unqualified.'
 if k=='electronics_shelf':return 'Broad face down; slots and holes vertical.','Flat profile/drill; do not mirror metal frame load assumptions.','Computer standoffs and connectors unselected.'
 if k=='battery_cassette':return 'Open top up candidate; prove guide/gusset support removal.','Document standard-cutter access to internal guide windows.','Cutter access and selected battery hardware incomplete.'
 if k.startswith('battery_side_panel_'):return 'Flat panel face down.','Profile from sheet; drill normal to panel.','Cassette interface and process tolerances provisional.'
 if k.startswith(('battery_latch_','battery_access_latch_')):return 'Envelope only until retention geometry is defined.','Functional latch definition required before setup selection.','Retention unmodeled.'
 if k=='belly_center_0':return 'Open protective shell; orient for support removal.','Supported thin-wall surfacing/profile.','Attachment and sealing unfinished.'
 if k=='battery_skid':return 'Intended metal protective plate.','Flat profile and finished attachment holes.','Retaining interface unfinished.'
 if k=='foot':return 'Flexible material and retention design required.','Manufacturing route depends on selected boot or mold.','Envelope, not release geometry.'
 if k in ['lidar_lid','power_button']:return 'Selected equipment interface required.','Purchased device or custom part must be specified.','Reference/device envelope.'
 return 'Part-specific process selection required.','Document cutter direction, support and inspection.','Unverified.'
for item in inventory['custom_material_families']:
 a,b,c=plan(item['key']);rows.append({**item,'fdm_plan':a,'cnc_plan':b,'status':c})
(out/'part-process-register.json').write_text(json.dumps({'model_sha256':inventory['model_sha256'],'part_families':rows,'scope':'Proposed setups and part-specific review status; no CAM or sliced-print qualification.'},indent=2))
findings=[
 ('Structural shell clamp footprint','blocker','verified defect','Both', ['clamp-bearing-faces.json','washer-land-screen.json'], 'Revise head/nut bearing lands and compression stack; test slip and preload.'),
 ('Thigh stator-pocket cutter access','blocker','suspected access constraint','CNC', ['thigh-lobe-access.json'],'Demonstrate all pocket faces with standard cutter/holder or revise exposed structural split.'),
 ('Cassette guide and gusset access','blocker','unverified setup','Both', ['inventory.json','input-source/build.py'],'Prove support removal and straight-tool setups; revise trapped features if needed.'),
 ('Printed leg and frame strength','blocker','qualification missing','FDM', ['inventory.json'],'Select actual printed/hybrid route, complete directional coupons and assembled load/creep tests.'),
 ('Boot, lower cover and skid retention','blocker','design definition missing','Both', ['inventory.json'],'Complete serviceable retention geometry and hardware.'),
 ('Battery and equipment interfaces','major','components unselected','Both', ['inventory.json'],'Select commercial packs, adapters, contacts, computer/sensors and retention before final packaging.'),
 ('Bearing, shaft and bushing fit intervals','major','qualification missing','Both', ['inventory.json'],'Use supplier dimensions, independent fit/process parameters and manufactured coupons.'),
 ('Current print preparations','major','release evidence missing','FDM', ['inventory.json'],'Regenerate plate/profile/layer review for released geometry; older-hash support files do not apply automatically.'),
 ('Integrated rail and enclosure machining effort','major','geometry cost indicator','CNC', ['inventory.json'],'Quote multi-setup fixtures and evaluate flat/formed routes for cosmetic or simple parts.'),
 ('Short tubes and trimmed shoulder screws','major','additional manufacturing operations','Both', ['input-source/slim_limb.py'],'Create cut/face/deburr gauges and assemble pod stacks on bench as retained modules.'),
 ('M3 tie screw displayed seating','minor','nominal model clearance','Both', ['input-source/cohesive_chassis.py'],'Model selected head profile and seated position; observed normal gap0.07071mm.'),
 ('Extraction holes tangent to bearing-seat boundary','minor','geometric robustness concern','Both', ['input-source/cohesive_limb.py'],'Resolve cutter/press-tool contact on actual bearing race while preserving full support; avoid zero-width tangencies.'),
]
(out/'findings.json').write_text(json.dumps({'model_sha256':inventory['model_sha256'],'findings':[{'finding':a,'severity':b,'evidence_state':c,'route':d,'evidence':e,'required_action':f} for a,b,c,d,e,f in findings],'scope':'Review of the frozen input model; corrective geometry requires a separate disposition.'},indent=2))
print('Indexed',len(rows),'part families and',len(findings),'findings')
