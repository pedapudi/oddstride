"""Quick raised equipment-head concept; dimensions are packaging assumptions."""
import copy,hashlib,json
import cadquery as cq
import numpy as np
import trimesh
from integrated_candidate import ROOT,box,cyl
from kinematics import P,POSES,matrix,uniform
import build as b
BASE=ROOT/'output/integrated-candidate';OUT=ROOT/'output/raised-head-prototype'
for p in [OUT,OUT/'step',OUT/'stl']:p.mkdir(exist_ok=True)
raw=(BASE/'model.json').read_bytes();model=json.loads(raw);P.update(model['parameters'])
HEAD_DROP=20.0
HEAD_FORWARD=12.0
HEAD_UP_DEG=7.0
HEAD_SETTLE=-3.0
HEAD_PIVOT=(218,0,94)
def posture_fraction(z):
 t=np.clip((z-54)/40,0,1)
 return t*t*(3-2*t)
def posed(shape,z=None):
 f=1.0 if z is None else posture_fraction(z)
 return shape.rotate(HEAD_PIVOT,(218,1,94),-HEAD_UP_DEG*f).translate((HEAD_FORWARD*f,0,HEAD_SETTLE*f))
def posed_point(x,y,z,section_z=None):
 f=1.0 if section_z is None else posture_fraction(section_z)
 a=np.deg2rad(HEAD_UP_DEG*f);dx=x-218;dz=z-94
 return (218+np.cos(a)*dx-np.sin(a)*dz+HEAD_FORWARD*f,y,94+np.sin(a)*dx+np.cos(a)*dz+HEAD_SETTLE*f)
LIDAR_X=posed_point(250,0,164)[0]
LIDAR_SEAT_Z=168.5
def neck_z(z):
 t=np.clip((z-54)/60,0,1)
 return z-HEAD_DROP*t*t*(3-2*t)
def src(k):return cq.importers.importStep(str(BASE/'step'/(k+'.step'))).val()
def loft(rows,wall=0):
 wires=[]
 for z,x,w,d in rows:
  q=cq.Workplane('XY',origin=(x,0,z)).rect(w-2*wall,d-2*wall).val()
  wires.append(q.fillet2D(min(18 if w>80 else 9,(w-2*wall)/2-1,(d-2*wall)/2-1),q.Vertices()))
 return cq.Solid.makeLoft(wires,ruled=False)
def organic_loft(rows):
 wires=[]
 for z,x,w,d,power in rows:
  points=[]
  for theta in np.linspace(0,2*np.pi,64,endpoint=False):
   co,si=np.cos(theta),np.sin(theta)
   points.append(cq.Vector(x+w/2*np.sign(co)*abs(co)**(2/power),d/2*np.sign(si)*abs(si)**(2/power),z))
  wires.append(posed(cq.Wire.assembleEdges([cq.Edge.makeSpline(points,periodic=True)]),z))
 return cq.Solid.makeLoft(wires,ruled=False)
# One continuous surface defines the neck, rear head and rounded chin.
# The detachable joint is a section through this surface, not a separate flange.
form_rows=[(44,128,44,96,2),(54,135,56,88,2),(70,148,60,64,2),
 (88,168,60,54,2),(104,195,66,58,2),(114,218,82,88,2.3),
 (116,224,90,98,2.4),(118,230,100,108,2.55),(120,236,110,118,2.7),
 (126,248,130,140,3),(144,260,136,146,3.8),(158,260,134,146,4),
 (174,255,126,138,4),(184,250,108,120,4)]
form_rows=[(neck_z(z),x,w,d,power) for z,x,w,d,power in form_rows]
form_outer=organic_loft(form_rows)
neck_region=posed(box(500,400,300,(200,0,-36-HEAD_DROP))) # upper face at Z114 minus the head drop
neck_outer=form_outer.intersect(neck_region)
outer=form_outer.cut(neck_region)
# Matching stations keep the inner wall from overshooting the throat transition.
inside=organic_loft([(z,x,w-8,d-8,power) for z,x,w,d,power in form_rows])
inside=inside.intersect(posed(box(500,400,62,(200,0,149-HEAD_DROP)))) # cavity and hardware follow the head
shell=outer.cut(inside)
# A lower-rear port joins the head cavity to the sloping cable neck.
port=posed(box(34,30,40,(222,0,115-HEAD_DROP),5))
shell=shell.cut(port).cut(cyl(15,50,(LIDAR_X,0,140),(0,0,1)))
visor=shell.intersect(posed(box(45,200,32,(330,0,146-HEAD_DROP),8)))
shell=shell.cut(visor)
for y in [-34,34]:
 hole=posed(cyl(10.3,40,(300,y,146-HEAD_DROP),(1,0,0)));shell=shell.cut(hole);visor=visor.cut(hole)
cut=posed(box(250,240,200,(250,0,68-HEAD_DROP))) # parting height follows the head
lower=shell.intersect(cut);lid=shell.cut(cut)
# Integral level seat preserves the horizontal scan band despite the upward gaze.
seat=cyl(32,18,(LIDAR_X,0,LIDAR_SEAT_Z-18),(0,0,1))
lid=lid.fuse(seat).cut(inside).cut(cyl(15,60,(LIDAR_X,0,130),(0,0,1)))
# Oval sections form a continuous curved neck, flared at both mounting interfaces.
def oval(rows):
 return cq.Solid.makeLoft([posed(cq.Workplane('XY',origin=(x,0,neck_z(z))).ellipse(w/2,d/2).val(),neck_z(z)) for z,x,w,d in rows],ruled=False)
# neck_outer is the lower section of the continuous head-and-neck loft.
neck_inner=oval([(40,127,30,44),(54,135,30,42),(70,148,28,34),(88,168,28,30),(104,195,30,32),(116,223,32,34)])
saddle=box(32,108,12,(127,0,48.8),4)
neck=neck_outer.fuse(saddle).cut(neck_inner)
body=src('body_center_0').fuse(cyl(32,4,(82,0,51.5),(0,0,1)))
# Clearance around the flared root leaves the upper cover independently removable.
body=body.cut(box(64,112,100,(132,0,70),4))
neck=neck.cut(body)
# Three recessed, side-accessible M3 x 30 screws close the structural halves.
neck_hardware=[]
seam_points=[(posed_point(x,0,neck_z(z),neck_z(z))[0],posed_point(x,0,neck_z(z),neck_z(z))[2]) for x,z in [(167,70),(148,88),(222,106)]]
for i,(x,z) in enumerate(seam_points):
 neck=neck.cut(cyl(1.7,100,(x,-50,z)))
 neck=neck.cut(cyl(3.1,36,(x,-50,z)))
 nut_pocket=b.hex_nut(5.8,40,x,12,z,.01).fuse(cyl(1.7,40,(x,12,z)))
 neck=neck.cut(nut_pocket)
 bolt=cyl(1.5,30,(x,-14,z)).fuse(cyl(2.75,3,(x,-17,z)))
 neck_hardware.append((f'neck_seam_screw_{i}',bolt,'M3 x 30 socket-head screw envelope. Recessed side access; threads are simplified.'))
 neck_hardware.append((f'neck_seam_nut_{i}',b.hex_nut(5.5,2.4,x,12,z,1.5),'M3 hex nut in an externally accessible hex pocket.'))
# Two vertical M4 screws secure the root directly to a revised front crossmember.
crossmember=cq.importers.importStep(str(ROOT/'output/step-parts/chassis_crossmember_121.step')).val()
for y in [-40,40]:
 hole=cyl(2.2,45,(121,y,25),(0,0,1))
 neck=neck.cut(hole).cut(cyl(4,25,(121,y,51),(0,0,1)))
 crossmember=crossmember.cut(hole)
 bolt=cyl(2,16,(121,y,35),(0,0,1)).fuse(cyl(3.5,4,(121,y,51),(0,0,1)))
 neck_hardware.append((f'neck_root_screw_{y}',bolt,'M4 x 16 socket-head screw through the root saddle and front crossmember. Install with the body cover removed.'))
 nut=b.hex_nut(7,3.2,0,0,0,2).rotate((0,0,0),(1,0,0),90).translate((121,y,37.6))
 neck_hardware.append((f'neck_root_nut_{y}',nut,'M4 hex nut below the front crossmember; accessible before the upper body cover is fitted.'))
# Accessible from inside the open head; each head fastener engages one neck half.
for y in [-22,22]:
 hole=posed(cyl(2.2,25,(218,y,100-HEAD_DROP),(0,0,1)))
 neck=neck.cut(hole);lower=lower.cut(hole)
 pocket=posed(b.hex_nut(7.2,3.5,0,0,0,.01).rotate((0,0,0),(1,0,0),90).translate((218,y,108-HEAD_DROP)))
 neck=neck.cut(pocket).cut(posed(box(12,60,3.5,(218,y-30 if y<0 else y+30,109.75-HEAD_DROP))))
 bolt=posed(cyl(2,12,(218,y,106-HEAD_DROP),(0,0,1)).fuse(cyl(3.5,4,(218,y,118-HEAD_DROP),(0,0,1))))
 neck_hardware.append((f'neck_head_screw_{y}',bolt,'M4 x 12 socket-head screw installed from inside the open head.'))
 nut=posed(b.hex_nut(7,3.2,0,0,0,2).rotate((0,0,0),(1,0,0),90).translate((218,y,108-HEAD_DROP)))
 neck_hardware.append((f'neck_head_nut_{y}',nut,'M4 hex nut loaded through the side slot before mounting the head.'))
# The open split exposes the complete cable channel and lies flat on the print bed.
neck_left=neck.intersect(box(300,150,250,(180,-75.1,80)))
neck_right=neck.intersect(box(300,150,250,(180,75.1,80)))
remove_prefix=('front_fascia','camera_','lens_','iris_','sensor_window','depth_sensor','body_nose_surround')
model['parts']=[p for p in model['parts'] if not p['name'].startswith(remove_prefix)]
# Remove the former head nuts along with its screws; retain the four rail bolts.
model['parts']=[p for p in model['parts'] if not p['name'].startswith('camera_hood_')]
template=copy.deepcopy(next(p for p in model['parts'] if p['name']=='body_center_0'))
custom={}
def add(name,s,color='#e5e7dc',material='petg',note='',replace=False):
 if not s.isValid():s=s.fix()
 assert s.isValid() and len(s.Solids())==1,(name,s.isValid(),len(s.Solids()))
 custom[name]=s;v,f=s.tessellate(.16,.12)
 model['meshes'][name]={'vertices':[list(q.toTuple()) for q in v],'faces':[list(q) for q in f]}
 p=copy.deepcopy(template);bb=s.BoundingBox();p.update(name=name,mesh=name,color=color,material=material,group='body',leg=None,check=True,volume_mm3=s.Volume(),mass_kg=s.Volume()*b.DENSITY.get(material,1.24e-6),com_mm=list(s.Center().toTuple()),bounds_mm=[bb.xlen,bb.ylen,bb.zlen],note=note)
 if replace:model['parts']=[q for q in model['parts'] if q['name']!=name]
 model['parts'].append(p)
 cq.exporters.export(s,str(OUT/'step'/(name+'.step')));cq.exporters.export(s,str(OUT/'stl'/(name+'.stl')),tolerance=.16,angularTolerance=.12)
 print(name,'valid',round(s.Volume()),flush=True)
add('body_center_0',body,replace=True,note='Prototype roof: lidar moved into the raised head; front relief accommodates the hollow neck.')
add('neck_left',neck_left,note='Structural left neck half. Lay the center split face on the print bed; the curved load path lies mainly within the layers. Lay cables into the open channel before closing. Three recessed M3 x 30 screws join the halves.')
add('neck_right',neck_right,note='Structural right neck half. Open cable channel, accessible nut recesses and a 0.2 mm center seam. Print with the center split face on the bed; local fastener recesses may need support.')
add('chassis_crossmember_121',crossmember,replace=True,material='aluminum',note='Front crossmember with two added 4.4 mm holes for the neck saddle. Drill or machine before assembly; nuts are accessible with the body cover removed.')
for name,shape,note in neck_hardware:add(name,shape,color='#626a65',material='steel',note=note)
add('equipment_head_lower',lower,note='Equipment enclosure with an integral rounded chin and rear throat. Its exterior continues the neck surface across the removable joint; two internal M4 screws attach it to the neck halves. Sensor packaging remains provisional.')
add('equipment_head_lid',lid,note='Removable upper head shell with an integral level lidar seat and crown cable opening. Fastening, gaskets and selected lidar mounting remain to be detailed.')
add('head_visor',visor,color='#263b37',note='Curved dark front visor with two provisional camera ports. Optical windows and sealing are not selected.')
for y in [-34,34]:
 add('head_camera_'+str(y),posed(cyl(10,15,(315,y,146-HEAD_DROP),(1,0,0))),color='#444c48',material='envelope',note='Provisional camera package, not a selected sensor.')
 add('head_lens_'+str(y),posed(cyl(7.5,1,(330,y,146-HEAD_DROP),(1,0,0))),color='#183d43',material='envelope',note='Optical surface placeholder.')
for name,z in [('lidar_base',LIDAR_SEAT_Z),('lidar',LIDAR_SEAT_Z+4),('lidar_lid',LIDAR_SEAT_Z+22)]:
 p=next(p for p in model['parts'] if p['name']==name);m=model['meshes'][p['mesh']];v=np.asarray(m['vertices']);lo=v.min(0);hi=v.max(0);delta=np.array([LIDAR_X-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,z-lo[2]])
 # Give moved equipment its own mesh so no other part placement changes.
 key=name+'_raised';model['meshes'][key]={'vertices':(v+delta).tolist(),'faces':m['faces']};p['mesh']=key;p['com_mm']=(np.asarray(p['com_mm'])+delta).tolist();p['note']='Existing lidar envelope relocated to the head crown; the scan band is above the shell. Sensor selection and field of view remain provisional.'
# Show the usable mounting volume without adding fictitious equipment mass.
model['status']='Raised equipment-head packaging prototype. Head and neck geometry checked at sampled poses; hardware, sensors and load qualification unfinished.'
model['source_model_sha256']=hashlib.sha256(raw).hexdigest()
encoded=json.dumps(model,separators=(',',':')).encode();(OUT/'model.json').write_bytes(encoded);stamp=hashlib.sha256(encoded).hexdigest()
assembly=cq.Assembly(name='Raised_equipment_head_prototype')
for name,s in custom.items():
 if name not in ['body_center_0','chassis_crossmember_121']:assembly.add(s,name=name)
assembly.export(str(OUT/'head-and-neck.step'))
fit_rows=[]
for a in ['neck_left','neck_right']:
 for name,shape in custom.items():
  if name==a:continue
  if name in ['head_visor','equipment_head_lid'] or name.startswith('head_camera') or name.startswith('head_lens'):continue
  overlap=custom[a].intersect(shape).Volume()
  fit_rows.append({'a':a,'b':name,'overlap_mm3':overlap})
tool_rows=[]
tools=[]
for i,(x,z) in enumerate(seam_points):tools.append((f'seam_{i}',cyl(2,100,(x,-17.1,z),(0,-1,0))))
for y in [-40,40]:tools.append((f'root_{y}',cyl(2,100,(121,y,55.1),(0,0,1))))
for y in [-22,22]:tools.append((f'head_{y}',posed(cyl(2,80,(218,y,122.1-HEAD_DROP),(0,0,1)))))
for name,tool in tools:
 hits=[]
 for key in ['neck_left','neck_right','equipment_head_lower','chassis_crossmember_121']:
  v=tool.intersect(custom[key]).Volume()
  if v>.05:hits.append({'part':key,'overlap_mm3':v})
 tool_rows.append({'tool':name,'hits':hits})
print('DRIVER ACCESS',tool_rows,flush=True)
(OUT/'neck-fit.json').write_text(json.dumps({'model_sha256':stamp,'pairs':fit_rows,'driver_access':tool_rows,'scope':'Solid interference in the neck mounting stack. Contact strength, fastener preload, fit tolerances and hand clearance require separate checks. A 4 mm diameter straight driver shaft is checked with the head lid and body cover removed; this does not model a driver handle.'},indent=2))
print('MOUNT OVERLAPS',[(r['a'],r['b'],round(r['overlap_mm3'],3)) for r in fit_rows if r['overlap_mm3']>.05],flush=True)
# Targeted moving-limb clearance, with inherited unrelated intersections retained.
meshes={k:trimesh.Trimesh(vertices=m['vertices'],faces=m['faces'],process=False) for k,m in model['meshes'].items()}
new={p['name']:p for p in model['parts'] if (p['name'] in custom and p['name']!='chassis_crossmember_121') or p['name'].startswith('lidar')}
head=trimesh.collision.CollisionManager();limbs=trimesh.collision.CollisionManager()
for n,p in new.items():head.add_object(n,meshes[p['mesh']])
moving={p['name']:p for p in model['parts'] if p.get('leg') and p.get('service_role') not in ['keepout','withdrawal']}
for n,p in moving.items():limbs.add_object(n,meshes[p['mesh']])
def check(q):
 for n,p in moving.items():limbs.set_transform(n,matrix(p,q))
 _,pairs=limbs.in_collision_other(head,return_names=True);return sorted([sorted(t) for t in pairs])
prior=json.loads((BASE/'audit.json').read_text());results=[]
retained={p['name'] for p in model['parts']}
for row in prior['motion_samples']:
 old=[pair for pair in row['hits'] if all(n in retained for n in pair) and not any(n in new for n in pair)]
 hits=check(row['angles']);results.append({**row,'hits':sorted(old+hits),'head_and_roof_hits':hits,'passed':not(old+hits)})
sweep=[{'roll_deg':r,'hits':check(uniform([r,30,-60]))} for r in range(-60,61,2)]
report={'model_sha256':stamp,'motion_samples':results,'roll_sweep':sweep,'scope':'New head, neck, roof and relocated lidar against all modeled leg parts at 35 poses and 61 roll samples. Unchanged unrelated collisions inherited from the source model. No sensor, structural, cable-flex or manufacturing qualification.'}
(OUT/'audit.json').write_text(json.dumps(report,indent=2))
(OUT/'packaging.json').write_text(json.dumps({'model_sha256':stamp,'shoulder_axis_x_mm':185,'head_center_mm':posed_point(258,0,140),'placement_change':{'forward_mm':HEAD_FORWARD,'upward_gaze_deg':HEAD_UP_DEG,'settle_mm':HEAD_SETTLE},'lidar_seat_z_mm':LIDAR_SEAT_Z,'junction':'Continuous exterior with a tilted removable throat joint; no external flange.','head_drop_mm':HEAD_DROP,'head_lower_bounds_z_mm':[lower.BoundingBox().zmin,lower.BoundingBox().zmax],'head_lid_max_z_mm':lid.BoundingBox().zmax,'lidar_scan_band_z_mm':[LIDAR_SEAT_Z+4,LIDAR_SEAT_Z+22],'gross_cavity_litres':inside.Volume()/1e6,'cavity_note':'Gross enclosed cavity before neck overlap, sensor envelopes, walls around mounts or cooling hardware.','head_mass_kg':sum(p['mass_kg'] for p in model['parts'] if p['name'] in custom and p['name'] not in ['body_center_0','chassis_crossmember_121']),'neck_root_channel_mm':[30,42],'neck_split_gap_mm':0.2,'assembly_sequence':['Bolt each neck half to the exposed front crossmember; leave screws loose.','Lay cables in the channel; close the halves with three side M3 screws and tighten root fasteners.','Install the head using two M4 screws from inside the open enclosure; connect sensors.','Fit the head lid and body cover.'],'manufacturing_note':'Side halves fit within roughly 160 x 54 mm in the split plane. Print split-face down; local counterbores may require supports. Fit, strength and tool-access qualification remain provisional.'},indent=2))
print('RAISED HEAD COMPLETE',[(r['pose'],r['head_and_roof_hits']) for r in results],'roll hits',sum(bool(r['hits']) for r in sweep),flush=True)
