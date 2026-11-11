"""Replay the independently checked assembly sequence with native custom exports."""
import json,hashlib,runpy,sys
from pathlib import Path
from motor_complex_exports import COMPONENTS
ROOT=Path(__file__).resolve().parents[1];MODEL=ROOT.parent;PROJECT=MODEL.parents[2];original=PROJECT/'analysis/dfma/motor-complex-fit/release_check.py';out=ROOT/'audits/native-motor-complex-assembly';out.mkdir(exist_ok=True)
paths={k:ROOT/'exports'/(label+'.step')for k,(_,label)in COMPONENTS.items()}
paths.update({f'pod_sleeve_{a}':ROOT/'exports'/f'bench-native-pod_sleeve_{a}.step'for a in [90,210,330]})
assert all(p.exists()for p in paths.values()),[str(p)for p in paths.values()if not p.exists()]
text=original.read_text();text=text.replace("HERE=Path(__file__).resolve().parent",'HERE=Path('+repr(str(out))+')').replace("ROOT=HERE.parents[2]/'proposals/sculpted/model'",'ROOT=Path('+repr(str(MODEL))+')')
a=text.index("  p=Path(args.outer_step)");b=text.index('\n  if not p.exists()',a);text=text[:a]+"  p=NATIVE_PATHS[key]"+text[b:]
text=text.replace("EXPECTED={'thigh_outer':args.outer_sha or '28e49d8e38c3d75233eeea3e8bdd8927e92fb8ebbf60c6e5c39618dc6a996c19',\n          'input_crank':args.crank_sha or 'f207fda710a287a74df9a5a864500737c50de6e25fa377909b8d2995a418b60f'}",'EXPECTED='+repr({k:hashlib.sha256(p.read_bytes()).hexdigest()for k,p in paths.items()}))
text=text.replace('shapes={};hashes={};checks=[]','NATIVE_PATHS={k:Path(v)for k,v in '+repr({k:str(p)for k,p in paths.items()})+'.items()}\nshapes={};hashes={};checks=[]')
text=text.replace('8 mm OD / 4.4 mm ID','8 mm OD / 4.3 mm ID')
copy=out/'checker.py';copy.write_text(text);sys.argv=[str(copy)];runpy.run_path(str(copy),run_name='__main__');report=json.loads((out/'release-report.json').read_text());report.update(original_checker_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),native_checker_sha256=hashlib.sha256(copy.read_bytes()).hexdigest(),native_scope='Every custom part used by this independent staged-assembly checker is replaced by its native export. Additional paired-race axial checks are separate.',native_input_paths={k:str(p.relative_to(ROOT))for k,p in paths.items()},source_of_truth_promoted=False);(out/'release-report.json').write_text(json.dumps(report,indent=2)+'\n')
