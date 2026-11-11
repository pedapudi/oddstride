"""Validate native authoring recipes locally before sending expensive Fusion work.

This independent CAD replay is an audit tool. Its solids are never imported into
Fusion; Fusion still authors every custom part from native sketches and features.
"""
import json,sys,math
from pathlib import Path
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.gp import gp_Trsf
from build_part import recipe
ROOT=Path(__file__).resolve().parents[1]
def vector(p):return cq.Vector(*p)
def wire(profile):
 edges=[]
 for edge in profile['edges']:
  if edge['kind']=='line':e=cq.Edge.makeLine(vector(edge['start']),vector(edge['end']))
  elif edge['kind']=='arc':e=cq.Edge.makeThreePointArc(vector(edge['start']),vector(edge['mid']),vector(edge['end']))
  elif edge['kind']=='circle':e=cq.Edge.makeCircle(edge['radius'],vector(edge['center']),vector(edge['normal']))
  elif edge['kind']=='bezier':e=cq.Edge.makeBezier([vector(p) for p in edge['control_points']])
  else:e=cq.Edge.makeSpline([vector(p) for p in edge['points']])
  edges.append(e)
 return cq.Wire.assembleEdges(edges)
def replay(graph,detailed=True):
 nodes={n['id']:n for n in graph['nodes']};cache={};records={}
 def build(key):
  if key in cache:return cache[key]
  n=nodes[key];op=n['op']
  if op in ['makeBox','makeCylinder','makeCone','makeSphere']:
   kwargs={k:vector(v) if k in ['pnt','dir'] else v for k,v in n.items() if k not in ['id','op','source_translation_folded']};s=getattr(cq.Solid,op)(**kwargs)
  elif op=='extrudeLinear':s=cq.Solid.extrudeLinear(wire(n['outerWire']),[wire(p) for p in n['innerWires']],vector(n['vecNormal']),n['taper'])
  elif op=='makeLoft':s=cq.Solid.makeLoft([wire(p) for p in n['profiles']],n['ruled'])
  elif op in ['cut','fuse','intersect','profileCut']:s=getattr(build(n['target']),'cut' if op=='profileCut' else op)(*[build(k) for k in n['tools']])
  elif op=='translate':s=build(n['target']).translate(n['vector'])
  elif op=='rotate':s=build(n['target']).rotate(n['start'],n['end'],n['degrees'])
  elif op=='mirror':s=build(n['target']).mirror(n['plane'],vector(n['origin']))
  elif op=='moved':
   transform=gp_Trsf();transform.SetValues(*[v for row in n['matrix'] for v in row]);s=build(n['target']).moved(cq.Location(transform))
  elif op=='compound':s=cq.Compound.makeCompound([build(k) for k in n['tools']])
  elif op=='extractSolid':s=build(n['target']).Solids()[n['index']]
  elif op=='fillet':
   s=build(n['target']);edges=[]
   for expected in n['edges']:
    def error(edge):
     if expected['kind']=='circle' and edge.geomType()=='CIRCLE':
      circle=BRepAdaptor_Curve(edge.wrapped).Circle();p=circle.Location();return (vector([p.X(),p.Y(),p.Z()])-vector(expected['center'])).Length+abs(circle.Radius()-expected['radius'])+abs(edge.Length()-expected['length'])
     a,b=edge.startPoint(),edge.endPoint();u,v=vector(expected['start']),vector(expected['end']);return min((a-u).Length+(b-v).Length,(a-v).Length+(b-u).Length)+abs(edge.Length()-expected['length'])
    edge=min(s.Edges(),key=error);assert error(edge)<.15,(key,'edge match',error(edge))
    if edge not in edges:edges.append(edge)
   s=s.fillet(n['radius'],edges)
  elif op=='circularCutPattern':
   seed=n['seed'];tool=cq.Solid.makeCylinder(seed['radius'],seed['height'],vector(seed['pnt']),vector(seed['dir']));axis=[0,0,0];axis[n['axis']]=1
   s=build(n['target']).cut(*[tool.rotate((0,0,0),axis,i*360/n['quantity']) for i in range(n['quantity'])])
  elif op=='ruledAnnularRevolve':
   axis=[0,0,0];axis[n['axis']]=1
   outer=cq.Solid.makeLoft([cq.Wire.makeCircle(r,vector(c),vector(axis)) for c,r in zip(n['centers'],n['outer_radii'])],True)
   inner=cq.Solid.makeLoft([cq.Wire.makeCircle(r,vector(c),vector(axis)) for c,r in zip(n['centers'],n['inner_radii'])],True);s=outer.cut(inner)
  else:raise NotImplementedError(op)
  cache[key]=s;solids=s.Solids();bb=s.BoundingBox() if solids and detailed else None
  records[key]={'operation':op,'volume_mm3':s.Volume() if solids and detailed else 0 if not solids else None,'solid_count':len(solids),'bounds_mm':[bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax] if bb else None};return s
 shape=build(graph['root']);return shape,records
def audit(key):
 graph=recipe(key);shape,records=replay(graph,detailed=False)
 from audit_part import volume
 record=next(p for p in json.loads((ROOT/'manifests/parts.json').read_text())['parts'] if p['id']==key);source=cq.importers.importStep(str(ROOT/record['source_step'])).val()
 actual=volume(shape)[0];reference=volume(source)[0];result={'part':key,'source_volume_mm3':reference,'replay_volume_mm3':actual,'relative_volume_error':abs(actual-reference)/reference,'nodes':records}
 (ROOT/'audits'/f'{key}-recipe-replay.json').write_text(json.dumps(result,indent=2));print(key,'recipe volume error',result['relative_volume_error'],flush=True);return result
if __name__=='__main__':audit(sys.argv[1])
