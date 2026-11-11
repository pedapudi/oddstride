"""Audit staged tool access, part withdrawal and the revised body attachments."""
import hashlib,json
from pathlib import Path
import cadquery as cq
from build import face_x,box
import numpy as np
import trimesh
from kinematics import ROOT,POSES,matrix
out=ROOT/'output';raw=(out/'model.json').read_bytes();model=json.loads(raw)
parts={p['name']:p for p in model['parts']};meshes={}
for name,p in parts.items():
 d=model['meshes'][p['mesh']];m=trimesh.Trimesh(vertices=d['vertices'],faces=d['faces'],process=False)
 m.apply_transform(matrix(p,POSES['stand']));meshes[name]=m

def manager(removed=()):
 cm=trimesh.collision.CollisionManager()
 for name,p in parts.items():
  if name not in removed and p['check']:cm.add_object(name,meshes[name])
 return cm

def stage_path(label,moving,removed,delta,steps=61):
 cm=manager(set(removed)|set(moving));hits=[]
 fractions=np.r_[.0001,.001,.0025,.005,np.linspace(.01,1,steps)]
 for i,t in enumerate(fractions):
  tf=np.eye(4);tf[:3,3]=np.array(delta)*t
  for name in moving:
   if not parts[name]['check'] and name not in ['lidar','lidar_base','lidar_lid']:continue
   collision,names=cm.in_collision_single(meshes[name],transform=tf,return_names=True)
   if collision:hits.append({'fraction':round(float(t),4),'part':name,'with':sorted(names)})
 return {'name':label,'moving_parts':moving,'removed_before':sorted(removed),'translation_mm':delta,'samples':len(fractions),'collision_samples':len(hits),'first_interferences':hits[:8]}

roof=['body_center_0','power_button','status_display','status_display_dial','lidar','lidar_base','lidar_lid','body_wordmark','body_serial','body_status_dot']
sides=[]
cover_screws=[n for n in parts if n.startswith('body_service_screw_')]
tray_screws=[n for n in parts if n.startswith('tray_screw_')]
cassette_screws=[n for n in parts if n.startswith('cassette_screw_')]
cassette_group=[n for n in parts if n.startswith(('battery_','cassette_nut_'))]
paths=[stage_path('Lift top-and-side clamshell',roof,cover_screws,[0,0,110]),
       stage_path('Lift electronics tray and computer',['electronics_shelf','electronics_clearance'],roof+cover_screws+tray_screws,[0,0,120]),
       stage_path('Lower battery cassette with electronics installed',cassette_group,roof+cover_screws+cassette_screws,[0,0,-100])]

def tool(label,origin,axis,removed):
 origin=np.array(origin,float);axis=np.array(axis,float);cm=manager(removed)
 volumes=[]
 for radius,length,offset in [(1.5,6,0),(3,60,6),(10,45,66)]:
  tf=trimesh.geometry.align_vectors([0,0,1],axis);tf[:3,3]=origin+axis*(offset+length/2)
  shape=trimesh.creation.cylinder(radius=radius,height=length,sections=24,transform=tf)
  hit,names=cm.in_collision_single(shape,return_names=True)
  volumes.append({'radius_mm':radius,'length_mm':length,'hits':sorted(names) if hit else []})
 return {'name':label,'origin_mm':origin.tolist(),'axis':axis.tolist(),'removed_before':sorted(removed),'volumes':volumes,'clear':not any(v['hits'] for v in volumes)}

tools=[]
for side in [-1,1]:
 for x in [-112,112]:tools.append(tool(f'Roof/side cover screw {side} {x}',[x,side*112.1,22],[0,side,0],cover_screws))
 for x in [-52,52]:
  tools.append(tool(f'Independent cassette screw {side} {x}',[x,side*106.1,-6],[0,side,0],roof+sides+cover_screws+cassette_screws))
  tools.append(tool(f'Top electronics deck screw {side} {x}',[x,side*88,10.6],[0,0,1],roof+cover_screws+tray_screws))
 for x in [-63,63]:tools.append(tool(f'Fixed lower brace screw {side} {x}',[x,side*97,6.6],[0,0,1],roof+cover_screws+tray_screws+['electronics_shelf','electronics_clearance']+[n for n in parts if n.startswith('chassis_brace_screw_')]))
 for x in [-125.5,125.5]:
  for z in [-12,24]:
   removed=[n for n,p in parts.items() if not p['leg'] and p['material'] in ['petg','fabric','envelope']]+[n for n in parts if n.startswith('chassis_bolt_')]
   tools.append(tool(f'Leg cartridge/frame screw {side} {x} {z}',[x,side*109.1,z],[0,side,0],removed))
for y in [-89,89]:
 for z in [-27,27]:
  xx=face_x(y,z)
  tools.append(tool(f'Face screw {y} {z}',[xx+.3,y,z],[1,0,0],[n for n in parts if n.startswith('front_fascia_screw_')]))

# Lower trim and the two nose-return screws are serviced from outside.
for side in [-1,1]:
 for x in [-50,50]:tools.append(tool(f'Battery trim screw {side} {x}',[x,side*99.7,-59],[0,side,0],[n for n in parts if n.startswith('battery_access_screw_')]))
for front in [-1,1]:
 for yy in [-18,18]:
  tools.append(tool(f'End cap to frame screw {front} {yy}',[front*121,yy,46.4],[0,0,1],roof+cover_screws+[n for n in parts if n.startswith('end_cap_screw_')]))
 for side in [-1,1]:
  for dx in [-3,3]:
   tools.append(tool(f'Frame crossmember screw {front} {side} {dx}',[front*121+dx,side*99,36.1],[0,0,1],roof+cover_screws+['body_aft_0','body_nose_surround','front_fascia','sensor_bezel','sensor_window']+[n for n in parts if n.startswith('chassis_tie_bolt_')]))
# Nuts enter the open pockets before batteries, wiring and tray are installed.
nut_cm=trimesh.collision.CollisionManager();nut_cm.add_object('battery_cassette',meshes['battery_cassette']);nut_paths=[]
for name in [n for n in parts if n.startswith('cassette_nut_')]:
 hits=[]
 for dz in np.linspace(20,0,41):
  tf=np.eye(4);tf[2,3]=dz
  if nut_cm.in_collision_single(meshes[name],transform=tf):hits.append(float(dz))
 nut_paths.append({'part':name,'samples':41,'insertion_distance_mm':20,'interference_offsets_mm':hits})

cache={}
def solid(name):
 if name=='electronics_clearance':return box(130,135,32,(0,0,25.5),2)
 key=parts[name]['mesh']
 if key not in cache:cache[key]=cq.importers.importStep(str(out/'step-parts'/f'{key}.step')).val()
 return cache[key]
pairs=[('electronics_shelf','chassis_lower_brace'),('chassis_lower_brace','battery_cassette'),('electronics_shelf','electronics_clearance'),('electronics_shelf','battery_cassette'),('body_aft_0','chassis_crossmember_-121'),('body_nose_surround','chassis_crossmember_121')]
for side in [-1,1]:
 pairs += [('chassis_lower_brace',f'chassis_beam_{side*102}'),('electronics_shelf',f'chassis_beam_{side*102}'),('battery_cassette',f'battery_side_panel_{side}'),('electronics_shelf',f'battery_side_panel_{side}'),('body_center_0',f'chassis_beam_{side*102}')]
fits=[{'parts':[a,b],'overlap_mm3':max(0,solid(a).intersect(solid(b)).Volume()),'minimum_gap_mm':solid(a).distance(solid(b))} for a,b in pairs]
# Cylindrical probes check the independent cassette and deck attachments.
holes=[]
for side in [-1,1]:
 for x in [-52,52]:
  probe=cq.Solid.makeCylinder(1.48,15,cq.Vector(x,side*87,-6),cq.Vector(0,side,0))
  for name in ['battery_cassette',f'chassis_beam_{side*102}']:
   holes.append({'part':name,'side':side,'x_mm':x,'blocked_mm3':max(0,solid(name).intersect(probe).Volume())})
for side in [-1,1]:
 for x in [-52,52]:
  probe=cq.Solid.makeCylinder(1.2,10,cq.Vector(x,side*88,-1),cq.Vector(0,0,1))
  for name in ['electronics_shelf','chassis_lower_brace']:
   holes.append({'part':name,'side':side,'x_mm':x,'blocked_mm3':max(0,solid(name).intersect(probe).Volume())})
# The computer is an envelope, so its exact solid is recreated from the specified box.
from build import box
computer=box(130,135,32,(0,0,25.5),2)
roof_gap=computer.distance(solid('body_center_0'))
assert computer.intersect(solid('body_center_0')).Volume()<1e-4
# Track genuine reductions separately from attachment hardware newly defined here.
old=json.loads((ROOT.parent/'design/iterations/assembly-baseline/model.json').read_text())
counts=lambda data:{'cover_screws':sum(p['name'].startswith('body_service_screw_') for p in data['parts']),
 'separate_battery_guides':sum(p['name'].startswith('battery_rail_') for p in data['parts']),
 'tray_screws':sum(p['name'].startswith('tray_screw_') for p in data['parts']),
 'cassette_screws':sum(p['name'].startswith('cassette_screw_') for p in data['parts']),
 'cassette_nuts':sum(p['name'].startswith('cassette_nut_') for p in data['parts'])}
report={'model_sha256':hashlib.sha256(raw).hexdigest(),'computer_to_roof_gap_mm':roof_gap,'deck_support_gap_mm':solid('electronics_shelf').distance(solid('chassis_lower_brace')),'paths':paths,'tool_access':tools,'attachment_fits':fits,'shared_hole_paths':holes,'nut_insertion':nut_paths,'hardware_counts':{'before':counts(old),'after':counts(model)},'scope':'Nominal rigid CAD. Paths sampled after listed parts/fasteners are removed. A 3 mm diameter tip, 6 mm diameter straight tool shaft and 20 mm diameter handle are tested. Wires, real connectors, hands, flex seals, thread engagement, preload and loaded strength are not qualified.'}
report['passed']=all(p['collision_samples']==0 for p in paths) and all(t['clear'] for t in tools) and all(f['overlap_mm3']<1e-3 for f in fits) and all(h['blocked_mm3']<1e-3 for h in holes) and all(not p['interference_offsets_mm'] for p in nut_paths)
(out/'assembly-audit.json').write_text(json.dumps(report,indent=2))
(out/'assembly-transforms.json').write_text(json.dumps({'model_sha256':report['model_sha256'],'matrices':{n:matrix(p,POSES['stand']).tolist() for n,p in parts.items()},'roof':roof,'sides':sides,'cassette':cassette_group,'cover_screws':cover_screws,'tray_screws':tray_screws,'cassette_screws':cassette_screws},separators=(',',':')))
print(json.dumps({k:report[k] for k in ['passed','hardware_counts']},indent=2))
for p in paths:
 if p['collision_samples']:print('PATH',p['name'],p['first_interferences'])
for t in tools:
 if not t['clear']:print('TOOL',t['name'],t['volumes'])
for f in fits:
 if f['overlap_mm3']>1e-3:print('FIT',f)
for h in holes:
 if h['blocked_mm3']>1e-3:print('HOLE',h)

for p in nut_paths:
 if p['interference_offsets_mm']:print('NUT',p)

assert report["passed"], "Resolve assembly access or removal-path interferences before publishing."
