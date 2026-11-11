"""Build a review manifest from the final, independently checked CAD proposals."""
import hashlib,importlib.util,json,zipfile
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent

def collect(path,label):
 modelroot=path/'model' if label!='baseline' else path
 raw=(modelroot/'output/model.json').read_bytes();model=json.loads(raw)
 stamp=hashlib.sha256(raw).hexdigest();r=json.loads((modelroot/'output/engineering.json').read_text())
 assert r['model_sha256']==stamp,(label,'stale engineering')
 spec=importlib.util.spec_from_file_location('review_'+label,modelroot/'kinematics.py');kin=importlib.util.module_from_spec(spec);spec.loader.exec_module(kin)
 vertices=[];enclosure=[]
 for p in model['parts']:
  if not p.get('leg') and p['material'] not in ['envelope','fabric']:
   enclosure.extend(model['meshes'][p['mesh']]['vertices'])
  if p['name'].endswith('_hip_disc') or (label=='sculpted' and p['name'].endswith('_thigh_outer')):
   v=np.array(model['meshes'][p['mesh']]['vertices']);world=np.c_[v,np.ones(len(v))]@kin.matrix(p,model['poses']['stand']).T;vertices.extend(world[:,1])
 presets=r['motion']['presets'];assert all(not v['collision'] for v in presets.values()),label
 assert min(v['minimum_distance_mm'] for v in presets.values())>=model['parameters']['clearance_screen_mm'],label
 assert all(v['collision_samples']==0 for v in r['motion']['transitions'].values()),label
 assert r['battery_fit']['intersections']==[] and r['fixed_packaging']['intersections']==[],label
 assert r['printability']['all_fit'],label
 enclosure=np.array(enclosure);extent=np.ptp(enclosure,axis=0)
 stats={'model_sha256':stamp,'body_length_mm':float(extent[0]),'body_width_mm':float(extent[1]),'core_body_length_mm':model['parameters']['body_length'],'cap_span_mm':float(max(vertices)-min(vertices)),'roll_axis_span_mm':2*model['parameters']['roll_y'],'foot_diameter_mm':2*model['parameters']['foot_radius'],'base_mass_kg':r['mass']['base_kg'],'preset_count':len(presets),'minimum_preset_gap_mm':min(v['minimum_distance_mm'] for v in presets.values()),'transition_collision_samples':sum(v['collision_samples'] for v in r['motion']['transitions'].values()),'step_part_count':len(list((modelroot/'output/step-parts').glob('*.step'))),'print_envelopes_fit':r['printability']['all_fit']}
 if label!='baseline':
  for name in ['mounting-fit','mounting-audit','parts-catalog','studio-provenance','studio-view-provenance']:
   assert json.loads((modelroot/'output'/f'{name}.json').read_text())['model_sha256']==stamp,(label,name)
  body=json.loads((modelroot/'output/body-revision-comparison.json').read_text())
  assert body['model_sha256']==stamp,(label,'body revision identity')
  if label=='compact':assert body['limb_meshes_unchanged']
  else:
   refinement=json.loads((modelroot/'output/refinement-checks.json').read_text())
   assert refinement['model_sha256']==stamp and refinement['previous_sampled_motion_preserved'] and refinement['joint_parameters_unchanged']
  assert json.loads((modelroot/'output/body-detail-provenance.json').read_text())['model_sha256']==stamp,(label,'stale nose detail')
  view=json.loads((modelroot/'output/studio-view-provenance.json').read_text())
  camera=view['camera'];camera=camera if isinstance(camera,dict) else {'position':camera,'target':view['target'],'ortho_scale':view['ortho_scale']}
  np.testing.assert_allclose(camera['position'],[.55,-1.5,.25],atol=1e-6)
  np.testing.assert_allclose(camera['target'],[0,0,-.105],atol=1e-6)
  assert abs(camera['ortho_scale']-.78)<1e-6
  pose=view['pose'];pose=model['poses'][pose] if isinstance(pose,str) else pose
  for q in pose.values():np.testing.assert_allclose(q,[0,45,-75],atol=1e-6)
 return stats

if __name__=='__main__':
 notes=json.loads((ROOT/'review-notes.json').read_text())
 records={key:collect(ROOT/key,key) for key in ['compact','sculpted']}
 records['baseline']=collect(ROOT.parent/'model','baseline')
 data={'reference':'../design/06-tinfox-instrument-concept.png','reference_sha256':hashlib.sha256((ROOT.parent/'design/06-tinfox-instrument-concept.png').read_bytes()).hexdigest(),'stats':records,'proposals':notes,'metrics':[]}
 limb={}
 for key,name in [('compact','limb-profile-comparison.json'),('sculpted','limb-revision-comparison.json')]:
  result=json.loads((ROOT/key/'model/output'/name).read_text())
  assert result['model_sha256']==records[key]['model_sha256'],(key,'stale limb comparison')
  limb[key]=result['comparison_summary']
 data['limb_metrics']=[]
 for title,key,unit in [('Moving leg mass change','moving_leg_mass_delta_g','g'),('Hip-pitch inertia change in standing pose','hip_pitch_inertia_change_percent','%'),('Knee-axis inertia change','knee_pitch_inertia_change_percent','%'),('Minimum sampled thigh section modulus change','thigh_section_modulus_change_percent','%'),('Minimum sampled shin section modulus change','shin_section_modulus_change_percent','%')]:
  data['limb_metrics'].append([title,*[f'{limb[p][key]:+.1f} {unit}' for p in ['compact','sculpted']]])
 data['limb_metrics'].append(['Folded thigh-to-shin gap, previous → current',*[f"{limb[p]['fold_min_thigh_shin_gap_mm_before']:.2f} → {limb[p]['fold_min_thigh_shin_gap_mm_after']:.2f} mm" for p in ['compact','sculpted']]])
 rows=[('Rigid body length, including nose','body_length_mm','mm'),('Rigid body width','body_width_mm','mm'),('Span across motor caps','cap_span_mm','mm'),('Hip roll axis spacing','roll_axis_span_mm','mm'),('Rounded sole diameter','foot_diameter_mm','mm'),('Estimated base mass','base_mass_kg','kg'),('Individual STEP files','step_part_count',''),('Presets checked','preset_count',''),('Minimum tested preset gap','minimum_preset_gap_mm','mm'),('Intersecting transition samples','transition_collision_samples','')]
 for title,key,unit in rows:
  values=[]
  for p in ['baseline','compact','sculpted']:
   v=records[p][key];digits=2 if unit=='kg' or key=='minimum_preset_gap_mm' else 1
   values.append(f'{v:.{digits}f} {unit}'.strip() if unit else str(v))
  data['metrics'].append([title,*values])
 data['metrics'].append(['Printed part envelopes fit H2D',*['Yes' if records[p]['print_envelopes_fit'] else 'No' for p in ['baseline','compact','sculpted']]])
 (ROOT/'comparison.json').write_text(json.dumps(data,indent=2))
 print(json.dumps(records,indent=2))
 archive=ROOT/'tinfox-two-proposals.zip'
 with zipfile.ZipFile(archive.with_suffix('.zip.tmp'),'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for key in ['compact','sculpted']:
   root=ROOT/key/'model'
   comparison_name='limb-profile-comparison.json' if key=='compact' else 'limb-revision-comparison.json'
   for name in ['tinfox-assembly.step','tinfox-individual-cad.zip','engineering.json','parts-catalog.json','torques.csv',comparison_name,'body-revision-comparison.json','body-detail-provenance.json']:
    z.write(root/'output'/name,f'{key}/model/output/{name}')
   z.write(root/'README.md',f'{key}/model/README.md')
   for source in sorted(root.glob('*.py'))+ [root/'parameters.json',root/'requirements.txt']:
    z.write(source,f'{key}/model/{source.name}')
   z.write(ROOT/key/'design/12-studio-view.png',f'{key}/design/12-studio-view.png')
   z.write(ROOT/key/'design/15-body-detail.png',f'{key}/design/15-body-detail.png')
   if key=='sculpted':
    for name in ['integration-audit.json','refinement-checks.json','manufacturing-plan.json','tinfox-manufacturing-kit.zip','assembly-audit.json','assembly-guide.txt','hardware-research.json','hardware-shortlist.csv','limb-assembly-audit.json','limb-hardware-guide.txt']:
     z.write(root/'output'/name,f'{key}/model/output/{name}')
    z.write(ROOT/key/'design/17-face-curvature.svg',f'{key}/design/17-face-curvature.svg')
   for name in ['13-shin-profile.svg','14-limb-profile.svg']:
    profile=ROOT/key/'design'/name
    if profile.exists():z.write(profile,f'{key}/design/{name}')
  for name in ['comparison.json','review-notes.json','delivery-checks.json','body-baseline-meshes.json','body-baseline-motion.json','README.md']:
   z.write(ROOT/name,name)
 archive.with_suffix('.zip.tmp').replace(archive)
 print('Wrote comparison manifest and both-proposal CAD archive.')
