"""Build qualified handed parts serially while independent local audits overlap."""
import json,subprocess,concurrent.futures
from pathlib import Path
from mirror_part import mirror,source_for
ROOT=Path(__file__).resolve().parents[1];PYTHON=ROOT.parents[3]/'.venv/bin/python'
manifest=json.loads((ROOT/'manifests/parts.json').read_text());keys=[p['id'] for p in manifest['parts']]
pending=[k for k in keys if source_for(k) and not (ROOT/'exports'/f'{k}.step').exists()]
pending.sort(key=lambda k:(k.endswith('_right'),k));futures={};failed={};deferred=[]
def audit(key):
 for filename in ['audit_part.py','audit_sections.py']:
  r=subprocess.run([str(PYTHON),str(ROOT/'source'/filename),key],capture_output=True,text=True)
  print(r.stdout or r.stderr,flush=True)
  if r.returncode:return False
 return True
def qualified(key):
 for suffix,gate in [('geometry','geometric_gate_passed'),('sections','section_gate_passed')]:
  path=ROOT/'audits'/f'{key}-{suffix}.json'
  if not path.exists() or not json.loads(path.read_text())[gate]:return False
 return True
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for key in pending:
  source,_=source_for(key)
  if source in futures:futures[source].result()
  if not qualified(source):deferred.append(key);continue
  print('Native handed part',key,flush=True)
  if mirror(key):futures[key]=pool.submit(audit,key)
  else:failed[key]='Native mirror construction failed; see RPC evidence.'
 for key,job in futures.items():
  if not job.result():failed[key]='Local audit execution failed.'
(ROOT/'manifests/mirror-batch.json').write_text(json.dumps({'built':list(futures),'deferred':deferred,'failed':failed,'migration_gate_passed':False},indent=2))
print('Finished',len(futures),'deferred',deferred,'failed',failed,flush=True)
