"""Compare current native shell and linkage substitutions through the frozen front-leg knee sweep."""
import gzip,hashlib,json,sys
from pathlib import Path
import cadquery as cq
import trimesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent));import kinematics as k
raw=gzip.decompress((ROOT/'snapshots/cohesive-limb/model.json.gz').read_bytes());data=json.loads(raw);k.P.update(data['parameters']);parts={p['name']:p for p in data['parts'] if p.get('leg')=='FL' and p['group'] in ['thigh','knee','rod','crank'] and p.get('service_role') not in ['keepout','withdrawal']};meshes={key:trimesh.Trimesh(vertices=v['vertices'],faces=v['faces'],process=False) for key,v in data['meshes'].items()};replacements={};refs={}
for kind in ['shin','thigh']:
 for side in ['inner','outer']:
  path=ROOT/'exports'/f'cohesive-{kind}-{side}-final.step';assert path.exists();shape=cq.importers.importStep(str(path)).val();v,f=shape.tessellate(.02,.04);replacements['FL_'+kind+'_'+side]=trimesh.Trimesh(vertices=[p.toTuple() for p in v],faces=f,process=False);refs[kind+'_'+side]=hashlib.sha256(path.read_bytes()).hexdigest()
for key in ['input_crank','knee_inner_spacer','pushrod','sleeve_0','sleeve_1','knee_axle','foot']:
 path=ROOT/'exports'/('cohesive-'+key.replace('_','-')+'.step');shape=cq.importers.importStep(str(path)).val();v,f=shape.tessellate(.02,.04);replacements['FL_'+key]=trimesh.Trimesh(vertices=[p.toTuple() for p in v],faces=f,process=False);refs[key]=hashlib.sha256(path.read_bytes()).hexdigest()
known=[{'knee_motor','input_crank'}]+[{x,y} for x in ['knee_axle','knee_inner_spacer'] for y in ['bearing_inner','bearing_outer']];managers={}
for native in [False,True]:
 m=trimesh.collision.CollisionManager()
 for name,p in parts.items():m.add_object(name,replacements[name] if native and name in replacements else meshes[p['mesh']])
 managers[native]=m
rows=[]
for knee in range(-156,-47):
 pose=k.uniform([0,30,knee]);hits={}
 for native,m in managers.items():
  for name,p in parts.items():m.set_transform(name,k.matrix(p,pose))
  _,pairs=m.in_collision_internal(return_names=True);filtered=[]
  for a,b in pairs:
   if parts[a]['group']==parts[b]['group'] or {a.split('_',1)[1],b.split('_',1)[1]} in known:continue
   filtered.append(tuple(sorted([a,b])))
  hits['native' if native else 'source']=set(filtered)
 rows.append({'knee_deg':knee,'source_hits':sorted(hits['source']),'native_hits':sorted(hits['native']),'added_hits':sorted(hits['native']-hits['source'])})
record={'source_model_sha256':hashlib.sha256(raw).hexdigest(),'native_step_sha256':refs,'knee_samples':rows,'passed':all(not r['added_hits'] for r in rows),'native_clear_samples':sum(not r['native_hits'] for r in rows),'scope':'109 one-degree front-leg knee samples, hip 30 degrees and roll zero. All modeled hardware retained; same rigid-group contacts and explicit shaft/bearing mating pairs are checked separately. Not a full body range or continuous swept-volume proof.'};(ROOT/'audits/cohesive-native-leg-motion.json').write_text(json.dumps(record,indent=2));print(json.dumps({'passed':record['passed'],'samples':len(rows),'native_clear_samples':record['native_clear_samples'],'added':[r for r in rows if r['added_hits']]}))
