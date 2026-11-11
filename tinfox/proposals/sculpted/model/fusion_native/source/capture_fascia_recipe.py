"""Reconstruct the removable face without discarded full-body tooling."""
import json
from pathlib import Path
import numpy as np
import cadquery as cq
import capture as cap
import build as b
from capture_cover_delta import compare
ROOT=Path(__file__).resolve().parents[1]
def bowed(offset=0):
 wires=[]
 for zz in np.linspace(-53,57,19):
  points=[(b.face_x(float(y),float(zz))-offset,float(y)) for y in np.linspace(-110,110,13)]
  wires.append(cq.Workplane('XY',origin=(0,0,float(zz))).moveTo(230,-110).lineTo(*points[0]).spline(points[1:],includeCurrent=True).lineTo(230,110).close().val())
 return cq.Solid.makeLoft(wires,ruled=False)
def blank(inset=0):
 wires=[]
 for x,w,h,r in [(241.3,200.3,87.7,18),(243.5,196.5,83.5,17),(276,192.5,80,16)]:
  wire=cq.Workplane('YZ',origin=(x,0,2)).rect(w-2*inset,h-2*inset).val();wires.append(wire.fillet2D(r-inset,wire.Vertices()))
 return cq.Solid.makeLoft(wires,ruled=True)
def fascia():
 inside=bowed(2.1);s=blank().intersect(bowed()).cut(blank(2.1).intersect(inside)).clean()
 aperture=cq.Workplane('YZ',origin=(240,0,5)).rect(168,40).extrude(40).edges('|X').fillet(10).val();s=s.cut(aperture)
 for y in [-89,89]:
  for z in [-27,27]:
   s=s.cut(b.cyl(1.7,30,(239,y,z),(1,0,0))).cut(b.cyl(2.7,1.8,(b.face_x(y,z)-.6,y,z),(1,0,0)))
   s=s.cut(b.cyl(3.5,30,(239,y,z),(1,0,0)).intersect(inside))
 # All other source nose pieces end behind X=243 mm and cannot affect this face.
 return s.intersect(b.box(100,300,150,(293,0,0))).clean()
shape=fascia();reference=cq.importers.importStep(str(ROOT/'snapshots/step/front_fascia.step')).val();evidence=compare(reference,shape)
root=cap.ref(shape);bb=shape.BoundingBox();record={'root':root,'volume_mm3':shape.Volume(),'bounds_mm':{k:getattr(bb,k) for k in ['xmin','xmax','ymin','ymax','zmin','zmax']}}
folder=ROOT/'snapshots/reconstructed/front_fascia';folder.mkdir(parents=True,exist_ok=True)
(folder/'recipe.json').write_text(json.dumps({'schema':1,'nodes':cap.NODES,'parts':{'front_fascia':record}},indent=2));(folder/'reconstruction-audit.json').write_text(json.dumps(evidence,indent=2));print(evidence,flush=True)
