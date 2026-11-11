"""Recompute the baseline sections from the archived solid source, not old STEP surfaces."""
import importlib.util,json
from pathlib import Path
import cadquery as cq
import numpy as np
from kinematics import ROOT
base=ROOT.parent/'design/iterations/refinement-baseline'
spec=importlib.util.spec_from_file_location('archived_limb_build',base/'build.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b);b.build_leg('FL')
report=json.loads((base/'mounting-audit.json').read_text())
for member in ['thigh','shin']:
 s=cq.Compound.makeCompound([b.solids['FL_'+member+'_inner'],b.solids['FL_'+member+'_outer']])
 print('Baseline section',member,flush=True)
 stations=range(-65,-156,-5) if member=='thigh' else range(-35,-136,-5)
 rows=[]
 for z in stations:
  cut=s.intersect(cq.Workplane('XY').box(200,200,.2).val().translate((0,60,z)))
  bounds=cut.BoundingBox();center=cut.Center();inertia=cq.Shape.matrixOfInertia(cut)
  iy=inertia[1][1]/.2-cut.Volume()/.2*.2**2/12
  rows.append({'z_mm':z,'section_modulus_y_mm3':iy/max(abs(bounds.xmin-center.x),abs(bounds.xmax-center.x))})
 report[member+'_sections']=rows;report['minimum_'+member+'_section_modulus_y_mm3']=min(v['section_modulus_y_mm3'] for v in rows)
report['section_source']='Rebuilt from archived parametric limb source using supported spline solids; replaces earlier section samples taken from incomplete STEP surface imports.'
(base/'corrected-section-audit.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k.startswith('minimum_')})
