"""Check bearing extraction, assembly gaps and connector packaging at sampled poses."""
import json,math,hashlib
import numpy as np
import cadquery as cq
import trimesh
import service_design as sd
from kinematics import ROOT, POSES, matrix, uniform, frames, point, LEGS, P
out=sd.OUT;data=json.loads((out/'model.json').read_text());stamp=hashlib.sha256((out/'model.json').read_bytes()).hexdigest()
parts={p['name']:p for p in data['parts']};cache={}
def solid(k):
 if k not in cache:
  p=out/'step'/f'{k}.step'
  if not p.exists():p=ROOT/'output/step-parts'/f'{k}.step'
  cache[k]=cq.importers.importStep(str(p)).val()
 return cache[k]
fits=[];paths=[]
def path(name,s,obstacles,axis):
 samples=[]
 for d in [0,.1,.5,1,2,4,8,12,20,35]:
  overlap=sum(max(0,s.translate(tuple(d*v for v in axis)).intersect(q).Volume()) for q in obstacles)
  samples.append({'distance_mm':d,'overlap_mm3':overlap})
 passed=all(q['overlap_mm3']<1e-4 for q in samples)
 paths.append({'name':name,'axis':axis,'samples':samples,'passed':passed});assert passed,(name,samples)
inner,outer=[solid(k) for k in ['shin_inner','shin_outer']]
for label,s,direction,bearingkey in [('inner',inner,-1,'bearing_inner'),('outer',outer,1,'bearing_outer')]:
 bearing=solid(bearingkey)
 probe=sd.ring(14.8,14.2,1,77.5 if label=='outer' else 57.5)
 coverage=s.intersect(probe).Volume()/probe.Volume();assert coverage>.999,(label,'complete seat',coverage)
 fits.append({'name':label+' continuous circular seat','wall_coverage_fraction':coverage})
 path(label+' bearing exits outward after splitting shin',bearing,[s],(0,direction,0))
 # Rear access runs behind the outer race; both 2 mm pins clear the 2.6 mm holes.
 for xx in [-12.7,12.7]:
  pin=sd.cyl(1,3,(xx,71 if label=='outer' else 62,0))
  overlap=max(0,pin.intersect(s).Volume());assert overlap<1e-4,(label,'tool',xx,overlap)
  fits.append({'name':label+' extraction pin '+str(xx),'overlap_mm3':overlap,'radial_tool_clearance_mm':.3})
 path(label+' shin half opens laterally',s,[outer if label=='inner' else inner],(0,direction,0))
 for kind in ['bolt','nut','sleeve']:
  for tag in ['37','105']:
   q=solid('shin_clamp_'+kind+'_'+tag);v=max(0,q.intersect(s).Volume())
   fits.append({'name':label+' with '+kind+' '+tag,'overlap_mm3':v});assert v<1e-4,(label,kind,tag,v)
# Transform thigh into knee-local coordinates at zero knee for concentric seat checks.
for label in ['inner','outer']:
 t=solid('thigh_'+label).translate((0,0,170));bearing=solid('bearing_'+label)
 gap=t.distance(bearing);assert gap>.25,(label,'axial stop gap',gap)
 retained=max(0,t.intersect(bearing.translate((0,.5 if label=='outer' else -.5,0))).Volume());assert retained>1,(label,'retention',retained)
 fits.append({'name':label+' bearing to thigh backup stop','distance_mm':gap,'retention_overlap_at_half_mm_displacement_mm3':retained})
 v=max(0,t.intersect(inner.fuse(outer)).Volume());assert v<1e-4,(label,'retainer shin',v)
# Sample dynamic collision using triangle meshes. Connector-to-connector contacts
# within one mating set are intentional. No other same-group exemptions apply.
meshes={k:trimesh.Trimesh(vertices=v['vertices'],faces=v['faces'],process=False) for k,v in data['meshes'].items()}
manager=trimesh.collision.CollisionManager();checked={}
for n,p in parts.items():
 if p.get('service_role') in ['keepout','withdrawal']:continue
 if not p['check'] and not p.get('service_role'):continue
 manager.add_object(n,meshes[p['mesh']]);checked[n]=p
changed={'shin_inner','shin_outer','thigh_inner','thigh_outer'}
def focus(p):return p['name'] in ['body_nose_surround','body_aft_0'] or bool(p.get('service_role')) or p['name'].split('_',1)[-1] in changed
results=[]
poses={**POSES}
for r in [-45,0,45]:
 for h in [0,30,65]:
  for k in [-140,-90,-60]:poses[f'sample_{r}_{h}_{k}']=uniform([r,h,k])
for name,q in poses.items():
 for n,p in checked.items():manager.set_transform(n,matrix(p,q))
 _,pairs=manager.in_collision_internal(return_names=True)
 hits=[]
 for a,b in pairs:
  p,t=checked[a],checked[b]
  if not(focus(p) or focus(t)):continue
  if '_port_' in a and '_port_' in b and a.rsplit('_',1)[0]==b.rsplit('_',1)[0]:continue
  if p['leg']==t['leg']:
   ends={a.split('_',1)[-1],b.split('_',1)[-1]}
   # Exact nominal axle/bearing and pin interfaces are checked separately.
   if not(p.get('service_role') or t.get('service_role')):
    if p['group']==t['group']:continue
    if any(n in ends for n in ['knee_axle','knee_inner_spacer','output_pin','input_pin']):continue
    if any('rod_bush_' in n for n in ends):continue
  hits.append(sorted([a,b]))
 results.append({'pose':name,'angles':q,'hits':sorted(hits),'passed':not hits})
 print(name,len(hits),flush=True)
# Plug and boot pull outward with exterior body covers removed and the robot
# parked in neutral. This is a geometric path, not a hand-access certification.
obstacles=trimesh.collision.CollisionManager()
for n,p in checked.items():
 if p.get('service_role') or n.startswith(('body_','belly_','front_fascia','sensor_')):continue
 obstacles.add_object(n,meshes[p['mesh']],transform=matrix(p,POSES['stand']))
withdrawals=[]
for entry in json.loads((out/'parts.json').read_text())['connectors']:
 prefix=entry['prefix'];family=entry['motor'].split('_')[1];front=1 if entry['leg'][0]=='F' else -1;side=1 if entry['leg'][1]=='L' else -1
 _,_,_,r=sd.port_frame(54.4 if family=='knee' else 0,entry['sign'])
 if family=='roll':r=np.array([r[1],-r[0],r[2]]);r[0]*=front
 r[1]*=side
 conflicts=set()
 for suffix in ['plug','boot']:
  p=parts[prefix+'_'+suffix];base=matrix(p,POSES['stand'])
  for distance in [0,1,3,6,10,15,20,25]:
   move=np.eye(4);move[:3,3]=r*distance
   _,names=obstacles.in_collision_single(meshes[p['mesh']],transform=base@move,return_names=True)
   conflicts.update(names)
 withdrawals.append({'port':prefix,'sampled_travel_mm':25,'passed':not conflicts,'obstacles':sorted(conflicts)})
linkage=[]
for pose,q in poses.items():
 for leg,(_,side) in LEGS.items():
  f=frames(leg,q[leg]);yy=side*70;phase=math.radians(P['crank_phase_deg'])
  upper=point(f['crank'],[22,yy,0]);lower=point(f['knee'],[22*math.cos(phase),yy,-22*math.sin(phase)])
  rod_upper=point(f['rod'],[0,yy,0]);rod_lower=point(f['rod'],[0,yy,-170])
  errors=[float(np.linalg.norm(upper-rod_upper)),float(np.linalg.norm(lower-rod_lower))]
  assert max(errors)<1e-8,(pose,leg,errors)
  linkage.append({'pose':pose,'leg':leg,'eye_pin_error_mm':errors,'eye_spacing_mm':float(np.linalg.norm(upper-lower))})
report={'model_sha256':stamp,'linkage_closure':linkage,'paths':paths,'fits':fits,'connector_withdrawal':withdrawals,'motion_samples':results,'passed_service_paths':all(p['passed'] for p in paths),'connector_motion_clear':all(p['passed'] for p in results),'scope':'Nominal exact-solid bearing removal and static fit checks; sampled rigid meshes for connectors, initial cable segments and revised limbs. Cable deformation, continuous trajectory clearance, fatigue, actual insertion depth and physical bearing fits are not qualified.'}
(out/'audit.json').write_text(json.dumps(report,indent=2));print('AUDIT WRITTEN',flush=True)
