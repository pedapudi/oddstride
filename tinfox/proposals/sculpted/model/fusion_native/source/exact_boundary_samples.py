"""Sample every trimmed BRep face without depending on a tessellator.

Samples are evaluated on the underlying surface after UV classification. Trim
samples use the face's two-dimensional edge curves, avoiding tolerant 3D edge
vertices that can lie away from their parent surface.
"""
import numpy as np
from OCP.BRepAdaptor import BRepAdaptor_Surface,BRepAdaptor_Curve2d
from OCP.BRepClass import BRepClass_FaceClassifier
from OCP.BRepTools import BRepTools
from OCP.TopAbs import TopAbs_IN,TopAbs_ON
from OCP.gp import gp_Pnt2d

def sample_boundary(shape):
 points=[];records=[];rng=np.random.default_rng(427)
 for index,face in enumerate(shape.Faces()):
  surface=BRepAdaptor_Surface(face.wrapped);u0,u1,v0,v1=BRepTools.UVBounds_s(face.wrapped);interior=[];trim=[]
  for u in np.linspace(u0,u1,17):
   for v in np.linspace(v0,v1,17):
    if BRepClass_FaceClassifier(face.wrapped,gp_Pnt2d(float(u),float(v)),1e-9).State()==TopAbs_IN:interior.append((float(u),float(v)))
  for edge in face.Edges():
   curve=BRepAdaptor_Curve2d(edge.wrapped,face.wrapped)
   for t in np.linspace(curve.FirstParameter(),curve.LastParameter(),17):
    uv=curve.Value(float(t));trim.append((uv.X(),uv.Y()))
  if not interior:
   for u,v in rng.uniform([u0,v0],[u1,v1],(2000,2)):
    if BRepClass_FaceClassifier(face.wrapped,gp_Pnt2d(float(u),float(v)),1e-9).State()==TopAbs_IN:interior.append((float(u),float(v)))
  assert trim,(index,'No surface trim samples')
  count=32 if face.Area()>500 else 12;chosen=[]
  for candidates in [interior,trim]:
   if candidates:chosen.extend(candidates[int(i)]for i in np.linspace(0,len(candidates)-1,min(count,len(candidates))).astype(int))
  start=len(points)
  for u,v in chosen:points.append(surface.Value(u,v).Coord())
  records.append({'face':index,'samples':len(chosen),'interior_candidates':len(interior),'trim_candidates':len(trim),'sample_range':[start,len(points)],'method':'Exact surface evaluation; interior UV classified, boundary UV taken from face trim curves'})
 assert len(records)==len(shape.Faces()) and all(r['samples']for r in records)
 return np.array(points),{'faces':records,'all_faces_sampled':True,'sample_count':len(points),'scope':'Finite samples of every face; not a continuous Hausdorff bound.'}
