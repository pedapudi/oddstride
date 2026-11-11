"""Evaluate which source hull stations affect the retained end-support region."""
import sys,json
from pathlib import Path
import numpy as np,cadquery as cq
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
import build as b
from audit_part import volume
results=[]
for inset in [0,4.2]:
 target=b.torso(inset).intersect(b.box(40,300,150,(261,0,0)))
 for station_set in [[214,226,236,242],[226,236,242],[236,242]]:
  stations=[x for x in station_set if x<245.4-inset]+[245.4-inset]
  try:
   shape=cq.Solid.makeLoft([b.body_section(x,inset) for x in stations],ruled=False);edges=[e for e in shape.Edges() if e.BoundingBox().xlen<1e-4 and abs(e.Center().x-(245.4-inset))<.01];shape=cq.Workplane(obj=shape).newObject(edges).fillet(5-inset).val().intersect(b.box(40,300,150,(261,0,0)))
   errors=[]
   for a,other in [(shape,target),(target,shape)]:
    points,_=a.tessellate(.03,.1);indices=np.random.default_rng(10).choice(len(points),min(250,len(points)),replace=False);errors += [other.distance(cq.Vertex.makeVertex(*points[i].toTuple())) for i in indices]
   sv,_=volume(shape);tv,_=volume(target);row={'inset':inset,'stations':stations,'max_mm':max(errors),'volume_relative_error':abs(sv-tv)/tv};print(row,flush=True);results.append(row)
  except Exception as e:results.append({'inset':inset,'stations':stations,'error':str(e)})
(ROOT/'audits/nose-hull-station-reduction.json').write_text(json.dumps(results,indent=2))
