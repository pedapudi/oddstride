"""Explicit absolute-deflection meshes for comparison, with parent-face checks."""
import math
import numpy as np
import cadquery as cq
from OCP.BRepTools import BRepTools
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from OCP.TopAbs import TopAbs_REVERSED

def tessellate_absolute(shape,linear_mm=.005,angular_radians=.03):
 BRepTools.Clean_s(shape.wrapped)
 mesher=BRepMesh_IncrementalMesh(shape.wrapped,linear_mm,False,angular_radians,True);assert mesher.IsDone()
 vertices=[];triangles=[];errors=[];missing=[]
 for index,face in enumerate(shape.Faces()):
  location=TopLoc_Location();poly=BRep_Tool.Triangulation_s(face.wrapped,location)
  if poly is None:missing.append(index);continue
  transform=location.Transformation();points=[poly.Node(i).Transformed(transform)for i in range(1,poly.NbNodes()+1)];offset=len(vertices);vertices.extend([p.Coord()for p in points]);reverse=face.wrapped.Orientation()==TopAbs_REVERSED
  for tri in poly.Triangles():
   ids=[tri.Value(i)-1+offset for i in[1,2,3]];triangles.append([ids[0],ids[2],ids[1]]if reverse else ids)
  for i in np.unique(np.linspace(0,len(points)-1,min(100,len(points))).astype(int)):
   p=points[i];errors.append(face.distance(cq.Vertex.makeVertex(*p.Coord())))
 assert not missing,missing
 record={'linear_deflection_mm':linear_mm,'angular_deflection_rad':angular_radians,'relative_deflection':False,'faces':len(shape.Faces()),'vertices':len(vertices),'triangles':len(triangles),'sampled_vertices_to_own_face':len(errors),'maximum_own_face_deviation_mm':max(errors,default=0),'own_face_gate_passed':max(errors,default=0)<linear_mm*1.1}
 return np.array(vertices),np.array(triangles),record
