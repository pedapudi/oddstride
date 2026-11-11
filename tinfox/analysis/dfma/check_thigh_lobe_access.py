"""Finite straight-tool corridor screen at current stator-pocket lobes."""
from pathlib import Path
import sys,json,math,hashlib
import cadquery as cq
ROOT=Path(__file__).resolve().parents[2]/'proposals/sculpted/model';sys.path.insert(0,str(ROOT));import service_design as sd
folder=Path(__file__).resolve().parent/'input-step'
parts={key:cq.importers.importStep(str(folder/(key+'.step'))).val() for key in ['thigh_inner','thigh_outer']}
_,t,_,_=sd.port_frame(54.4,1)
directions={'X+':[1,0,0],'X-':[-1,0,0],'Y+':[0,1,0],'Y-':[0,-1,0],'Z+':[0,0,1],'Z-':[0,0,-1],'root_split+':t.tolist(),'root_split-':(-t).tolist()}
rows=[]
for angle in [90,210,330]:
 a=math.radians(angle);point=((43.5+3)*math.cos(a),52,(43.5+3)*math.sin(a))
 for key,shape in parts.items():
  tests=[]
  for label,direction in directions.items():
   tool=cq.Solid.makeCylinder(1.5,120,cq.Vector(*point),cq.Vector(*direction));v=sum(s.Volume() for s in shape.intersect(tool).Solids())
   tests.append({'direction':label,'overlap_mm3':v,'clear_sampled_corridor':v<.001})
  rows.append({'part':key,'tie_angle_deg':angle,'probe_center_mm':point,'point_inside_part':shape.isInside(cq.Vector(*point)), 'tool_diameter_mm':3,'tool_length_mm':120,'tests':tests})
report={'checks':rows,'input_step_manifest':'input-step/manifest.json','scope':'One finite cylindrical approach per direction at one void location per lobe. A clear corridor does not establish reach to every cut face, flute length, feasible fixturing or holder clearance. Blocked axial directions alone do not prove an undercut.'}
(Path(__file__).resolve().parent/'thigh-lobe-access.json').write_text(json.dumps(report,indent=2))
for r in rows:print(r['part'],r['tie_angle_deg'],[x['direction'] for x in r['tests'] if x['clear_sampled_corridor']],flush=True)
