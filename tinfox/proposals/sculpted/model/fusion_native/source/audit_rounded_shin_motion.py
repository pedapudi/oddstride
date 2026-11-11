"""Check the current shin against all retained moving knee hardware."""
import gzip,hashlib,json,sys
from pathlib import Path
import cadquery as cq
import trimesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent));import kinematics as k
target=json.loads((ROOT/'manifests/latest-shell-target.json').read_text());source_hash=target['source_model_sha256'];raw=gzip.decompress((ROOT/'snapshots/latest-leg'/source_hash/'model.json.gz').read_bytes());assert hashlib.sha256(raw).hexdigest()==source_hash;data=json.loads(raw);k.P.update(data['parameters'])
parts={p['name']:p for p in data['parts']if p.get('leg')=='FL'and p['group']in['thigh','knee','rod','crank']and p.get('service_role')not in['keepout','withdrawal']}
meshes={key:trimesh.Trimesh(vertices=v['vertices'],faces=v['faces'],process=False)for key,v in data['meshes'].items()};replacements={};refs={}
for half in ['inner','outer']:
 path=ROOT/'exports'/('rounded-native-shin_'+half+'.step');shape=cq.importers.importStep(str(path)).val();assert shape.isValid()and len(shape.Solids())==1;v,f=shape.tessellate(.02,.04);replacements['FL_shin_'+half]=trimesh.Trimesh(vertices=[p.toTuple()for p in v],faces=f,process=False);refs[half]=hashlib.sha256(path.read_bytes()).hexdigest()
known=[{'knee_motor','input_crank'}]+[{x,y}for x in['knee_axle','knee_inner_spacer']for y in['bearing_inner','bearing_outer']];managers={}
for native in[False,True]:
 m=trimesh.collision.CollisionManager()
 for name,p in parts.items():m.add_object(name,replacements[name]if native and name in replacements else meshes[p['mesh']])
 managers[native]=m
rows=[]
for knee in range(-156,-47):
 pose=k.uniform([0,30,knee]);hits={}
 for native,m in managers.items():
  for name,p in parts.items():m.set_transform(name,k.matrix(p,pose))
  _,pairs=m.in_collision_internal(return_names=True);filtered=[]
  for a,b in pairs:
   if parts[a]['group']==parts[b]['group']or{a.split('_',1)[1],b.split('_',1)[1]}in known:continue
   filtered.append(tuple(sorted([a,b])))
  hits[native]=set(filtered)
 rows.append({'knee_deg':knee,'source_hits':sorted(hits[False]),'native_hits':sorted(hits[True]),'added_hits':sorted(hits[True]-hits[False])})
record={'source_model_sha256':source_hash,'native_step_sha256':refs,'knee_samples':rows,'passed':all(not r['added_hits']for r in rows),'native_clear_samples':sum(not r['native_hits']for r in rows),'scope':'109 one-degree knee positions, hip30/roll0, current washer/shoulder screw hardware retained. Rigid-group and named bearing mates excluded. Sampled motion, not strength or a continuous sweep.'}
(ROOT/'audits/rounded-shin-motion.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'clear':record['native_clear_samples'],'added':[r for r in rows if r['added_hits']]})
