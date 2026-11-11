"""Index the exact individual STEP solids and package them for CAD review."""
import hashlib,json,zipfile,re
from pathlib import Path
from kinematics import ROOT
out=ROOT/'output';raw=(out/'model.json').read_bytes();model=json.loads(raw)
roles={
 'nose_standoff':('Sensor-panel support tab','Body','Joins the inset nose panel to the surrounding body rim.','Two Ø3 mm holes; front contact faces meet the panel and the rear face of the rim.','Machined aluminum; select screws/nuts and verify thread engagement and panel stiffness.'),
 'roll_cartridge':('Fixed roll-motor and bearing mount','Mounts','Bolts the roll stator to the chassis and houses the roll bearing.','Nine Ø3.4 mm stator holes on a 73 mm pitch circle; 66.2 mm nominal bearing bore.','Machined aluminum; bearing retention, screw engagement and fits need review.'),
 'motor_carrier':('Roll-output / hip-motor carrier','Mounts','Carries the hip-pitch stator on the roll actuator output.','Perpendicular motor axes; six Ø4.4 mm roll-output holes on a 24 mm pitch circle and nine Ø3.4 mm hip-stator holes on a 73 mm pitch circle.','Machined aluminum; check tool access, bearing journal tolerance and motor datums.'),
 'hip_hub':('Hip-output coupling','Mounts','Connects the hip output to the proximal knee-motor support ties.','Six Ø4.4 mm output holes on a 24 mm pitch circle; three tie positions at 43.5 mm radius.','Machined aluminum; select screws and confirm output pilot clearance.'),
 'motor_mount_ring':('Knee-motor stator plate','Mounts','Spreads knee-stator loads into the metal ties and the integrated thigh cradle.','Nine Ø3.4 mm stator holes on a 73 mm pitch circle; three tie positions at 43.5 mm radius.','3 mm aluminum plate; finish holes and verify motor-face contact.'),
 'knee_drive_adapter':('Knee-output spacer adapter','Mounts','Connects the knee actuator output to the input crank.','Six Ø4.4 mm output holes on a 24 mm pitch circle.','Machined aluminum; verify pilot, screw lengths and axial stack.'),
 'thigh_inner':('Integrated motor cradle / inner thigh','Limbs','Combines the recessed knee-motor housing and inner structural thigh half.','170 mm hip-to-knee spacing; metal stator plate and compression sleeves distribute motor loads.','PETG prototype; joint fits and printed strength remain unqualified.'),
 'thigh_outer':('Sculpted outer thigh','Limbs','Closes the structural thigh sandwich and provides a recessed cap seat.','Variable outer depth; 170 mm hip-to-knee spacing; removable fasteners.','PETG prototype; preserve the wall geometry and review supports in the slicer.'),
 'shin_inner':('Inner structural shin','Limbs','Supports the knee-bearing carrier and joins the foot end.','6001-size bearing housed in a separate metal carrier.','PETG prototype; use both halves and qualify the printed load path.'),
 'shin_outer':('Outer structural shin','Limbs','Closes the curved shin around the bearing carriers and knee rocker.','Pairs with the inner shin and through-fasteners.','PETG prototype; use both halves and qualify the printed load path.'),
 'input_crank':('Knee input crank','Transmission','Converts actuator rotation into pushrod travel.','22 mm crank radius; six output-interface holes and Ø6 mm rod-pin hole.','Machined aluminum; final pins, washers and retention remain to be selected.'),
 'output_crank':('Knee output rocker','Transmission','Transfers pushrod load to the shin at the rear of the knee.','22 mm crank radius; installed −78° phase; Ø6 mm rod-pin hole.','Machined aluminum; final pins, washers and retention remain to be selected.'),
 'pushrod':('Knee pushrod','Transmission','Joins the equal-radius input and output cranks.','170 mm eye spacing; Ø6 mm pin holes.','Steel part; pinned joints and fatigue strength need qualification.'),
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
 role=re.sub(r'(?<=[A-Za-z])(?=\d)',' ',role)
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
