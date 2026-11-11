"""Recover the hood's eight-station interpolation as editable Bezier guides."""
import sys,json,math
from pathlib import Path
import numpy as np
from scipy.optimize import brentq
import cadquery as cq
from OCP.BRep import BRep_Tool
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent));import low_sensor_saddle as h
result={}
for inner,label in [(False,'Outer'),(True,'Inner')]:
 stations=[(x,w-8 if inner else w,lo-3 if inner else lo,hi-4 if inner else hi,min(2 if inner else 4,((hi-4)-(lo-3) if inner else hi-lo)/2-.2)) for x,w,lo,hi in h.STATIONS]
 shape=h.smooth_loft([h.wire(x,w,lo,hi,r) for x,w,lo,hi,r in stations]);surfaces=[BRep_Tool.Surface_s(f.wrapped) for f in shape.Faces()];surfaces=[s for s in surfaces if hasattr(s,'NbVPoles')];s=surfaces[0];assert s.VDegree()==7 and s.NbVPoles()==8 and s.NbVKnots()==2;xp=np.array([s.Pole(1,i).X() for i in range(1,9)]);basis=lambda t:np.array([math.comb(7,i)*t**i*(1-t)**(7-i) for i in range(8)]);ts=[0]+[brentq(lambda t:float(basis(t)@xp)-x,0,1) for x,*_ in stations[1:-1]]+[1];weights=np.linalg.inv(np.array([basis(t) for t in ts]));guides=[]
 candidates=[]
 for f in surfaces:
  for u in [f.UKnot(1),(f.UKnot(1)+f.UKnot(f.NbUKnots()))/2,f.UKnot(f.NbUKnots())]:
   curve=f.UIso(u);candidates.append(np.array([curve.Pole(i).Coord() for i in range(1,9)]))
 for edge in ['horizontal','vertical','corner']:
  for sign in [-1,1]:
   for top in [False,True]:
    points=[]
    for x,w,lo,hi,r in stations:
     if edge=='horizontal':y=sign*(w/2-r);z=hi if top else lo
     elif edge=='vertical':y=sign*w/2;z=hi-r if top else lo+r
     else:y=sign*(w/2-r+r/math.sqrt(2));z=hi-r+r/math.sqrt(2) if top else lo+r-r/math.sqrt(2)
     points.append([x,y,z])
    poles=weights@np.array(points);error=min(float(np.max(np.linalg.norm(poles-p,axis=1))) for p in candidates);assert error<.0001,(label,edge,sign,top,error);guides.append({'edge':edge,'sign':sign,'top':top,'source_control_pole_error_mm':error})
 result[label]={'degree':7,'section_parameters':ts,'station_to_bezier_coefficients':weights.tolist(),'guides':guides}
(ROOT/'snapshots/current-targets/hood-loft-interpolation.json').write_text(json.dumps(result,indent=2));print({label:{'degree':r['degree'],'guide_count':len(r['guides']),'maximum_source_pole_error_mm':max(g['source_control_pole_error_mm'] for g in r['guides'])} for label,r in result.items()})
