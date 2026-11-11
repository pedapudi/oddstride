"""Derive minimal exact cubic spans from four editable stem stations and end slopes."""
import json,sys
from pathlib import Path
import numpy as np
from scipy.interpolate import BSpline
from OCP.BRepAdaptor import BRepAdaptor_Curve
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent));import cohesive_limb as cl
rows=[]
for edge in cl.shin_outline(0).Edges():
 if edge.geomType()!='BSPLINE':continue
 a=BRepAdaptor_Curve(edge.wrapped);c=a.BSpline();knots=[c.Knot(i) for i in range(1,c.NbKnots()+1)];full=[c.Knot(i) for i in range(1,c.NbKnots()+1) for _ in range(c.Multiplicity(i))];basis=BSpline(full,np.eye(c.NbPoles()),3);matrix=np.vstack([basis(knots),basis.derivative()(knots[0]),basis.derivative()(knots[-1])]);inverse=np.linalg.inv(matrix);constraints=np.array([[c.Value(t).X(),c.Value(t).Z()] for t in knots]+[[a.DN(knots[0],1).X(),a.DN(knots[0],1).Z()],[a.DN(knots[-1],1).X(),a.DN(knots[-1],1).Z()]])
 spans=[]
 for lo,hi in zip(knots,knots[1:]):
  span=np.vstack([basis(lo),basis(lo)+(hi-lo)/3*basis.derivative()(lo),basis(hi)-(hi-lo)/3*basis.derivative()(hi),basis(hi)])@inverse
  spans.append({'coefficients':span.tolist(),'control_points_mm':(span@constraints).tolist()})
 rows.append({'side':'right' if constraints[0,0]>0 else 'left','basis':'four original fit stations and two endpoint derivatives; piecewise cubic, C2 continuous','stations_and_derivatives_mm':constraints.tolist(),'spans':spans})
path=ROOT/'snapshots/cohesive-limb/intent/shin-cubic-design-skeleton.json';path.write_text(json.dumps(rows,indent=2));print(path)
