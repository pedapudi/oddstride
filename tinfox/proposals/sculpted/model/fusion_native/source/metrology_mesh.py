"""Absolute-deflection metrology meshes, independent of CadQuery's relative mesh mode."""
import cadquery as cq
from OCP.BRepTools import BRepTools
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from OCP.TopAbs import TopAbs_REVERSED

def absolute_tessellate(shape,linear_mm=.01,angular_rad=.04):
 BRepTools.Clean_s(shape.wrapped)
 mesher=BRepMesh_IncrementalMesh(shape.wrapped,linear_mm,False,angular_rad,True);assert mesher.IsDone()
 vertices=[];triangles=[]
 for face in shape.Faces():
  location=TopLoc_Location();mesh=BRep_Tool.Triangulation_s(face.wrapped,location);assert mesh is not None
  offset=len(vertices);transform=location.Transformation();vertices.extend(cq.Vector(mesh.Node(i).Transformed(transform)) for i in range(1,mesh.NbNodes()+1));reverse=face.wrapped.Orientation()==TopAbs_REVERSED
  for triangle in mesh.Triangles():
   a,b,c=triangle.Value(1),triangle.Value(2),triangle.Value(3);triangles.append(tuple(offset+x-1 for x in ((a,c,b) if reverse else (a,b,c))))
 return vertices,triangles
