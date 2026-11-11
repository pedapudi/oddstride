"""Measure actual axial material near the three pod ties; no CAD mutation."""
from pathlib import Path
import hashlib,json,math,shutil
import cadquery as cq
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN,TopAbs_ON
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]/'proposals/sculpted/model'
SNAP=ROOT/'fusion_native/snapshots/paired-bearing-target/b968fea927022ba467e05eb52ab602a680e14fd7295c263eefcb95a58a90cdc6'
F=HERE/'input-step';F.mkdir(exist_ok=True)
keys=['hip_hub','motor_mount_ring','thigh_inner','thigh_outer']+[f'pod_sleeve_{a}' for a in (90,210,330)]
sources={}
for key in keys:
 p=(ROOT/'fusion_native/snapshots/knee-stub-cleanup'/f'{key}.step') if key=='thigh_outer' else SNAP/'step'/f'{key}.step'
 shutil.copy2(p,F/p.name);sources[key]=dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
p=ROOT/'output/integrated-candidate/step/input_crank.step';shutil.copy2(p,F/p.name);sources['input_crank']=dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
rows=[]
for key in keys:
 shape=cq.importers.importStep(str(F/(key+'.step'))).val();classifier=BRepClass3d_SolidClassifier(shape.wrapped)
 for a in (90,210,330):
  if key.startswith('pod_sleeve_') and key!=f'pod_sleeve_{a}':continue
  aa=math.radians(a);x,z=43.5*math.cos(aa),43.5*math.sin(aa)
  for r in (2.0,2.6,3.3,4.3):
   px,pz=x+r*math.cos(aa),z+r*math.sin(aa)
   intervals=[];start=None
   for i in range(-20,321):
    y=i*.25;classifier.Perform(gp_Pnt(px,y,pz),1e-6);inside=classifier.State() in (TopAbs_IN,TopAbs_ON)
    if inside and start is None:start=y
    if not inside and start is not None:intervals.append([start,y-.25]);start=None
   if start is not None:intervals.append([start,80])
   rows.append(dict(part=key,tie_angle=a,radial_witness_mm=r,axial_material_intervals_quarter_mm=intervals))
report=dict(source_model_sha256=SNAP.name,scope='Quarter-mm outward radial witness samples only; use exact contact probes for final bearing areas.',sources=sources,sections=rows)
(HERE/'pod-stack-sections.json').write_text(json.dumps(report,indent=2)+'\n')
for r in rows:
 if r['radial_witness_mm'] in (2.0,3.3):print(r,flush=True)
