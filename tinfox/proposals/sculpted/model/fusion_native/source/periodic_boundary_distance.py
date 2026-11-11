"""Resolve periodic surface branches before accepting an off-boundary diagnosis."""
import math
import cadquery as cq
from OCP.BRep import BRep_Tool
from OCP.BRepTools import BRepTools
from OCP.BRepClass import BRepClass_FaceClassifier
from OCP.GeomAPI import GeomAPI_ProjectPointOnSurf
from OCP.gp import gp_Pnt,gp_Pnt2d
from OCP.TopAbs import TopAbs_IN,TopAbs_ON

class BoundaryDistance:
 def __init__(self,shape):
  self.faces=shape.Faces();self.compound=cq.Compound.makeCompound(self.faces);self.periodic=[];self.recoveries=[]
  for i,face in enumerate(self.faces):
   surface=BRep_Tool.Surface_s(face.wrapped)
   if surface.IsUPeriodic() or surface.IsVPeriodic():self.periodic.append((i,face,surface,BRepTools.UVBounds_s(face.wrapped)))
 def __call__(self,point):
  value=self.compound.distance(cq.Vertex.makeVertex(*point))
  if value<.005:return value
  original=value
  for index,face,surface,(u0,u1,v0,v1) in self.periodic:
   projection=GeomAPI_ProjectPointOnSurf(gp_Pnt(*point),surface)
   if not projection.NbPoints() or projection.LowerDistance()>=value:continue
   u,v=projection.LowerDistanceParameters()
   def branches(t,lo,hi,periodic,period):
    if not periodic:return [t]
    return [t+k*period for k in range(math.ceil((lo-t-1e-8)/period),math.floor((hi-t+1e-8)/period)+1)]
   us=branches(u,u0,u1,surface.IsUPeriodic(),surface.UPeriod() if surface.IsUPeriodic() else 1)
   vs=branches(v,v0,v1,surface.IsVPeriodic(),surface.VPeriod() if surface.IsVPeriodic() else 1)
   for pu in us:
    for pv in vs:
     if BRepClass_FaceClassifier(face.wrapped,gp_Pnt2d(pu,pv),1e-7).State() in [TopAbs_IN,TopAbs_ON]:
      candidate=surface.Value(pu,pv).Distance(gp_Pnt(*point))
      if candidate<value:
       value=candidate;self.recoveries.append({'point_mm':list(point),'face':index,'original_compound_distance_mm':original,'classified_uv':[pu,pv],'projected_distance_mm':candidate})
  return value
