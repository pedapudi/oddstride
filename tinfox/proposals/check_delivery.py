"""Cross-check proposal exports, contact heights and archive contents."""
import hashlib,importlib.util,json,zipfile
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
report={}
body_baselines=json.loads((ROOT/'body-baseline-meshes.json').read_text())
motion_baselines=json.loads((ROOT/'body-baseline-motion.json').read_text())
def sampled_angles(record,step):
 return {round(float(q),6) for low,high in record['clear_intervals_deg'] for q in np.arange(low,high+step*.5,step)}
for label in ['compact','sculpted']:
 root=ROOT/label/'model';raw=(root/'output/model.json').read_bytes();m=json.loads(raw);stamp=hashlib.sha256(raw).hexdigest()
 baseline=body_baselines[label]
 keys={p['mesh'] for p in m['parts'] if p.get('leg')}
 fingerprints={k:hashlib.sha256(json.dumps(m['meshes'][k],sort_keys=True).encode()).hexdigest() for k in sorted(keys)}
 if label=='compact':assert fingerprints==baseline['meshes'],(label,'body revision changed a limb mesh')
 else:
  refinement=json.loads((root/'output/refinement-checks.json').read_text())
  assert refinement['model_sha256']==stamp and refinement['joint_parameters_unchanged']
  baseline={'model_sha256':refinement['baseline_model_sha256'],'meshes':baseline['meshes']}
 body=json.loads((root/'output/body-revision-comparison.json').read_text())
 assert body['baseline_model_sha256']==baseline['model_sha256'],(label,'body baseline mismatch')
 assert body['model_sha256']==stamp,(label,'stale body report')
 spec=importlib.util.spec_from_file_location('delivery_'+label,root/'kinematics.py');kin=importlib.util.module_from_spec(spec);spec.loader.exec_module(kin)
 eng=json.loads((root/'output/engineering.json').read_text());assert eng['model_sha256']==stamp
 old_motion=motion_baselines[label]['motion'];new_motion=eng['motion']
 step=old_motion['step_deg'];assert new_motion['step_deg']==step
 for leg,axes in old_motion['joint_sweeps'].items():
  for axis,state in axes.items():
   lost=sampled_angles(state,step)-sampled_angles(new_motion['joint_sweeps'][leg][axis],step)
   assert not lost,(label,leg,axis,'lost previously clear sampled angles',sorted(lost))
 for leg,state in old_motion['folded_hip_sweeps'].items():
  lost=sampled_angles(state,step)-sampled_angles(new_motion['folded_hip_sweeps'][leg],step)
  assert not lost,(label,leg,'folded hip regression',sorted(lost))
 catalog=json.loads((root/'output/parts-catalog.json').read_text());assert catalog['model_sha256']==stamp
 contact=[]
 for leg in kin.LEGS:
  foot=next(p for p in m['parts'] if p['name']==leg+'_foot');vertices=np.array(m['meshes'][foot['mesh']]['vertices'])
  for case in eng['torque_cases']:
   poses={l:list(q) for l,q in m['poses']['stand'].items()};poses[leg]=case['q_deg']
   actual=(np.c_[vertices,np.ones(len(vertices))]@kin.matrix(foot,poses).T)[:,2].min()
   expected=kin.contacts(leg,case['q_deg'])[0][2]
   delta=float(actual-expected)
   assert -.4<=delta<=.4,(label,leg,case['case'],'contact mismatch mm',delta)
   contact.append({'leg':leg,'case':case['case'],'support_height_error_mm':delta})
 with zipfile.ZipFile(root/'output/tinfox-individual-cad.zip') as z:
  assert json.loads(z.read('parts-catalog.json'))['model_sha256']==stamp
  for p in catalog['parts']:
   assert hashlib.sha256(z.read(p['step'])).hexdigest()==p['step_sha256'],(label,p['id'])
   assert (root/'output'/p['step']).is_file()
 for name in ['studio-provenance','studio-view-provenance','mounting-fit','mounting-audit']:
  assert json.loads((root/'output'/f'{name}.json').read_text())['model_sha256']==stamp,(label,name)
 report[label]={'model_sha256':stamp,'body_baseline_model_sha256':baseline['model_sha256'],'unchanged_limb_meshes':sum(value==baseline['meshes'].get(key) for key,value in fingerprints.items()),'sampled_joint_intervals_preserved':True,'individual_step_count':len(catalog['parts']),'foot_contact_cases':contact,'scope':'Checks final export identity, declared limb geometry changes and preserved sampled joint intervals during refinement, and support heights on all legs in the prescribed torque poses. Does not validate deformable soles, gait control or loads.'}
(ROOT/'delivery-checks.json').write_text(json.dumps(report,indent=2))
print('Both proposal archives and render hashes match; modeled foot support heights agree with the torque geometry.')
