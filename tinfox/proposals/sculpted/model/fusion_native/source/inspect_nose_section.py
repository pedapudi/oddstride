"""Diagnose a nominal slice independently of full-surface fidelity."""
import json
from pathlib import Path
import cadquery as cq
from audit_sections import section,sample
ROOT=Path(__file__).resolve().parents[1];source=cq.importers.importStep(str(ROOT/'snapshots/step/body_nose_surround.step')).val();native=cq.importers.importStep(str(ROOT/'exports/body_nose_surround-tangent.step')).val();z=40.321092140007075;results=[]
for mode in [False,True]:
 a=section(source,2,z,mode);b=section(native,2,z,mode);rows=[]
 for name,s,t,other in [('source_to_native',a,b,native),('native_to_source',b,a,source)]:
  points=[p for curve in sample(s) for p in curve];errors=[{'point':p,'section_distance':t.distance(cq.Vertex.makeVertex(*p)),'other_solid_distance':other.distance(cq.Vertex.makeVertex(*p)),'plane_error':abs(p[2]-z)} for p in points];worst=sorted(errors,key=lambda r:r['section_distance'],reverse=True)[:8];rows.append({'direction':name,'plane_error_max':max(p['plane_error'] for p in errors),'worst':worst})
 record={'approximation':mode,'source_edges':len(a.Edges()),'native_edges':len(b.Edges()),'directions':rows};print(json.dumps(record),flush=True);results.append(record)
(ROOT/'audits/nose-section-conditioning.json').write_text(json.dumps(results,indent=2))
