"""Reconstruct a planar face section from boundary roots and trimmed-face membership."""
import json
import numpy as np
import cadquery as cq
from scipy.optimize import brentq
from OCP.BRepClass import BRepClass_FaceClassifier
from OCP.TopAbs import TopAbs_IN,TopAbs_ON
from OCP.gp import gp_Pnt
from audit_sections import ROOT,section,sample
s=cq.importers.importStep(str(ROOT/'exports/body_nose_surround-tangent.step')).val();face=s.Faces()[54];z=40.321092140007075;points=[]
for edge in face.Edges():
 ts=np.linspace(0,1,101)
 for a,b in zip(ts,ts[1:]):
  va=edge.positionAt(float(a)).z-z;vb=edge.positionAt(float(b)).z-z
  if va*vb<0:
   t=brentq(lambda t:edge.positionAt(t).z-z,float(a),float(b),xtol=1e-14);points.append(edge.positionAt(t).toTuple())
  if abs(va)<1e-9:points.append(edge.positionAt(float(a)).toTuple())
points=sorted({tuple(round(v,9) for v in p) for p in points},key=lambda p:p[1]);rows=[]
for a,b in zip(points,points[1:]):
 m=(np.array(a)+np.array(b))/2;cl=BRepClass_FaceClassifier(face.wrapped,gp_Pnt(*m),1e-6);rows.append({'a':a,'b':b,'state':str(cl.State()),'inside':cl.State() in [TopAbs_IN,TopAbs_ON]})
print(json.dumps(rows,indent=2));(ROOT/'audits/nose-planar-section-proof.json').write_text(json.dumps(rows,indent=2))
