"""Add editable native loft stations sampled from the source's exact loft.

Intermediate curves are sketch definitions, never imported solid geometry. The
original six design sections remain present. Extra stations constrain differences
between the two CAD kernels' smooth-loft interpolation.
"""
import json,math
from pathlib import Path
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.BRepTools import BRepTools_WireExplorer
from OCP.GeomAbs import GeomAbs_Line,GeomAbs_Circle
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln,gp_Pnt,gp_Dir
ROOT=Path(__file__).resolve().parents[1]

def wire(profile):
 edges=[]
 for e in profile['edges']:
  if e['kind']=='line':edge=cq.Edge.makeLine(cq.Vector(*e['start']),cq.Vector(*e['end']))
  elif e['kind']=='arc':edge=cq.Edge.makeThreePointArc(cq.Vector(*e['start']),cq.Vector(*e['mid']),cq.Vector(*e['end']))
  elif e['kind']=='circle':edge=cq.Edge.makeCircle(e['radius'],cq.Vector(*e['center']),cq.Vector(*e['normal']))
  else:edge=cq.Edge.makeSpline([cq.Vector(*p) for p in e['points']])
  edges.append(edge)
 return cq.Wire.assembleEdges(edges)

def profile(w):
 ex=BRepTools_WireExplorer(w.wrapped);edges=[]
 def xyz(p):return [p.X(),p.Y(),p.Z()]
 while ex.More():
  e=cq.Edge(ex.Current());a=BRepAdaptor_Curve(e.wrapped);u0,u1=a.FirstParameter(),a.LastParameter();row={'start':list(e.startPoint().toTuple()),'end':list(e.endPoint().toTuple()),'length':e.Length()}
  if a.GetType()==GeomAbs_Line:row['kind']='line'
  elif a.GetType()==GeomAbs_Circle:
   c=a.Circle();row.update(kind='circle' if abs(u1-u0-2*math.pi)<1e-6 else 'arc',center=xyz(c.Location()),radius=c.Radius(),normal=xyz(c.Axis().Direction()),mid=xyz(a.Value((u0+u1)/2)))
  else:
   count=max(17,min(81,math.ceil(e.Length())+1));row.update(kind='spline',points=[xyz(a.Value(u0+(u1-u0)*i/(count-1))) for i in range(count)])
  edges.append(row);ex.Next()
 f=cq.Face.makeFromWires(w)
 return {'edges':edges,'origin':list(f.Center().toTuple()),'normal':list(f.normalAt().toTuple())}

def main():
 graph=json.loads((ROOT/'snapshots/source_graph.json').read_text());overrides=json.loads((ROOT/'source/native_profile_overrides.json').read_text())
 for key in [2369,3437]:
  node=graph['nodes'][key];assert node['id']==key and node['op']=='makeLoft' and not node['ruled']
  original=node['profiles'];solid=cq.Solid.makeLoft([wire(p) for p in original],ruled=False);profiles=[]
  for i,p in enumerate(original):
   profiles.append(p)
   if i==len(original)-1:continue
   z0=p['origin'][2];z1=original[i+1]['origin'][2]
   for fraction in [i/8 for i in range(1,8)]:
    z=z0+(z1-z0)*fraction;operation=BRepAlgoAPI_Section(solid.wrapped,gp_Pln(gp_Pnt(0,0,z),gp_Dir(0,0,1)),True)
    assert operation.IsDone()
    wires=cq.Wire.combine(cq.Shape.cast(operation.Shape()).Edges());assert len(wires)==1
    profiles.append(profile(wires[0]))
  overrides[str(key)]={'profiles':profiles,'original_station_count':len(original),'native_station_count':len(profiles),'reason':'Constrain native loft interpolation to the frozen V0 source surface.'}
 path=ROOT/'source/native_profile_overrides.json';path.write_text(json.dumps(overrides,indent=2));print({k:v['native_station_count'] for k,v in overrides.items()})
if __name__=='__main__':main()
