"""Confirm the V0 fascia can be built without obsolete parent nose layers."""
import sys,json
from pathlib import Path
import numpy as np
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
import build as b

def bowed(offset):
 wires=[]
 for z in np.linspace(-53,57,19):
  p=[(b.face_x(float(y),float(z))-offset,float(y)) for y in np.linspace(-110,110,13)];wires.append(cq.Workplane('XY',origin=(0,0,float(z))).moveTo(230,-110).lineTo(*p[0]).spline(p[1:],includeCurrent=True).lineTo(230,110).close().val())
 return cq.Solid.makeLoft(wires,ruled=False)
def blank(inset):
 wires=[]
 for x,w,h,r in [(241.3,200.3,87.7,18),(243.5,196.5,83.5,17),(276,192.5,80,16)]:
  w=cq.Workplane('YZ',origin=(x,0,2)).rect(w-2*inset,h-2*inset).val();wires.append(w.fillet2D(r-inset,w.Vertices()))
 return cq.Solid.makeLoft(wires,ruled=True)
front=bowed(0);back=bowed(2.1);s=blank(0).intersect(front).cut(blank(2.1).intersect(back));s=s.cut(cq.Workplane('YZ',origin=(240,0,5)).rect(168,40).extrude(40).edges('|X').fillet(10).val())
for y in [-89,89]:
 for z in [-27,27]:
  s=s.cut(b.cyl(1.7,30,(239,y,z),(1,0,0))).cut(b.cyl(2.7,1.8,(b.face_x(y,z)-.6,y,z),(1,0,0)))
  s=s.cut(b.cyl(3.5,30,(239,y,z),(1,0,0)).intersect(back))
s=s.intersect(b.box(100,300,150,(293,0,0))).clean();cq.exporters.export(s,str(ROOT/'exports/fascia-functional-reconstruction.step'))
from audit_part import audit
audit('front_fascia','fascia-functional-reconstruction')
