"""Capture constructive CAD operations as editable-feature recipes, never meshes.

The recipe stores analytic primitives, planar sketch curves, solid operations and
transforms. Source BReps are used only to read sketch curves and check results.
No serialized BRep, STEP or mesh is used to author a Fusion part.
"""
import json, math, functools, sys, hashlib
from pathlib import Path
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.BRepTools import BRepTools_WireExplorer
from OCP.GeomAbs import GeomAbs_Line,GeomAbs_Circle,GeomAbs_BSplineCurve
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
NODES=[];UNKNOWN=[];SHAPES={}

def xyz(v):
    if hasattr(v,'toTuple'):return list(v.toTuple())
    if hasattr(v,'X'):return [v.X(),v.Y(),v.Z()]
    return list(v)

def edge(e):
    a=BRepAdaptor_Curve(e.wrapped);u0,u1=a.FirstParameter(),a.LastParameter();kind=a.GetType()
    d={'start':xyz(e.startPoint()),'end':xyz(e.endPoint()),'length':e.Length()}
    if kind==GeomAbs_Line:d['kind']='line'
    elif kind==GeomAbs_Circle:
        c=a.Circle();d.update(kind='circle' if abs(u1-u0-2*math.pi)<1e-6 else 'arc',center=xyz(c.Location()),radius=c.Radius(),normal=xyz(c.Axis().Direction()),mid=xyz(a.Value((u0+u1)/2)))
    else:
        # Native editable fitted spline, checked against source after exporting.
        # More samples are retained around the tightly curved limb transitions.
        n=max(8,min(81,math.ceil(e.Length()/2)+1))
        d.update(kind='spline',points=[xyz(a.Value(u0+(u1-u0)*i/(n-1))) for i in range(n)])
    return d

def wire(w):
    ex=BRepTools_WireExplorer(w.wrapped);edges=[]
    while ex.More():edges.append(edge(cq.Edge(ex.Current())));ex.Next()
    # Plane from the source planar face; all authored profile geometry is 2D.
    f=cq.Face.makeFromWires(w);normal=xyz(f.normalAt());origin=xyz(f.Center())
    return {'edges':edges,'origin':origin,'normal':normal}

def ref(s):
    n=getattr(s,'_native_node',None)
    if n is None:n=SHAPES.get(s.hashCode())
    if n is None:
        UNKNOWN.append({'type':str(type(s)),'volume':s.Volume(),'bounds':xyz(s.BoundingBox().center)})
        raise RuntimeError('Unrecorded source solid; refusing BRep/mesh fallback: '+str(type(s)))
    return n

def node(out,kind,**data):
    n=len(NODES);NODES.append({'id':n,'op':kind,**data});out._native_node=n;SHAPES[out.hashCode()]=n;return out

def alias(name):
    old=getattr(cq.Shape,name)
    @functools.wraps(old)
    def wrapped(self,*args,**kwargs):
        out=old(self,*args,**kwargs)
        if hasattr(self,'_native_node'):out._native_node=self._native_node
        return out
    setattr(cq.Shape,name,wrapped)

for name in ['clean','fix','copy']:alias(name)
_old_solids=cq.Shape.Solids
def _solids(self):
    result=_old_solids(self)
    if hasattr(self,'_native_node'):
        for i,s in enumerate(result):
            if len(result)==1:s._native_node=self._native_node;SHAPES[s.hashCode()]=self._native_node
            else:node(s,'extractSolid',target=ref(self),index=i)
    return result
cq.Shape.Solids=_solids
for name in ['cut','fuse','intersect']:
    old=getattr(cq.Shape,name)
    def wrap(old=old,name=name):
        @functools.wraps(old)
        def fn(self,*args,**kwargs):
            out=old(self,*args,**kwargs)
            if hasattr(self,'_native_node'):node(out,name,target=ref(self),tools=[ref(s) for s in args])
            return out
        return fn
    setattr(cq.Shape,name,wrap())
for name in ['translate','rotate','mirror','moved']:
    old=getattr(cq.Shape,name)
    def wrap(old=old,name=name):
        @functools.wraps(old)
        def fn(self,*args,**kwargs):
            out=old(self,*args,**kwargs)
            if hasattr(self,'_native_node'):
                if name=='translate':data={'vector':xyz(args[0])}
                elif name=='rotate':data={'start':xyz(args[0]),'end':xyz(args[1]),'degrees':args[2]}
                elif name=='mirror':data={'plane':args[0] if args else kwargs.get('mirrorPlane','XY'),'origin':xyz(args[1]) if len(args)>1 else [0,0,0]}
                else:
                    t=args[0].wrapped.Transformation();data={'matrix':[[t.Value(i,j) for j in range(1,5)] for i in range(1,4)]}
                node(out,name,target=ref(self),**data)
            return out
        return fn
    setattr(cq.Shape,name,wrap())
for name in ['makeBox','makeCylinder','makeCone','makeSphere','makeLoft','extrudeLinear','revolve']:
    old=getattr(cq.Solid,name)
    def wrap(old=old,name=name):
        @functools.wraps(old)
        def fn(*args,**kwargs):
            out=old(*args,**kwargs)
            import inspect
            if name=='extrudeLinear' and isinstance(args[0],cq.Face):
                v={'outerWire':args[0].outerWire(),'innerWires':args[0].innerWires(),'vecNormal':args[1],'taper':args[2] if len(args)>2 else kwargs.get('taper',0)}
            else:
                a=inspect.signature(old).bind(*args,**kwargs);a.apply_defaults();v=a.arguments
            if name in ['makeBox','makeCylinder','makeCone','makeSphere']:
                d={k:xyz(x) if k in ['pnt','dir'] else x for k,x in v.items()}
            elif name=='makeLoft':d={'profiles':[wire(w) for w in v['listOfWire']],'ruled':v['ruled']}
            else:
                d={k:wire(x) if k=='outerWire' else [wire(q) for q in x] if k=='innerWires' else xyz(x) if k in ['vecNormal','axisStart','axisEnd'] else x for k,x in v.items()}
            return node(out,name,**d)
        return fn
    setattr(cq.Solid,name,staticmethod(wrap()))
for name in ['fillet','chamfer']:
    old=getattr(cq.Solid,name)
    def wrap(old=old,name=name):
        @functools.wraps(old)
        def fn(self,*args,**kwargs):
            out=old(self,*args,**kwargs)
            if hasattr(self,'_native_node'):
                es=args[-1];d={'radius':args[0]} if name=='fillet' else {'length':args[0],'length2':args[1]}
                node(out,name,target=ref(self),edges=[edge(e) for e in es],**d)
            return out
        return fn
    setattr(cq.Solid,name,wrap())
    setattr(cq.Compound,name,wrap())


_old_compound=cq.Compound.makeCompound
def _compound(items):
    items=list(items);out=_old_compound(items)
    if items and all(hasattr(s,'_native_node') or s.hashCode() in SHAPES for s in items):
        node(out,'compound',tools=[ref(s) for s in items])
    return out
cq.Compound.makeCompound=staticmethod(_compound)
for _name in ['fuse','cut','intersect']:
    _old=getattr(cq.Compound,_name)
    def _wrapper(old=_old,name=_name):
        def operation(self,*args,**kwargs):
            out=old(self,*args,**kwargs)
            if hasattr(self,'_native_node'):node(out,name,target=ref(self),tools=[ref(s) for s in args])
            return out
        return operation
    setattr(cq.Compound,_name,_wrapper())

_old_find=cq.Workplane._findType
def _find(self,types,searchStack=True,searchParents=True):
    result=_old_find(self,types,searchStack,searchParents)
    if result is not None and types==(cq.Solid,) and not hasattr(result,'_native_node'):
        q=self if searchStack else self.parent
        while q is not None:
            found=[x for x in q.objects if isinstance(x,(cq.Solid,cq.Compound))]
            if found:
                if all(hasattr(x,'_native_node') for x in found):node(result,'compound',tools=[ref(x) for x in found])
                break
            q=q.parent if searchParents else None
    return result
cq.Workplane._findType=_find

def reachable(root):
    visited=set()
    def visit(n):
        if n in visited:return
        visited.add(n);r=NODES[n]
        if 'target' in r:visit(r['target'])
        for t in r.get('tools',[]):visit(t)
    visit(root);return sorted(visited)

def main():
    import build as b
    b.build_body()
    b.build_leg('FL')
    b.build_leg('RL')
    import service_design as sd
    source=dict(b.prototypes)
    def put(key,s):
        b.prototypes[key]=s
        if key in ['shin_inner','shin_outer','thigh_inner','thigh_outer','motor_mount_ring','motor_carrier_1','motor_carrier_-1','shin_clamp_sleeve_37','shin_clamp_sleeve_105']:
            b.prototypes[key+'_right']=s.mirror('XZ')
    for out in [False,True]:
        key='shin_outer' if out else 'shin_inner';put(key,sd.shin(out).translate((0,-16,0)))
        key='thigh_outer' if out else 'thigh_inner';s=sd.thigh_retainer(source[key],out)
        if not out:
            for sign in [-1,1]:s=s.cut(sd.connector_parts(54.4,sign)[3]).cut(sd.cable_space(54.4,sign))
        put(key,s.clean())
    for tag,z in [('37',-30),('105',-105)]:put('shin_clamp_sleeve_'+tag,b.ring(4,2.15,18,58,z,2))
    plate=b.ring(48,30,3,50.5)
    for angle in range(20,380,40):
        x,z=36.5*math.cos(math.radians(angle)),36.5*math.sin(math.radians(angle));plate=plate.cut(b.cyl(1.7,5,(x,49.5,z)))
    for angle in b.POD_TIE_ANGLES:
        x,z=b.POD_TIE_RADIUS*math.cos(math.radians(angle)),b.POD_TIE_RADIUS*math.sin(math.radians(angle));plate=plate.cut(b.cyl(1.7,5,(x,49.5,z)))
    put('motor_mount_ring',plate)
    for front in [-1,1]:put('motor_carrier_'+str(front),sd.hip_port_cut(source['motor_carrier_'+str(front)]))
    for key in ['belly_center_0','body_center_0']:
        s=source[key]
        for front,side in sd.LEGS.values():
            for sign in [-1,1]:
                cut=sd.connector_parts(0,sign)[3].rotate((0,0,0),(0,0,1),-90).translate((-67.3,0,0))
                if front<0:cut=cut.mirror('YZ')
                if side<0:cut=cut.mirror('XZ')
                s=s.cut(cut.translate((front*b.P['hip_x'],side*b.P['roll_y'],0)))
        put(key,s.clean())
    # The end-cap builder reads the unchanged fascia as a cutting tool. Supply
    # its native operation graph instead of importing any source STEP geometry.
    old_import=cq.importers.importStep
    def source_import(path):
        key=Path(path).stem
        if key in source:return cq.Workplane(obj=source[key])
        raise RuntimeError('Untracked STEP use in native capture: '+str(path))
    cq.importers.importStep=source_import
    from body_caps import end_cap
    for key,front in [('body_nose_surround',True),('body_aft_0',False)]:put(key,end_cap(source[key],front))
    cq.importers.importStep=old_import
    put('lidar_lid',b.cyl(27,2,(82,0,74),(0,0,1)))
    # Mirror canonical leg parts once; Fusion will instantiate each shared part.
    leg_keys={p['mesh'] for p in b.parts if p.get('leg')}
    for key in list(b.prototypes):
        if key in leg_keys and not key.endswith('_right'):b.prototypes.setdefault(key+'_right',b.prototypes[key].mirror('XZ'))
    records={}
    for key,s in b.prototypes.items():
        if not hasattr(s,'_native_node'):print('UNRECORDED',key,flush=True);continue
        r=ref(s);records[key]={'root':r,'nodes':len(reachable(r)),'volume_mm3':s.Volume(),'bounds_mm':s.BoundingBox().__dict__|{}}
        records[key]['bounds_mm']={k:records[key]['bounds_mm'][k] for k in ['xmin','xmax','ymin','ymax','zmin','zmax']}
    out=Path(__file__).resolve().parents[1]/'snapshots';out.mkdir(exist_ok=True)
    (out/'source_graph.json').write_text(json.dumps({'schema':1,'nodes':NODES,'parts':records},indent=2))
    print('Captured',len(records),'parts',len(NODES),'nodes',flush=True)
if __name__=='__main__':main()
