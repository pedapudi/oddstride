"""Capture additional native sketch stations on the exact authorized roof lofts."""
import json
from pathlib import Path
import cadquery as cq
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln,gp_Pnt,gp_Dir
from refine_loft_profiles import wire,profile
ROOT=Path(__file__).resolve().parents[1]
record=next(p for p in json.loads((ROOT/'manifests/parts.json').read_text())['parts'] if p['id']=='body_center_0')
graph=json.loads((ROOT/record['source_graph']).read_text());nodes={n['id']:n for n in graph['nodes']};overrides={}
for key in [480,481]:
 original=nodes[key]['profiles'];solid=cq.Solid.makeLoft([wire(p) for p in original],False);profiles=[]
 for i,p in enumerate(original):
  profiles.append(p)
  if i==len(original)-1:continue
  z0,z1=p['origin'][2],original[i+1]['origin'][2]
  for fraction in [.25,.5,.75]:
   z=z0+(z1-z0)*fraction;op=BRepAlgoAPI_Section(solid.wrapped,gp_Pln(gp_Pnt(0,0,z),gp_Dir(0,0,1)),True);assert op.IsDone()
   wires=cq.Wire.combine(cq.Shape.cast(op.Shape()).Edges());assert len(wires)==1
   profiles.append(profile(wires[0]))
 overrides[str(key)]={'profiles':profiles,'original_station_count':len(original),'native_station_count':len(profiles),'reason':'Constrain native roof interpolation to the exact authorized V0 source loft.'}
out=ROOT/'source/profile_overrides';out.mkdir(exist_ok=True);(out/'body_center_0.json').write_text(json.dumps(overrides,indent=2));print({k:v['native_station_count'] for k,v in overrides.items()})
