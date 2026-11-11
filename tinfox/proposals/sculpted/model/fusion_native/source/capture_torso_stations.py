"""Replace fragile end fillets with editable lofts through exact source sections.

Only native sketches and loft/extrude/union features are authored in Fusion.
The source BRep is used here to measure sectional curves, never imported there.
"""
import json,sys,importlib.util
from pathlib import Path
import cadquery as cq
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln,gp_Pnt,gp_Dir
from refine_loft_profiles import profile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
spec=importlib.util.spec_from_file_location('frozen_native_reference',ROOT/'snapshots/source/build.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
overrides={};out=ROOT/'source/torso_overrides.json'
# Final rear-end fillet nodes identify each complete torso envelope.
for key,inset in [(9,0),(19,2.8),(37,.6),(1418,1.9),(1430,4.7),(234,9),(4112,4.2)]:
 if len(sys.argv)>1 and str(key)!=sys.argv[1]:continue
 solid=b.torso(inset);cache={}
 def section(x):
  if x in cache:return cache[x]
  op=BRepAlgoAPI_Section(solid.wrapped,gp_Pln(gp_Pnt(x,0,0),gp_Dir(1,0,0)),True);assert op.IsDone()
  wires=cq.Wire.combine(cq.Shape.cast(op.Shape()).Edges());assert len(wires)==1,(key,x,len(wires))
  cache[x]=profile(wires[0]);return cache[x]
 front_end=245.4-inset;rear_end=-232+inset
 front=[x for x in [132,138,148,160,172,180,185,192,202,214,226,236,242] if x<front_end]
 rear=[x for x in [-228,-221,-212,-202,-192,-185,-180,-172,-160,-148,-138,-132] if x>rear_end]
 front=sorted(set(front+[front_end]));rear=sorted(set([rear_end]+rear))
 for values in [front,rear]:values[:]=sorted(set(values+[(a+c)/2 for a,c in zip(values,values[1:])]))
 for values,end,direction,radius in [(front,front_end,-1,max(.3,5-inset)),(rear,rear_end,1,max(.3,4-inset))]:
  values[:]=sorted(set(values+[end+direction*radius*f for f in [0,.001,.005,.02,.05,.1,.2,.35,.5,.75,1,1.25]]))
 base=100000+key*10
 nodes=[{'id':base,'op':'extrudeLinear','outerWire':section(-132),'innerWires':[],'vecNormal':[264.,0.,0.],'taper':0},
        {'id':base+1,'op':'makeLoft','profiles':[section(x) for x in front],'ruled':False},
        {'id':base+2,'op':'makeLoft','profiles':[section(x) for x in rear],'ruled':False},
        {'id':key,'op':'fuse','target':base,'tools':[base+1,base+2]}]
 overrides[str(key)]={'nodes':nodes,'inset_mm':inset,'source':'Frozen build.torso; measured planar section curves','station_counts':[len(front),len(rear)]}
 target=ROOT/'source/torso_overrides';target.mkdir(exist_ok=True);(target/(str(key)+'.json')).write_text(json.dumps(overrides[str(key)],indent=2));print(key,inset,len(front),len(rear),flush=True)
