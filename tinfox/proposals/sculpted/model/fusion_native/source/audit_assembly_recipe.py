"""Independently check native occurrence-frame recipes before assembly authoring.

This tests the proposed transforms, not an actual Fusion occurrence tree.
"""
import json,gzip,sys
from pathlib import Path
import numpy as np
from assembly import transforms
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent));import kinematics
manifest=json.loads((ROOT/'manifests/parts.json').read_text());model=json.loads(gzip.decompress((ROOT/manifest.get('reference_model','snapshots/reference-model.json.gz')).read_bytes()));p=model['parameters'];kinematics.P=p
poses=dict(model['poses']);rng=np.random.default_rng(37)
for index in range(100):poses['sample_'+str(index)]={leg:[float(rng.uniform(-60,60)),float(rng.uniform(-35,77)),float(rng.uniform(-156,-48))] for leg in ['FL','FR','RL','RR']}
errors=[];closures=[]
for label,pose in poses.items():
 local=transforms(p,pose)
 for leg,frames in local.items():
  global_frames={'mount':np.array(frames['mount'])}
  for frame,parent in [('roll','mount'),('thigh','roll'),('knee','thigh'),('crank','thigh'),('rod','thigh')]:global_frames[frame]=global_frames[parent]@np.array(frames[frame])
  for frame in frames:errors.append(float(np.max(np.abs(global_frames[frame]-kinematics.frames(leg,pose[leg])[frame]))))
  phase=np.deg2rad(p['crank_phase_deg']);crank_pin=np.array([p['crank_radius']*np.cos(phase),0,-p['crank_radius']*np.sin(phase),1]);proximal=global_frames['rod'][:3,3];distal=(global_frames['knee']@crank_pin)[:3]
  closures.append(float(abs(np.linalg.norm(distal-proximal)-p['thigh'])))
result={'scope':'Planned native frame recipe compared with independent source kinematics. Actual Fusion instance placement and joints are not yet verified.','pose_count':len(poses),'leg_cases':len(poses)*4,'transform_component_error_max':max(errors),'pushrod_closure_error_max_mm':max(closures),'parameters':{k:p[k] for k in ['thigh','shank_to_foot_center','crank_radius','crank_phase_deg','pitch_offset']},'passed':max(errors)<1e-10 and max(closures)<1e-10,'actual_fusion_assembly_verified':False}
(ROOT/'audits/assembly-recipe.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));assert result['passed']
