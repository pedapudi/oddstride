"""Independent planar-face section reconstruction for tolerant STEP trim edges.

Native planar faces can have trim edges a few microns off their underlying plane.
OCC's face/plane Boolean may omit an entire interval. Intersect each two-dimensional surface trim curve
with the sample plane, project roots onto the analytical plane-plane line, and
retain only intervals classified inside the trimmed face. Nonplanar faces still
use OCC surface intersections. This is metrology, never model authoring.
"""
import numpy as np
import cadquery as cq
from scipy.optimize import brentq
from OCP.BRepAdaptor import BRepAdaptor_Surface,BRepAdaptor_Curve2d
from OCP.GeomAbs import GeomAbs_Plane,GeomAbs_Cylinder
from OCP.BRepClass import BRepClass_FaceClassifier
from OCP.TopAbs import TopAbs_IN,TopAbs_ON
from OCP.gp import gp_Pnt,gp_Pnt2d

def perpendicular_cylinder_section(face,adaptor,axis,offset):
 cylinder=adaptor.Cylinder();direction=np.array(cylinder.Axis().Direction().Coord())
 if abs(abs(direction[axis])-1)>1e-10:return None
 v=(offset-cylinder.Location().Coord()[axis])/direction[axis]
 u0,u1=adaptor.FirstUParameter(),adaptor.LastUParameter();roots=[u0,u1]
 for edge in face.Edges():
  trim=BRepAdaptor_Curve2d(edge.wrapped,face.wrapped);ts=np.linspace(trim.FirstParameter(),trim.LastParameter(),101);values=[trim.Value(float(t)).Y()-v for t in ts]
  for i,(a,b)in enumerate(zip(ts,ts[1:])):
   if values[i]*values[i+1]<0:
    t=brentq(lambda t:trim.Value(float(t)).Y()-v,float(a),float(b),xtol=1e-14);roots.append(trim.Value(t).X())
   if abs(values[i])<1e-9:roots.append(trim.Value(float(a)).X())
  if abs(values[-1])<1e-9:roots.append(trim.Value(float(ts[-1])).X())
 roots=sorted(u for u in roots if u0-1e-8<=u<=u1+1e-8);unique=[]
 for u in roots:
  if not unique or abs(u-unique[-1])>1e-8:unique.append(u)
 edges=[]
 for a,b in zip(unique,unique[1:]):
  if BRepClass_FaceClassifier(face.wrapped,gp_Pnt2d((a+b)/2,v),1e-8).State() not in [TopAbs_IN,TopAbs_ON]:continue
  # Split complete or nearly complete circles into stable analytic arcs.
  count=max(1,int(np.ceil((b-a)/np.pi)))
  for first,last in zip(np.linspace(a,b,count+1),np.linspace(a,b,count+1)[1:]):
   points=[cq.Vector(*adaptor.Value(float(t),float(v)).Coord())for t in [first,(first+last)/2,last]];edges.append(cq.Edge.makeThreePointArc(*points))
 return edges

def section_by_faces(shape,axis,offset):
 from audit_sections import section
 edges=[];records=[];normal=np.eye(3)[axis]
 for index,face in enumerate(shape.Faces()):
  adaptor=BRepAdaptor_Surface(face.wrapped)
  if adaptor.GetType()==GeomAbs_Cylinder:
   exact=perpendicular_cylinder_section(face,adaptor,axis,offset)
   if exact is not None:
    edges.extend(exact);records.append({'face':index,'method':'Analytic perpendicular cylinder with classified UV trim intervals','intervals':len(exact)});continue
  if adaptor.GetType()!=GeomAbs_Plane:
   edges.extend(section(face,axis,offset,True).Edges());continue
  plane=adaptor.Plane();n=np.array(plane.Axis().Direction().Coord());direction=np.cross(n,normal)
  if np.linalg.norm(direction)<1e-9:
   edges.extend(section(face,axis,offset,True).Edges());continue
  direction/=np.linalg.norm(direction);origin=np.linalg.solve(np.array([n,normal,direction]),[np.dot(n,plane.Location().Coord()),offset,0]);roots=[];projection_errors=[]
  for edge in face.Edges():
   trim=BRepAdaptor_Curve2d(edge.wrapped,face.wrapped)
   def point(t):
    uv=trim.Value(float(t));return np.array(adaptor.Value(uv.X(),uv.Y()).Coord())
   ts=np.linspace(trim.FirstParameter(),trim.LastParameter(),101);vals=[point(t)[axis]-offset for t in ts]
   for i,(a,b) in enumerate(zip(ts,ts[1:])):
    if vals[i]*vals[i+1]<0:
     t=brentq(lambda t:point(t)[axis]-offset,float(a),float(b),xtol=1e-14);p=point(t);roots.append(float(np.dot(p-origin,direction)));projection_errors.append(float(np.linalg.norm(p-(origin+roots[-1]*direction))))
    if abs(vals[i])<1e-9:roots.append(float(np.dot(point(a)-origin,direction)))
   if abs(vals[-1])<1e-9:roots.append(float(np.dot(point(ts[-1])-origin,direction)))
  roots=sorted(roots);unique=[]
  for t in roots:
   if not unique or abs(t-unique[-1])>1e-6:unique.append(t)
  count=0
  for a,b in zip(unique,unique[1:]):
   midpoint=origin+(a+b)/2*direction;state=BRepClass_FaceClassifier(face.wrapped,gp_Pnt(*midpoint),1e-6).State()
   if state in [TopAbs_IN,TopAbs_ON]:edges.append(cq.Edge.makeLine(cq.Vector(*(origin+a*direction)),cq.Vector(*(origin+b*direction))));count+=1
  records.append({'face':index,'intervals':count,'maximum_trim_projection_mm':max(projection_errors,default=0)})
 return cq.Compound.makeCompound(edges),records
