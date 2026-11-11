"""Identify body interference at the reported joint combinations."""
import hashlib,importlib.util,json,sys
from pathlib import Path
from kinematics import ROOT,P,uniform
viewer=ROOT.parents[2]/'viewer/serve.py'
spec=importlib.util.spec_from_file_location('review_server',viewer);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
folder=sys.argv[1] if len(sys.argv)>1 else 'raised-head-prototype'
p=ROOT/'output'/folder/'model.json';engine=module.Engine(p);P.update(engine.data['parameters'])
parts=engine.parts

def body_hits(q):
 result=engine.check(uniform(q));return [pair for pair in result['pairs'] if bool(parts[pair[0]].get('leg'))!=bool(parts[pair[1]].get('leg'))]
reported=[]
for roll in [-60,-30,0,30,60]:
 for pitch in [-60,90]:reported.append({'angles_deg':[roll,pitch,-60],'body_hits':body_hits([roll,pitch,-60])})
intervals=[]
for roll in [-60,-30,0,30,60]:
 runs=[];start=None;previous=None
 for pitch in range(-90,111,5):
  clear=not body_hits([roll,pitch,-60])
  if clear and start is None:start=pitch
  if not clear and start is not None:runs.append([start,previous]);start=None
  previous=pitch
 if start is not None:runs.append([start,previous])
 intervals.append({'hip_roll_deg':roll,'knee_pitch_deg':-60,'clear_sample_intervals_deg':runs})
report={'model_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'reported_poses':reported,'pitch_sweep':intervals,'scope':'All four legs commanded to the listed angles. Body interference only; unrelated leg-to-leg and internal leg interfaces are excluded from this report. Clear samples are not a continuous operating envelope, strength rating or balance guarantee. No limits are installed on real hardware.'}
(ROOT/'output'/folder/'chassis-limits.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
