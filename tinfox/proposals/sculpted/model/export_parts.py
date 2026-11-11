"""Index the exact individual STEP solids and package them for CAD review."""
import hashlib,json,zipfile
from pathlib import Path
from kinematics import ROOT
out=ROOT/'output';raw=(out/'model.json').read_bytes();model=json.loads(raw)
roles={
 'roll_cartridge':('Fixed roll-motor and bearing mount','Mounts','Bolts the roll stator to the chassis and houses the roll bearing.','Nine Ø3.4 mm stator holes on a 73 mm pitch circle; 66.2 mm nominal bearing bore.','Machined aluminum; bearing retention, screw engagement and fits need review.'),
 'motor_carrier':('Roll-output / hip-motor carrier','Mounts','Carries the hip-pitch stator on the roll actuator output.','Perpendicular motor axes; six Ø4.4 mm roll-output holes on a 24 mm pitch circle and nine Ø3.4 mm hip-stator holes on a 73 mm pitch circle.','Machined aluminum; check tool access, bearing journal tolerance and motor datums.'),
 'hip_hub':('Hip-output coupling','Mounts','Connects the hip output to the proximal knee-motor support ties.','Six Ø4.4 mm output holes on a 24 mm pitch circle; three tie positions at 43.5 mm radius.','Machined aluminum; select screws and confirm output pilot clearance.'),
 'motor_mount_ring':('Knee-motor stator plate','Mounts','Spreads knee-stator loads into the metal ties and the integrated thigh cradle.','Nine Ø3.4 mm stator holes on a 73 mm pitch circle; three tie positions at 43.5 mm radius.','3 mm aluminum plate; finish holes and verify motor-face contact.'),
 'knee_drive_adapter':('Knee-output spacer adapter','Mounts','Connects the knee actuator output to the input crank.','Six Ø4.4 mm output holes on a 24 mm pitch circle.','Machined aluminum; verify pilot, screw lengths and axial stack.'),
 'motor_service_ring':('Motor cradle service ring','Limbs','Opens the stator-plate recess for axial motor installation.','Three existing axial tie positions; 0.3 mm nominal axial split gap.','PETG prototype; final tie stack and load qualification remain open.'),
 'electronics_shelf':('Flat electronics deck','Body','Removable printed equipment deck with six rounded openings and broad crossbars.','Four vertical M3 x 8 screws attach it to the fixed frame brace. Cassette fasteners remain independent.','Print the constant 4 mm section flat with vertical holes and no designed supports. Component standoffs and cooling remain to be selected.'),
 'chassis_lower_brace':('Fixed lower frame brace','Body','Maintains the lower connection between chassis rails when the deck is removed.','Flat 3 mm aluminum H plate; four rail screws and four tapped deck mounts.','Flat cutting and drilling/tapping candidate; printed copy is an unloaded fit mockup.'),
 'thigh_inner':('Integrated motor cradle / inner thigh','Limbs','Combines the recessed knee-motor housing and inner structural thigh half.','170 mm hip-to-knee spacing; metal stator plate and compression sleeves distribute motor loads.','PETG prototype; joint fits and printed strength remain unqualified.'),
 'thigh_outer':('Outer structural thigh clamshell','Limbs','Closes the structural thigh and incorporates the motor service ring and knee bezel.','Broad open retaining collar and integral motor/knee faces; 170 mm hip-to-knee spacing.','PETG prototype; preserve the wall geometry and review supports in the slicer.'),
 'shin_shell':('Continuous structural shin shell','Limbs','Integrates the outer wall and side webs around a keyed metal knee head.','Axial head insertion; two M3 clamps and an inboard DIN 472 ring.','PETG prototype with open inboard print access; qualify bending, torsion, layer adhesion and clamp creep.'),
 'knee_retaining_ring':('Inner knee bearing retaining ring','Hardware','Retains the inboard 6001 outer race in the metal knee head.','DIN 472 / J28, 1.2 mm thickness, nominal installed envelope.','Purchased spring-steel ring; verify vendor groove tolerances and plier access.'),
 'shin_inner':('Rear structural shin','Limbs','Carries integral split bearing seats, retaining shoulders and rocker structure.','Fore/aft split releases bearings radially; two M4 clamps and captive sleeves close the shell.','PETG prototype; use both halves and qualify the printed load path.'),
 'shin_outer':('Front structural shin','Limbs','Completes the direct split bearing housing and integral pushrod fork.','Two M4 clamps join the front and rear shells; the M5 pivot nut loads from the open split.','PETG prototype; use both halves and qualify the printed load path.'),
 'knee_head':('Integrated knee head','Limbs','Combines both bearing seats, the pushrod fork and keyed shin attachment.','Two 6001 bearings; double-shear 6 mm pin; integral metal compression columns.','Machined metal load path; printed mockups are unloaded fit checks.'),
 'input_crank':('Integrated knee input crank','Transmission','Combines the motor-output adapter and crank with a double-shear fork.','22 mm crank radius; six output-interface holes, 6 mm shoulder seat and M5 pin thread.','Machined aluminum; modeled shoulder pins require selected material, thread locking and fatigue qualification.'),
 'output_crank':('Knee output rocker','Transmission','Transfers pushrod load to the shin at the rear of the knee.','22 mm crank radius; installed −78° phase; Ø6 mm rod-pin hole.','Machined aluminum; modeled shoulder pins require selected material, thread locking and fatigue qualification.'),
 'pushrod':('Knee pushrod','Transmission','Joins the equal-radius input and output cranks.','170 mm eye spacing; finished 8 mm bushing bores in 15 mm eyes.','Steel part; pinned joints and fatigue strength need qualification.'),
}
def describe(key,p):
 for prefix,v in roles.items():
  if key==prefix or key.startswith(prefix+'_'):return v
 title=key.removesuffix('_right').replace('_',' ').capitalize()
 category='Body' if p['group']=='body' else ('Limbs' if p['material']=='petg' else 'Hardware')
 return title,category,p['note'] or 'Separate component of the exported assembly.','See the solid geometry and mating assembly.',('Printed fit prototype.' if p['material']=='petg' else 'Nominal solid; manufacturing details require review.')
records=[]
for path in sorted((out/'step-parts').glob('*.step')):
 key=path.stem;uses=[p for p in model['parts'] if p['mesh']==key]
 assert uses, f'Orphan CAD file: {key}'
 p=uses[0];title,category,role,interfaces,manufacture=describe(key,p)
 variant=[]
 if any(p['leg'] for p in uses):
  legs=[p['leg'] for p in uses]
  variant=[{'FL':'front left','FR':'front right','RL':'rear left','RR':'rear right'}[leg] for leg in legs]
 records.append({'id':key,'title':title,'category':category,'role':role,'interfaces':interfaces,'manufacturing':manufacture,'variant':', '.join(variant) or 'body','quantity':len(uses),'instances':[p['name'] for p in uses],'material':p['material'],'color':p['color'],'bounds_mm':p['bounds_mm'],'mass_kg':p['mass_kg'],'step':f'step-parts/{key}.step','step_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'stl':f'stl/{key}.stl','print_stl':f'print-stl/{key}.stl' if (out/'print-stl'/f'{key}.stl').exists() else None})
order={c:i for i,c in enumerate(['Mounts','Limbs','Transmission','Body','Hardware'])}
records.sort(key=lambda p:(order[p['category']],p['title'],p['variant']))
catalog={'model_sha256':hashlib.sha256(raw).hexdigest(),'units':'mm','status':'Nominal engineering CAD; not a release for manufacture. STEP retains solids without a native feature timeline. Local assembly coordinates are preserved.','parts':records}
(out/'parts-catalog.json').write_text(json.dumps(catalog,indent=2))
readme='''TINFOX INDIVIDUAL CAD PARTS

All dimensions are millimetres. Each STEP contains the named component in its
local assembly coordinates. Import STEP into Fusion 360 as a solid body.
The files do not include a Fusion feature timeline. The parametric source is
model/build.py in the full review package.

Use parts-catalog.json to identify quantity, handedness, mating interfaces and
material. Distinct left/right and front/rear geometries have separate files.
Motor envelopes and provisional flexible gaiters are excluded from this set.

These are design prototypes, not approved manufacturing drawings. Verify
supplier motor datums, bearing fits, screw lengths, retention and print strength
before manufacturing loaded parts. CAD holes are nominal geometry; no threaded
hole or fit should be inferred from a file name.
'''
with zipfile.ZipFile(out/'tinfox-individual-cad.zip','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('README.txt',readme);z.write(out/'parts-catalog.json','parts-catalog.json')
 for p in records:z.write(out/p['step'],p['step'])
print(f'Indexed {len(records)} individual STEP parts, including {sum(p["category"]=="Mounts" for p in records)} motor-mount variants.')
