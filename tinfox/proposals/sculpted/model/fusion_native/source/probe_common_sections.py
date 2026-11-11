"""Cross-check incomplete surface intersections using solid/plane common faces."""
import json
from pathlib import Path
import cadquery as cq
from audit_sections import sample
ROOT=Path(__file__).resolve().parents[1];z=40.321092140007075;face=cq.Face.makeFromWires(cq.Workplane('XY',origin=(200,0,z)).rect(400,400).val());a=cq.importers.importStep(str(ROOT/'snapshots/step/body_nose_surround.step')).val();b=cq.importers.importStep(str(ROOT/'exports/body_nose_surround-tangent.step')).val()
sa=a.intersect(face);sb=b.intersect(face);print('face counts',len(sa.Faces()),len(sb.Faces()),'edges',len(sa.Edges()),len(sb.Edges()),flush=True)
rows=[]
for name,s,t,parent in [('source_to_native',sa,sb,a),('native_to_source',sb,sa,b)]:
 points=[p for line in sample(s) for p in line];boundary=cq.Compound.makeCompound(parent.Faces());errors=[{'p':p,'distance':t.distance(cq.Vertex.makeVertex(*p)),'self_boundary':boundary.distance(cq.Vertex.makeVertex(*p))} for p in points];rows.append({'direction':name,'worst':sorted(errors,key=lambda x:x['distance'],reverse=True)[:5],'self_max':max(x['self_boundary'] for x in errors)})
record={'source_area':sa.Area(),'native_area':sb.Area(),'source_perimeter':sum(e.Length() for e in sa.Edges()),'native_perimeter':sum(e.Length() for e in sb.Edges()),'rows':rows};(ROOT/'audits/nose-common-section-proof.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
