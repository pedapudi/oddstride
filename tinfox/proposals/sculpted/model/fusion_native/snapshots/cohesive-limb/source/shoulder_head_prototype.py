"""Compact equipment head with a short plinth and a rail-mounted metal saddle."""
import copy,hashlib,json,os
import cadquery as cq
import numpy as np
import trimesh
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from integrated_candidate import ROOT,box,cyl
from kinematics import P,POSES,matrix,uniform
import build as b
import refined_limb
BASE=ROOT/'output/integrated-candidate';OUT=ROOT/'output'/os.environ.get('TINFOX_BUILD_FOLDER','shoulder-head-work')
for p in [OUT,OUT/'step',OUT/'stl']:p.mkdir(exist_ok=True)
raw=(BASE/'model.json').read_bytes();model=json.loads(raw);P.update(model['parameters'])
def src(k):
 for p in [BASE/'step'/(k+'.step'),ROOT/'output/v0-rounded-body/step'/(k+'.step'),ROOT/'output/service-design/step'/(k+'.step'),ROOT/'output/step-parts'/(k+'.step')]:
  if p.exists():return cq.importers.importStep(str(p)).val()
 raise FileNotFoundError(k)
def organic_loft(rows):
 wires=[]
 for z,x,w,d,power in rows:
  edges=[]
  for quarter in range(4):
   pts=[]
   for t in np.linspace(quarter*np.pi/2,(quarter+1)*np.pi/2,17):
    a,c=np.cos(t),np.sin(t)
    if abs(a)<1e-12:a=0
    if abs(c)<1e-12:c=0
    pts.append(cq.Vector(x+w/2*np.sign(a)*abs(a)**(2/power),d/2*np.sign(c)*abs(c)**(2/power),z))
   edges.append(cq.Edge.makeSpline(pts))
  wires.append(cq.Wire.assembleEdges(edges))
 # Cubic interpolation keeps the closely spaced shoulder sections stable when
 # split and bored; the default high-degree surface fails half-space cuts.
 loft=BRepOffsetAPI_ThruSections(True,False)
 loft.SetMaxDegree(3)
 for wire in wires:loft.AddWire(wire.wrapped)
 loft.Build()
 return cq.Solid(loft.Shape())
def nut_z(af,h,x,y,z,bore):return b.hex_nut(af,h,0,0,0,bore).rotate((0,0,0),(1,0,0),90).translate((x,y,z))
def ring_z(ro,ri,h,x,y,z):return cyl(ro,h,(x,y,z),(0,0,1)).cut(cyl(ri,h+2,(x,y,z-1),(0,0,1)))
# Compact head center is directly above the front hip axes (X185).
rows=[(48,96,108,116,3),(58,102,104,114,2.8),(66,116,100,110,2.6),(78,132,108,104,2.5),
 (90,147,110,104,2.5),(98,155,116,112,2.7),(102,163,122,122,2.8),
 (110,176,132,138,3.2),(130,185,136,146,4),(146,183,130,140,4),
 (154,180,120,132,4),(162,178,106,118,4)]
outer=organic_loft(rows)
inner=organic_loft([(z,x,w-10,d-10,p) for z,x,w,d,p in rows])
head_region=box(500,400,200,(180,0,198)) # lower face Z98
head_outer=outer.intersect(head_region)
inside=inner.intersect(box(500,400,56,(180,0,130))) # cavity Z102..158
shell=head_outer.cut(inside)
port=box(30,26,30,(151,0,98),5)
shell=shell.cut(port).cut(cyl(15,40,(178,0,140),(0,0,1)))
visor=shell.intersect(box(42,200,34,(256,0,129),11));shell=shell.cut(visor)
for y in [-34,34]:
 tool=cyl(13.2,45,(230,y,129),(1,0,0));shell=shell.cut(tool);visor=visor.cut(tool)
parting=box(400,300,200,(180,0,48));lower=shell.intersect(parting);lid=shell.cut(parting)
# A short hollow plinth has thick root and upper diaphragms rather than a narrow throat.
neck=outer.cut(head_region)
chamber=organic_loft([(56,114,68,82,3),(70,125,82,78,2.5),(84,141,86,78,2.5)])
neck=neck.cut(chamber).cut(port).cut(cyl(14,30,(82,0,44),(0,0,1)))
for side in [-1,1]:
 # Coaxial clearance for the shoulder motor complex; moving shells are audited separately.
 neck=neck.cut(cyl(72,130,(132,side*68,0),(1,0,0)))
# A flat metal saddle transfers head loads to both side rails through four standoffs.
bridge=box(64,196,4,(46,0,46),1.5).fuse(box(80,100,4,(84,0,46),1.5))
bridge=bridge.cut(cyl(16,10,(82,0,41),(0,0,1)))
for y in [-70,70]:bridge=bridge.cut(box(30,28,10,(46,y,46),3))
# Preserve the fixed motor connector insertion and cable envelopes.
for y in [-45,45]:bridge=bridge.cut(box(24,34,16,(80,y,46),2))
rails={side:src('chassis_beam_'+str(side*102)) for side in [-1,1]}
neck_hardware=[];extra=[];driver_tools=[]
for side in [-1,1]:
 rail=rails[side].fuse(box(48,24,4,(46,side*94,34),1))
 for x in [30,62]:
  y=side*90;hole=cyl(2.2,35,(x,y,20),(0,0,1));rail=rail.cut(hole);bridge=bridge.cut(hole)
  spacer=ring_z(4,2.2,8,x,y,36)
  extra.append((f'head_bridge_spacer_{x}_{side}',spacer,'aluminum','Standard 8 mm long M4 clearance spacer, 8 mm outer diameter. Final procurement remains to be verified.'))
  neck_hardware.extend([(f'head_bridge_screw_{x}_{side}',cyl(2,25,(x,y,24),(0,0,1)).fuse(cyl(3.5,4,(x,y,49),(0,0,1))),'M4 x 25 socket-head screw through washers, saddle, spacer and rail ear.'),
   (f'head_bridge_nut_{x}_{side}',nut_z(7,3.2,x,y,27.8,2),'M4 nut under the rail ear; assemble before fitting the head module.'),
   (f'head_bridge_washer_top_{x}_{side}',ring_z(4.5,2.15,1,x,y,48),'M4 flat washer.'),
   (f'head_bridge_washer_bottom_{x}_{side}',ring_z(4.5,2.15,1,x,y,31),'M4 flat washer.')])
  driver_tools.append((f'bridge_{x}_{side}',cyl(2,90,(x,y,53.1),(0,0,1)),['neck_left','neck_right','equipment_head_lower']))
 rails[side]=rail
# Four root fasteners clamp broad integral columns onto the saddle.
for x in [94,110]:
 for y in [-24,24]:
  neck=neck.fuse(cyl(8,14,(x,y,48),(0,0,1)).intersect(outer))
  hole=cyl(2.2,40,(x,y,36),(0,0,1));neck=neck.cut(hole).cut(cyl(5,110,(x,y,57.2),(0,0,1)));bridge=bridge.cut(hole)
  neck_hardware.extend([(f'neck_root_screw_{x}_{y}',cyl(2,20,(x,y,38),(0,0,1)).fuse(cyl(3.5,4,(x,y,58),(0,0,1))),'M4 x 20 socket-head root screw; install with the equipment head removed.'),
   (f'neck_root_washer_{x}_{y}',ring_z(4.5,2.15,.8,x,y,57.2),'M4 flat washer spreads the clamp load over the printed column.'),
   (f'neck_root_nut_{x}_{y}',nut_z(7,3.2,x,y,40.8,2),'M4 nut below the metal saddle, clear of the shoulder motors.')])
  driver_tools.append((f'root_{x}_{y}',cyl(2,110,(x,y,62.1),(0,0,1)),['equipment_head_lower']))
# Accessible seam fasteners remain outside the central wiring passage.
seam_points=[(88,64),(175,87),(110,87)]
for i,(x,z) in enumerate(seam_points):
 neck=neck.cut(cyl(2.2,160,(x,-80,z))).cut(cyl(3.8,52,(x,-80,z)))
 neck=neck.cut(b.hex_nut(7.2,60,x,24,z,.01)).cut(cyl(2.2,60,(x,24,z)))
 neck_hardware.extend([(f'neck_seam_screw_{i}',cyl(2,60,(x,-28,z)).fuse(cyl(3.5,4,(x,-32,z))),'M4 x 60 socket-head screw joins the two plinth halves.'),
  (f'neck_seam_nut_{i}',b.hex_nut(7,3.2,x,24,z,2),'M4 nut in an accessible side pocket.')])
 driver_tools.append((f'seam_{i}',cyl(2,90,(x,-32.1,z),(0,-1,0)),[]))
for x in [139,167]:
 for y in [-30,30]:
  hole=cyl(2.2,32,(x,y,80),(0,0,1));neck=neck.cut(hole);lower=lower.cut(hole)
  neck=neck.cut(nut_z(7.2,3.5,x,y,88,.01)).cut(box(12,70,3.5,(x,y+35*(1 if y>0 else -1),89.75)))
  neck_hardware.extend([(f'neck_head_screw_{x}_{y}',cyl(2,16,(x,y,86),(0,0,1)).fuse(cyl(3.5,4,(x,y,102),(0,0,1))),'M4 x 16 screw installed from inside the open head; four fasteners distribute impact loads.'),
   (f'neck_head_nut_{x}_{y}',nut_z(7,3.2,x,y,88,2),'M4 nut retained below the thick upper plinth diaphragm.')])
  driver_tools.append((f'head_{x}_{y}',cyl(2,80,(x,y,106.1),(0,0,1)),[]))
body=src('body_center_0').fuse(cyl(32,4,(82,0,51.5),(0,0,1)))
# A shallow crown encloses the saddle while leaving a serviceable roof.
crown=organic_loft([(46,46,140,218,4),(52,46,138,216,4),(58,46,128,194,4)])
crown=crown.cut(box(400,400,100,(46,0,1.5))) # cavity ceiling Z51.5
body=body.cut(box(70,202,6,(46,0,46),2)).cut(box(84,104,6,(84,0,46),2)).fuse(crown)
belly=src('belly_center_0')
# Local lateral scallops clear the folded thigh at zero roll. Larger rolled-in
# paths still require a coupled joint envelope because the battery is fixed.
for side in [-1,1]:
 for x,z,r in [(17,0,22),(19,-22,22),(119,13.5,9)]:
  tool=cyl(r,35,(x,side*106.5,z),(0,side,0))
  body=body.cut(tool);belly=belly.cut(tool)
 # A long, shallow recess replaces the abrupt openings while keeping the
 # outside wall inboard of the folded shin. Both shells share one smooth profile.
 def side_oval(y,w,h):return cq.Workplane('XZ',origin=(25,y,-7)).ellipse(w/2,h/2).val()
 inset=cq.Solid.makeLoft([side_oval(side*y,160,100) for y in [103.5,112.5]],ruled=True)
 pocket=cq.Solid.makeLoft([side_oval(side*y,w,h) for y,w,h in [(106.5,144,86),(112.5,158,100),(120,176,118)]],ruled=False)
 inset=inset.cut(pocket)
 for x in [-52,52]:inset=inset.cut(cyl(4.5,30,(x,side*95,-6),(0,side,0)))
 body=body.fuse(inset.intersect(box(800,800,200,(0,0,90))))
 belly=belly.fuse(inset.intersect(box(800,800,70,(0,0,-45.3))))

body=body.cut(organic_loft([(z,x,w+1.2,d+1.2,p) for z,x,w,d,p in rows]))
for x in [30,62]:
 for y in [-90,90]:body=body.cut(cyl(4.8,30,(x,y,40),(0,0,1)))
for x in [94,110]:
 for y in [-24,24]:body=body.cut(cyl(3,40,(x,y,30),(0,0,1)))
neck=neck.cut(body)
neck_left=neck.intersect(box(400,180,250,(170,-90.1,100)))
neck_right=neck.intersect(box(400,180,250,(170,90.1,100)))
# Elastomer bumper is below the camera apertures and lidar scan band.
bumper_outer=organic_loft([(z,x,w+4,d+4,p) for z,x,w,d,p in rows])
bumper=bumper_outer.cut(outer).intersect(box(400,300,8,(180,0,115)))
extra.extend([('head_bridge',bridge,'aluminum','4 mm aluminum saddle transfers head loads to both chassis rails. Printed substitutes are fit mockups; impact capacity is unqualified.'),
 ('head_bumper',bumper,'rubber','Replaceable elastomer bumper envelope; material, retention and energy absorption remain to be selected.'),
 *[(f'chassis_beam_{side*102}',rail,'aluminum','Side rail with integral mounting ears for the head saddle. Four M4 attachments bypass the removable body cover and thin front crossmember.') for side,rail in rails.items()]])
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
add('belly_center_0',belly,replace=True,note='Lower shell with local lateral thigh reliefs. Battery/frame interference still bounds combined hip-roll and hip-pitch travel.')
add('neck_left',neck_left,note='Structural left plinth half with broad root, hollow interior and thick upper diaphragm. Print split-face down; local bores may require supports. Fit and impact strength remain unqualified.')
add('neck_right',neck_right,note='Structural right plinth half with open wiring cavity, accessible nuts and broad bolted interfaces. Print split-face down.')
for name,shape,material,note in extra:add(name,shape,material=material,note=note,replace=name.startswith('chassis_beam'),color='#c2c8bd' if material=='rubber' else '#b6bcb5' if material=='aluminum' else '#e5e7dc')
for name,shape,note in neck_hardware:add(name,shape,color='#626a65',material='steel',note=note)
add('equipment_head_lower',lower,note='Compact rounded equipment head centered over the front hip axes. Four internal M4 screws attach it to the short structural plinth.')
add('equipment_head_lid',lid,note='Removable upper head shell with a level lidar seat and crown cable opening. Fastening, gaskets and selected lidar mounting remain to be detailed.')
add('head_visor',visor,color='#263b37',note='Curved dark front visor with two provisional camera ports. Optical windows and sealing are not selected.')
for y in [-34,34]:
 add('head_camera_'+str(y),cyl(10,16,(235,y,129),(1,0,0)),color='#444c48',material='envelope',note='Provisional camera envelope.')
 add('head_lens_'+str(y),cyl(12.6,.8,(251.3,y,129),(1,0,0)),color='#193c40',material='envelope',note='Flush optical-window placeholder; cameras remain level, with no upward head tilt.')
for name,z in [('lidar_base',162),('lidar',166),('lidar_lid',184)]:
 p=next(p for p in model['parts'] if p['name']==name);m=model['meshes'][p['mesh']];v=np.asarray(m['vertices']);lo=v.min(0);hi=v.max(0);delta=np.array([178-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,z-lo[2]])
 key=name+'_shoulder';model['meshes'][key]={'vertices':(v+delta).tolist(),'faces':m['faces']};p['mesh']=key;p['com_mm']=(np.asarray(p['com_mm'])+delta).tolist();p['note']='Provisional level lidar envelope. The crown-mounted sensor remains exposed during an inverted fall.'
for base_key,shape in refined_limb.custom_parts().items():
 for right in [False,True]:
  s=shape.mirror('XZ') if right else shape;key=base_key+('_right' if right else '')
  assert s.isValid() and len(s.Solids())==1,key
  vertices,faces=s.tessellate(.12,.1);bb=s.BoundingBox()
  model['meshes'][key]={'vertices':[list(v.toTuple()) for v in vertices],'faces':[list(f) for f in faces]}
  for p in model['parts']:
   if p['mesh']==key:p.update(volume_mm3=s.Volume(),mass_kg=p['mass_kg'] if key.startswith('bearing_') else s.Volume()*b.DENSITY[p['material']],com_mm=list(s.Center().toTuple()),bounds_mm=[bb.xlen,bb.ylen,bb.zlen],note='Shared structural clamshell profile, cam-shaped shin head and coordinated carrier/clamp clearance revision. See limb interface and folding reports.')
  cq.exporters.export(s,str(OUT/'step'/(key+'.step')));cq.exporters.export(s,str(OUT/'stl'/(key+'.stl')),tolerance=.12,angularTolerance=.1)
model['parameters'].update(refined_limb.geometry_parameters())
# Show the usable mounting volume without adding fictitious equipment mass.
model['status']='Shoulder-mounted head prototype. Broad plinth and metal rail saddle replace the exposed neck. Fall survival, printed strength and manufacturing tolerances are unqualified.'
model['source_model_sha256']=hashlib.sha256(raw).hexdigest()
encoded=json.dumps(model,separators=(',',':')).encode();(OUT/'model.json').write_bytes(encoded);stamp=hashlib.sha256(encoded).hexdigest()
assembly=cq.Assembly(name='Raised_equipment_head_prototype')
for name,s in custom.items():
 if name not in ['body_center_0','belly_center_0','chassis_beam_102','chassis_beam_-102']:assembly.add(s,name=name)
assembly.export(str(OUT/'head-and-neck.step'))
fit_rows=[]
for a in ['neck_left','neck_right']:
 for name,shape in custom.items():
  if name==a:continue
  if name in ['head_visor','equipment_head_lid'] or name.startswith('head_camera') or name.startswith('head_lens'):continue
  overlap=custom[a].intersect(shape).Volume()
  fit_rows.append({'a':a,'b':name,'overlap_mm3':overlap})
tool_rows=[]
for name,tool,removed in driver_tools:
 hits=[]
 for key in ['neck_left','neck_right','equipment_head_lower','head_bridge']:
  if key in removed:continue
  v=tool.intersect(custom[key]).Volume()
  if v>.05:hits.append({'part':key,'overlap_mm3':v})
 tool_rows.append({'tool':name,'removed_for_access':removed,'hits':hits})
print('DRIVER ACCESS',tool_rows,flush=True)
(OUT/'neck-fit.json').write_text(json.dumps({'model_sha256':stamp,'pairs':fit_rows,'driver_access':tool_rows,'scope':'Solid interference in the neck mounting stack. Contact strength, fastener preload, fit tolerances and hand clearance require separate checks. A 4 mm diameter straight driver shaft is checked with the head lid and body cover removed; this does not model a driver handle.'},indent=2))
print('MOUNT OVERLAPS',[(r['a'],r['b'],round(r['overlap_mm3'],3)) for r in fit_rows if r['overlap_mm3']>.05],flush=True)
# Targeted moving-limb clearance, with inherited unrelated intersections retained.
meshes={k:trimesh.Trimesh(vertices=m['vertices'],faces=m['faces'],process=False) for k,m in model['meshes'].items()}
new={p['name']:p for p in model['parts'] if p['name'].startswith(('neck_','head_','equipment_head','lidar','chassis_beam_')) or p['name'] in ['body_center_0','belly_center_0']}
head=trimesh.collision.CollisionManager();limbs=trimesh.collision.CollisionManager()
for n,p in new.items():head.add_object(n,meshes[p['mesh']])
moving={p['name']:p for p in model['parts'] if p.get('leg') and p.get('service_role') not in ['keepout','withdrawal']}
for n,p in moving.items():limbs.add_object(n,meshes[p['mesh']])
def check(q):
 for n,p in moving.items():limbs.set_transform(n,matrix(p,q))
 _,pairs=limbs.in_collision_other(head,return_names=True)
 # The stationary roll cartridge is mounted to the side rail. Match the
 # viewer's rigid body/mount exclusion; moving thigh-to-rail hits remain.
 return sorted([sorted((a,c)) for a,c in pairs if not (moving[a]['group']=='mount' and c.startswith('chassis_beam_'))])
prior=json.loads((BASE/'audit.json').read_text());results=[]
retained={p['name'] for p in model['parts']}
import importlib.util
spec=importlib.util.spec_from_file_location('review_server',ROOT.parents[2]/'viewer/serve.py')
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
engine=review.Engine(OUT/'model.json')
for row in prior['motion_samples']:
 hits=check(row['angles']);all_hits=engine.check(row['angles'])['pairs']
 results.append({**row,'hits':all_hits,'head_and_roof_hits':hits,'passed':not all_hits})
sweep=[{'roll_deg':r,'hits':check(uniform([r,30,-60]))} for r in range(-60,61,2)]
report={'model_sha256':stamp,'motion_samples':results,'roll_sweep':sweep,'scope':'New head, neck, roof and relocated lidar against all modeled leg parts at 35 poses and 61 roll samples. Unchanged unrelated collisions inherited from the source model. No sensor, structural, cable-flex or manufacturing qualification.'}
(OUT/'audit.json').write_text(json.dumps(report,indent=2))
(OUT/'packaging.json').write_text(json.dumps({'model_sha256':stamp,'head_center_x_mm':185,'shoulder_axis_x_mm':185,'head_roof_z_mm':162,'lidar_scan_band_z_mm':[166,184],'gross_cavity_litres':inside.Volume()/1e6,'load_path':['Head shell and thick lower flange','Four M4 head screws','Two structural plinth halves with upper and root diaphragms','Four M4 root screws','4 mm aluminum saddle and four metal spacers','Four M4 through-bolts and integral side-rail ears'],'assembly_sequence':['Attach saddle and spacers to the modified rails.','Attach plinth halves with the head absent, lay in wiring, and close the seam.','Attach the head from inside the open enclosure, then fit sensors and lid.'],'fall_limitations':['No drop-test or strength qualification.','Head-first impacts can involve whole-robot inertia.','The top-mounted lidar remains exposed in an inverted fall.','Elastomer bumper is not a certified energy absorber.'],'manufacturing_note':'Plinth halves print on their center split planes. Saddle is a flat 4 mm metal plate. Rail ears require revised rails; they are not supported by the removable body shell.'},indent=2))
print('RAISED HEAD COMPLETE',[(r['pose'],r['head_and_roof_hits']) for r in results],'roll hits',sum(bool(r['hits']) for r in sweep),flush=True)
