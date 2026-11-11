"""Run the frozen mechanical interface audit with native shell substitutions."""
import gzip,hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];MODEL=ROOT.parent;FROZEN=ROOT/'snapshots/cohesive-limb';WORK=ROOT/'audits/cohesive-leg-fit-input';WORK.mkdir(exist_ok=True);(WORK/'step').mkdir(exist_ok=True)
(WORK/'model.json').write_bytes(gzip.decompress((FROZEN/'model.json.gz').read_bytes()))
# Freeze the remaining unchanged hardware once, independently of moving body work.
keys=['hip_hub','motor_mount_ring','pod_sleeve_90','pod_sleeve_210','pod_sleeve_330','pod_tie_90','pod_tie_210','pod_tie_330','sleeve_0','sleeve_1','bolt_0','bolt_1','thigh_clamp_nut_0','knee_axle','axle_bolt','axle_nut','knee_inner_spacer','bearing_inner','bearing_outer','shin_clamp_bolt_37','shin_clamp_bolt_105','shin_clamp_nut_37','shin_clamp_nut_105','shin_clamp_sleeve_37','shin_clamp_sleeve_105','output_pin','output_pivot_nut','motor_carrier_1','motor_carrier_-1']
(FROZEN/'hardware').mkdir(exist_ok=True);refs=[]
for key in keys:
 dest=FROZEN/'hardware'/f'{key}.step'
 if not dest.exists():
  choices=[FROZEN/'step'/f'{key}.step']+[MODEL/'output'/f/'step'/f'{key}.step' for f in ['low-lidar-reference','integrated-candidate','v0-rounded-body','service-design']]+[MODEL/'output/step-parts'/f'{key}.step'];source=next(p for p in choices if p.exists());shutil.copyfile(source,dest)
 shutil.copyfile(dest,WORK/'step'/dest.name);refs.append({'part':key,'source':'unchanged frozen hardware/reference','sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
for kind in ['shin','thigh']:
 for side in ['inner','outer']:
  label=f'cohesive-{kind}-{side}';path=ROOT/'exports'/f'{label}-final.step'
  if not path.exists():path=ROOT/'exports'/f'{label}.step'
  shutil.copyfile(path,WORK/'step'/f'{kind}_{side}.step');refs.append({'part':f'{kind}_{side}','source':'native Fusion shell','export':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
for key in ['input_crank','motor_carrier_1','motor_carrier_-1','knee_inner_spacer','pushrod','sleeve_0','sleeve_1','knee_axle','foot']:
 path=ROOT/'exports'/('cohesive-'+key.replace('_','-')+'.step')
 assert path.exists(),path
 shutil.copyfile(path,WORK/'step'/f'{key}.step');refs=[r for r in refs if r['part']!=key];refs.append({'part':key,'source':'native Fusion assembly-driven part','export':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(WORK/'input-manifest.json').write_text(json.dumps({'source_model_sha256':hashlib.sha256((WORK/'model.json').read_bytes()).hexdigest(),'inputs':refs,'scope':'Four native manufacturing shells plus current crank, carriers, linkage, spacers, axle and foot; remaining hardware references frozen.'},indent=2))
subprocess.run([sys.executable,str(FROZEN/'source/audit_cohesive_limb.py'),str(WORK)],check=True,cwd=MODEL,env=__import__('os').environ|{'PYTHONPATH':str(MODEL)})
report=json.loads((WORK/'limb-interfaces.json').read_text());report['native_input_manifest']='audits/cohesive-leg-fit-input/input-manifest.json';report['scope']='Native structural shells, current motor carriers, crank, pushrod, compression sleeves, bearing spacer, axle and foot; remaining hardware frozen. '+report['scope'];(ROOT/'audits/cohesive-native-leg-interfaces.json').write_text(json.dumps(report,indent=2))
