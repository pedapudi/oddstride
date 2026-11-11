"""Native Fusion feature authoring engine; no mesh or BRep imports.

Executed inside Fusion through the MCP script API. The input recipe contains
analytic primitive dimensions and planar sketch curves captured from the source.
This module is not marked validated until its exports pass the migration audit.
"""
import math,json,re
import adsk.core as core
import adsk.fusion as fusion

MM=.1

def vec(a):return core.Vector3D.create(*a)
def pt(a):return core.Point3D.create(*(float(x)*MM for x in a))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(a):return math.sqrt(dot(a,a))
def unit(a):return [x/norm(a) for x in a]
def add(a,b):return [x+y for x,y in zip(a,b)]
def mul(a,k):return [x*k for x in a]
def collection(items):
    c=core.ObjectCollection.create()
    for i in items:c.add(i)
    return c

def safe(s):return re.sub('[^A-Za-z0-9_]','_',s)

class Builder:
    def __init__(self,design,component,part_id,graph):
        self.design=design;self.c=component;self.id=part_id;self.nodes={n['id']:n for n in graph};self.cache={};self.counter=0;self.features=[]
    def parameter(self,label,value,units='mm'):
        name=safe(self.id+'_'+label)
        p=self.design.userParameters.itemByName(name)
        if not p:p=self.design.userParameters.add(name,core.ValueInput.createByString(f'{value:.12g} {units}'),units,'Native source dimension; '+self.id)
        return core.ValueInput.createByString(name)
    def named(self,feature,name):
        feature.name=name;self.features.append(feature)
        return feature
    def plane(self,origin,normal,label):
        n=unit(normal);planes=[self.c.yZConstructionPlane,self.c.xZConstructionPlane,self.c.xYConstructionPlane]
        i=max(range(3),key=lambda k:abs(n[k]))
        if abs(n[i])>1-1e-7:
            base=planes[i];bn=base.geometry.normal;offset=dot(origin,[bn.x,bn.y,bn.z])
            if abs(offset)<1e-8:return base
            inp=self.c.constructionPlanes.createInput();inp.setByOffset(base,self.parameter(label+'_offset',offset));p=self.c.constructionPlanes.add(inp);p.name=label+' datum';return p
        # Parametric plane through an editable 3D datum sketch, never setByPlane.
        datum=self.c.sketches.add(self.c.xYConstructionPlane);datum.name=label+' orientation datum';datum.is3D=True
        trial=[1,0,0] if abs(n[0])<.8 else [0,1,0]
        u=unit([trial[1]*n[2]-trial[2]*n[1],trial[2]*n[0]-trial[0]*n[2],trial[0]*n[1]-trial[1]*n[0]])
        v=[n[1]*u[2]-n[2]*u[1],n[2]*u[0]-n[0]*u[2],n[0]*u[1]-n[1]*u[0]]
        points=[datum.sketchPoints.add(pt(p)) for p in [origin,add(origin,mul(u,10)),add(origin,mul(v,10))]]
        inp=self.c.constructionPlanes.createInput();inp.setByThreePoints(*points);p=self.c.constructionPlanes.add(inp);p.name=label+' datum';datum.isVisible=False;return p
    def sketch(self,profile,label):
        s=self.c.sketches.add(self.plane(profile['origin'],profile['normal'],label));s.name=label+' profile'
        curves=s.sketchCurves
        def q(a):return s.modelToSketchSpace(pt(a))
        s.isComputeDeferred=True
        for e in profile['edges']:
            if e['kind']=='line':curves.sketchLines.addByTwoPoints(q(e['start']),q(e['end']))
            elif e['kind']=='circle':curves.sketchCircles.addByCenterRadius(q(e['center']),e['radius']*MM)
            elif e['kind']=='arc':curves.sketchArcs.addByThreePoints(q(e['start']),q(e['mid']),q(e['end']))
            elif e['kind']=='spline':curves.sketchFittedSplines.add(collection(q(p) for p in e['points']))
            else:raise ValueError('Unsupported sketch curve '+e['kind'])
        s.isComputeDeferred=False
        if s.profiles.count!=1:raise RuntimeError(f'{label}: expected one closed sketch profile, got {s.profiles.count}')
        return s
    def circle(self,origin,normal,radius,label):
        s=self.c.sketches.add(self.plane(origin,normal,label));s.name=label+' profile'
        p=s.modelToSketchSpace(pt(origin));c=s.sketchCurves.sketchCircles.addByCenterRadius(p,radius*MM)
        d=s.sketchDimensions.addDiameterDimension(c,core.Point3D.create(p.x+radius*MM*1.3,p.y,0));d.parameter.expression=self.parameter(label+'_diameter',radius*2).stringValue
        return s
    def extrude(self,s,distance,label):
        inp=self.c.features.extrudeFeatures.createInput(s.profiles.item(0),fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(False,self.parameter(label+'_depth',distance))
        f=self.named(self.c.features.extrudeFeatures.add(inp),label);s.isVisible=False
        return [f.bodies.item(i) for i in range(f.bodies.count)]
    def copy(self,bodies,label):
        f=self.named(self.c.features.copyPasteBodies.add(collection(bodies)),label)
        return [f.bodies.item(i) for i in range(f.bodies.count)]
    def boolean(self,target,tools,operation,label):
        # Original bodies remain available to other feature branches. Cleanup
        # removes intermediate bodies only after the final native result exists.
        result=self.copy(target,label+' target')
        if len(result)!=1:raise RuntimeError(label+': multiple target bodies require an explicit reviewed union')
        if not tools:return result
        inp=self.c.features.combineFeatures.createInput(result[0],collection(tools));inp.operation=operation;inp.isKeepToolBodies=True
        f=self.named(self.c.features.combineFeatures.add(inp),label)
        return result
    def transform(self,bodies,matrix,label):
        result=self.copy(bodies,label+' source');inp=self.c.features.moveFeatures.createInput2(collection(result));inp.defineAsFreeMove(matrix)
        self.named(self.c.features.moveFeatures.add(inp),label);return result
    def build(self,key):
        if key in self.cache:return self.cache[key]
        n=self.nodes[key];op=n['op'];label=f'{key:04d} {op}'
        if op=='makeBox':
            origin=n['pnt'];L,W,H=n['length'],n['width'],n['height']
            if n['dir']!=[0,0,1]:raise ValueError('Review oriented box '+label)
            points=[origin,add(origin,[L,0,0]),add(origin,[L,W,0]),add(origin,[0,W,0])]
            profile={'origin':origin,'normal':[0,0,1],'edges':[{'kind':'line','start':a,'end':b} for a,b in zip(points,points[1:]+points[:1])]}
            s=self.sketch(profile,label);result=self.extrude(s,H,label+' stock')
        elif op=='makeCylinder':
            if abs(n['angleDegrees']-360)>1e-7:raise ValueError('Review partial cylinder '+label)
            s=self.circle(n['pnt'],n['dir'],n['radius'],label)
            normal=s.referencePlane.geometry.normal;direction=dot(n['dir'],[normal.x,normal.y,normal.z])
            result=self.extrude(s,n['height']*(1 if direction>0 else -1),label+' cylinder')
        elif op=='makeCone':
            if min(n['radius1'],n['radius2'])<=0:raise ValueError('Review cone apex '+label)
            sketches=[self.circle(n['pnt'],n['dir'],n['radius1'],label+' base'),self.circle(add(n['pnt'],mul(n['dir'],n['height'])),n['dir'],n['radius2'],label+' tip')]
            inp=self.c.features.loftFeatures.createInput(fusion.FeatureOperations.NewBodyFeatureOperation)
            for s in sketches:inp.loftSections.add(s.profiles.item(0))
            f=self.named(self.c.features.loftFeatures.add(inp),label+' conical loft');result=[f.bodies.item(0)]
            for s in sketches:s.isVisible=False
        elif op=='extrudeLinear':
            if n['innerWires']:raise ValueError('Review nested extruded profiles '+label)
            if n['taper']!=0:raise ValueError('Review tapered extrusion '+label)
            s=self.sketch(n['outerWire'],label);normal=s.referencePlane.geometry.normal
            distance=dot(n['vecNormal'],[normal.x,normal.y,normal.z]);result=self.extrude(s,distance,label+' extrusion')
        elif op=='makeLoft':
            sketches=[self.sketch(p,label+' section '+str(i)) for i,p in enumerate(n['profiles'])]
            inp=self.c.features.loftFeatures.createInput(fusion.FeatureOperations.NewBodyFeatureOperation)
            for s in sketches:inp.loftSections.add(s.profiles.item(0))
            f=self.named(self.c.features.loftFeatures.add(inp),label+' loft');result=[f.bodies.item(i) for i in range(f.bodies.count)]
            for s in sketches:s.isVisible=False
        elif op=='compound':result=[b for t in n['tools'] for b in self.build(t)]
        elif op in ['cut','fuse','intersect']:
            target=self.build(n['target']);tools=[b for t in n['tools'] for b in self.build(t)]
            operation={'cut':fusion.FeatureOperations.CutFeatureOperation,'fuse':fusion.FeatureOperations.JoinFeatureOperation,'intersect':fusion.FeatureOperations.IntersectFeatureOperation}[op]
            result=self.boolean(target,tools,operation,label)
        elif op=='extractSolid':
            bodies=self.build(n['target']);result=[bodies[n['index']]]
        elif op in ['translate','rotate','moved']:
            m=core.Matrix3D.create()
            if op=='translate':m.translation=vec(mul(n['vector'],MM))
            elif op=='rotate':m.setToRotation(math.radians(n['degrees']),vec([b-a for a,b in zip(n['start'],n['end'])]),pt(n['start']))
            else:
                values=[]
                for row in n['matrix']:values+=row[:3]+[row[3]*MM]
                values+=[0,0,0,1];m.setWithArray(values)
            result=self.transform(self.build(n['target']),m,label)
        elif op=='mirror':
            if n['origin']!=[0,0,0]:raise ValueError('Review offset mirror plane '+label)
            plane={'XY':self.c.xYConstructionPlane,'XZ':self.c.xZConstructionPlane,'YZ':self.c.yZConstructionPlane}[n['plane']]
            inp=self.c.features.mirrorFeatures.createInput(collection(self.build(n['target'])),plane)
            f=self.named(self.c.features.mirrorFeatures.add(inp),label+' handed part');result=[f.bodies.item(i) for i in range(f.bodies.count)]
        elif op=='fillet':
            result=self.copy(self.build(n['target']),label+' stock');edges=[]
            for expected in n['edges']:
                best=None;error=float('inf')
                for body in result:
                    for e in body.edges:
                        if not e.startVertex or not e.endVertex:continue
                        a=e.startVertex.geometry;b=e.endVertex.geometry
                        d=min(a.distanceTo(pt(expected['start']))+b.distanceTo(pt(expected['end'])),a.distanceTo(pt(expected['end']))+b.distanceTo(pt(expected['start'])))+abs(e.length-expected['length']*MM)
                        if d<error:best,error=e,d
                if best is None or error>.015:raise RuntimeError(label+' could not identify fillet edge within 0.15 mm')
                if best not in edges:edges.append(best)
            inp=self.c.features.filletFeatures.createInput();inp.addConstantRadiusEdgeSet(collection(edges),self.parameter(label+'_radius',n['radius']),True)
            self.named(self.c.features.filletFeatures.add(inp),label+' edge rounds')
        else:raise NotImplementedError('Native operation requires reviewed implementation: '+op)
        self.cache[key]=result;return result
    def finish(self,root):
        result=self.build(root)
        if len(result)!=1:raise RuntimeError('Manufactured part must have one final body')
        final=result[0];final.name=self.id
        # Remove intermediate construction bodies via native timeline features.
        extras=[b for b in self.c.bRepBodies if b!=final]
        for b in extras:self.c.features.removeFeatures.add(b)
        final.isVisible=True
        return final

def create_part(design,part_id,graph,root):
    occ=design.rootComponent.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name=part_id.replace('_',' ');c.partNumber=part_id
    b=Builder(design,c,part_id,graph);body=b.finish(root)
    return c,body

def run(_context: str):
    app=core.Application.get();design=fusion.Design.cast(app.activeProduct)
    assert app.activeDocument.name.startswith("Tinfox - Native Master Assembly"),"Wrong active document"
    graph={'nodes': [{'id': 0, 'op': 'makeCylinder', 'radius': 48, 'height': 3, 'pnt': [0.0, 50.5, 0.0], 'dir': [0.0, 1.0, 0.0], 'angleDegrees': 360}, {'id': 1, 'op': 'makeCylinder', 'radius': 30, 'height': 5, 'pnt': [0.0, 49.5, 0.0], 'dir': [0.0, 1.0, 0.0], 'angleDegrees': 360}, {'id': 2, 'op': 'cut', 'target': 0, 'tools': [1]}, {'id': 3, 'op': 'makeCylinder', 'radius': 1.7, 'height': 5, 'pnt': [34.29878065868566, 49.5, 12.483735231386907], 'dir': [0.0, 1.0, 0.0], 'angleDegrees': 360}, {'id': 4, 'op': 'cut', 'target': 2, 'tools': [3]}, {'id': 5, 'op': 'makeCylinder', 'radius': 1.7, 'height': 5, 'pnt': [18.250000000000004, 49.5, 31.60992723813201], 'dir': [0.0, 1.0, 0.0], 'angleDegrees': 360}, {'id': 6, 'op': 'cut', 'target': 4, 'tools': [5]}, {'id': 7, 'op': 'makeCylinder', 'radius': 1.7, 'height': 5, 'pnt': [-6.338158484842956, 49.5, 35.94548298494559], 'dir': [0.0, 1.0, 0.0], 'angleDegrees': 360}, {'id': 8, 'op': 'cut', 'target': 6, 'tools': [7]}, {'id': 9, 'op': 'makeCylinder', 'radius': 1.7, 'height': 5, 'pnt': [-27.960622173842694, 49.5, 23.46174775355869], 'dir': [0.0, 1.0, 0.0], 'angleDegrees': 360}, {'id': 10, 'op': 'cut', 'target': 8, 'tools': [9]}, {'id': 11, 'op': 'makeCylinder', 'radius': 1.7, 'height': 5, 'pnt': [-36.5, 49.5, 4.469960816887839e-15], 'dir': [0.0, 1.0, 0.0], 'angleDegrees': 360}, {'id': 12, 'op': 'cut', 'target': 10, 'tools': [11]}, {'id': 13, 'op': 'makeCylinder', 'radius': 1.7, 'height': 5, 'pnt': [-27.960622173842697, 49.5, -23.461747753558683], 'dir': [0.0, 1.0, 0.0], 'angleDegrees': 360}, {'id': 14, 'op': 'cut', 'target': 12, 'tools': [13]}, {'id': 15, 'op': 'makeCylinder', 'radius': 1.7, 'height': 5, 'pnt': [-6.338158484842957, 49.5, -35.94548298494559], 'dir': [0.0, 1.0, 0.0], 'angleDegrees': 360}, {'id': 16, 'op': 'cut', 'target': 14, 'tools': [15]}, {'id': 17, 'op': 'makeCylinder', 'radius': 1.7, 'height': 5, 'pnt': [18.250000000000004, 49.5, -31.60992723813201], 'dir': [0.0, 1.0, 0.0], 'angleDegrees': 360}, {'id': 18, 'op': 'cut', 'target': 16, 'tools': [17]}, {'id': 19, 'op': 'makeCylinder', 'radius': 1.7, 'height': 5, 'pnt': [34.29878065868566, 49.5, -12.483735231386904], 'dir': [0.0, 1.0, 0.0], 'angleDegrees': 360}, {'id': 20, 'op': 'cut', 'target': 18, 'tools': [19]}, {'id': 21, 'op': 'makeCylinder', 'radius': 1.7, 'height': 5, 'pnt': [2.6636067881454934e-15, 49.5, 43.5], 'dir': [0.0, 1.0, 0.0], 'angleDegrees': 360}, {'id': 22, 'op': 'cut', 'target': 20, 'tools': [21]}, {'id': 23, 'op': 'makeCylinder', 'radius': 1.7, 'height': 5, 'pnt': [-37.67210506462308, 49.5, -21.750000000000004], 'dir': [0.0, 1.0, 0.0], 'angleDegrees': 360}, {'id': 24, 'op': 'cut', 'target': 22, 'tools': [23]}, {'id': 25, 'op': 'makeCylinder', 'radius': 1.7, 'height': 5, 'pnt': [37.67210506462307, 49.5, -21.750000000000018], 'dir': [0.0, 1.0, 0.0], 'angleDegrees': 360}, {'id': 26, 'op': 'cut', 'target': 24, 'tools': [25]}], 'root': 26, 'volume_mm3': 12905.536957240713}
    group=next(o.component for o in design.rootComponent.occurrences if o.component.name=="Shared leg designs")
    occ=group.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name="Knee motor stator plate";c.partNumber="motor_mount_ring"
    builder=Builder(design,c,"motor_mount_ring",graph["nodes"]);body=builder.finish(graph["root"])
    print(json.dumps({"part":"motor_mount_ring","volume_mm3":body.physicalProperties.volume*1000,"source_volume_mm3":graph["volume_mm3"],"sketches":c.sketches.count,"features":len(builder.features),"body_count":c.bRepBodies.count,"timeline":design.timeline.count}))
