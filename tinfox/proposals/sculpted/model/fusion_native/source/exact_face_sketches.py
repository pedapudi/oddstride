"""Author the curved face with editable cubic control-point sketch spans.

Bezier poles are planar sketch dimensions, not a BRep import. Replacing sampled
fit-point curves avoids interpolation error around nearly tangent section planes.
API: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_SketchControlPointSplines_add.htm
"""
import json,sys,copy
from pathlib import Path
import cadquery as cq
import numpy as np
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GeomConvert import GeomConvert_BSplineCurveToBezierCurve
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent));import build as b
from build_part import recipe

def spans(z,offset):
 points=[(b.face_x(float(y),z)-offset,float(y)) for y in np.linspace(-110,110,13)]
 w=cq.Workplane('XY',origin=(0,0,z)).moveTo(230,-110).lineTo(*points[0]).spline(points[1:],includeCurrent=True).lineTo(230,110).close().val()
 edge=next(e for e in w.Edges() if e.geomType()=='BSPLINE');a=BRepAdaptor_Curve(edge.wrapped)
 converter=GeomConvert_BSplineCurveToBezierCurve(a.BSpline(),a.FirstParameter(),a.LastParameter(),1e-10);result=[]
 for index in range(1,converter.NbArcs()+1):
  arc=converter.Arc(index);assert arc.Degree()==3 and not arc.IsRational()
  control=[list(arc.Pole(i).Coord()) for i in range(1,5)]
  result.append({'kind':'bezier','start':control[0],'end':control[-1],'control_points':control,'degree':3})
 return result

def update(key):
 graph=recipe(key);overrides={}
 for node in graph['nodes']:
  if node['op']!='makeLoft':continue
  profiles=copy.deepcopy(node['profiles'])
  if len(profiles)!=19 or len(profiles[0]['edges'])!=4:continue
  if sum(e['kind']=='spline' for e in profiles[0]['edges'])!=1:continue
  for profile in profiles:
   z=profile['origin'][2];new=[]
   for edge in profile['edges']:
    if edge['kind']!='spline':new.append(edge);continue
    p=edge['points'][0];offset=b.face_x(p[1],p[2])-p[0]
    curves=spans(z,offset)
    assert np.linalg.norm(np.array(curves[0]['start'])-edge['points'][0])<1e-6
    new.extend(curves)
   profile['edges']=new
  overrides[str(node['id'])]={'profiles':profiles,'reason':'Exact cubic control-point spans from the source face construction; editable native sketches rather than fixed splines or sampled fit curves.'}
 assert overrides,key
 (ROOT/'source/profile_overrides'/f'{key}.json').write_text(json.dumps(overrides,indent=2));print(key,{k:len(v['profiles'][0]['edges']) for k,v in overrides.items()})
for key in sys.argv[1:]:update(key)
