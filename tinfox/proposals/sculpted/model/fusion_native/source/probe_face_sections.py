"""Independently intersect individual boundary faces to check a missing section."""
import json
import cadquery as cq
from pathlib import Path
from audit_sections import section,sample
ROOT=Path(__file__).resolve().parents[1];z=40.321092140007075
shapes=[cq.importers.importStep(str(ROOT/p)).val() for p in ['snapshots/step/body_nose_surround.step','exports/body_nose_surround-tangent.step']]
curves=[]
for s in shapes:
 edges=[]
 for f in s.Faces():edges.extend(section(f,2,z,True).Edges())
 curves.append(cq.Compound.makeCompound(edges))
 print('edges',len(edges),flush=True)
rows=[]
for a,b,parent in [(curves[0],curves[1],shapes[0]),(curves[1],curves[0],shapes[1])]:
 ps=[p for line in sample(a) for p in line];boundary=cq.Compound.makeCompound(parent.Faces());errors=[{'point':p,'error':b.distance(cq.Vertex.makeVertex(*p)),'self':boundary.distance(cq.Vertex.makeVertex(*p))} for p in ps];rows.append({'samples':len(ps),'worst':sorted(errors,key=lambda r:r['error'],reverse=True)[:5],'selfmax':max(r['self'] for r in errors)})
record={'rows':rows,'perimeters':[sum(e.Length() for e in s.Edges()) for s in curves]};(ROOT/'audits/nose-face-section-proof.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
