"""Preserve an immutable, hashed prototype reference for native comparison."""
import gzip,hashlib,json,shutil
from kinematics import ROOT
OUT=ROOT/'output/paired-roll-work';raw=(OUT/'model.json').read_bytes()
stamp=hashlib.sha256(raw).hexdigest();snap=ROOT/'fusion_native/snapshots/paired-bearing-target'/stamp
if snap.exists():
    raise RuntimeError('Snapshot already exists; verify it instead of overwriting archived evidence: '+str(snap))
snap.mkdir(parents=True);(snap/'step').mkdir();(snap/'source').mkdir()
with gzip.open(snap/'model.json.gz','wb') as f:f.write(raw)
parts={}
for p in json.loads(raw)['parts']:
    if not p['leg']:continue
    key=p['mesh'];file=OUT/'step'/(key+'.step')
    if key in parts or not file.exists():continue
    shutil.copy2(file,snap/'step'/file.name);parts[key]=hashlib.sha256(file.read_bytes()).hexdigest()
sources={}
for name in ['paired_roll.py','standard_knee.py','build_paired_roll.py','update_paired_cup.py','kinematics.py']:
    file=ROOT/name;shutil.copy2(file,snap/'source'/name);sources[name]=hashlib.sha256(file.read_bytes()).hexdigest()
(snap/'manifest.json').write_text(json.dumps(dict(model_sha256=stamp,parts=parts,sources=sources,
    scope='Immutable generated prototype reference. Native conversion and whole-robot integration remain unqualified.'),indent=2))
print(json.dumps(dict(model_sha256=stamp,snapshot=str(snap),parts=len(parts))),flush=True)
