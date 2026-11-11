"""Compare functional end-envelope regions, excluding unused construction stock."""
import json,sys,hashlib
from pathlib import Path
import numpy as np
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
import build as b
from audit_part import volume,area
export_label=sys.argv[1] if len(sys.argv)>1 else 'nose-outer-intent';inset=float(sys.argv[2]) if len(sys.argv)>2 else 0
native=cq.importers.importStep(str(ROOT/'exports'/f'{export_label}.step')).val();source=b.torso(inset)
mask=b.box(40,300,150,(261,0,0));native=native.intersect(mask);source=source.intersect(mask)
results={}
for label,a,target in [('native_to_source',native,source),('source_to_native',source,native)]:
 points,_=a.tessellate(.02,.05);rng=np.random.default_rng(6);ids=rng.choice(len(points),min(600,len(points)),replace=False);rows=[{'point':points[i].toTuple(),'distance':target.distance(cq.Vertex.makeVertex(*points[i].toTuple()))} for i in ids];results[label]={'max_mm':max(x['distance'] for x in rows),'worst':sorted(rows,key=lambda x:x['distance'],reverse=True)[:5]}
sv,_=volume(source);nv,_=volume(native);sa,_=area(source);na,_=area(native)
record={'surface':results,'relative_volume_error':abs(nv-sv)/sv,'relative_area_error':abs(na-sa)/sa,'source_faces':len(source.Faces()),'native_faces':len(native.Faces()),'passed':max(r['max_mm'] for r in results.values())<.05 and abs(nv-sv)/sv<.001 and abs(na-sa)/sa<.001,'region':'X >= 241 mm; the actual V0 end-shell/chin envelope','native_step_sha256':hashlib.sha256((ROOT/'exports'/f'{export_label}.step').read_bytes()).hexdigest()}
(ROOT/'audits'/f'{export_label}-geometry.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)
