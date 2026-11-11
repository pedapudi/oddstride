"""Native Fusion feature authoring engine; no mesh or BRep imports.

Executed inside Fusion through the MCP script API. The input recipe contains
analytic primitive dimensions and planar sketch curves captured from the source.
This module is not marked validated until its exports pass the migration audit.
"""
import math,json,re,time
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
class DiagnosticMismatch(RuntimeError):pass

class Builder:
    def __init__(self,design,component,part_id,graph):
        self.design=design;self.c=component;self.id=part_id;self.nodes={n['id']:n for n in graph};self.cache={};self.counter=0;self.features=[];self.usage={};self.timings=[];self.last_feature_time=time.perf_counter();self.expected_nodes={};self.diagnostic_trace=[]
    def check_node(self,key,bodies):
        expected=self.expected_nodes.get(str(key))
        if expected is None:return
        actual=sum(b.volume for b in bodies)*1000
        error=abs(actual-expected['volume_mm3'])/max(abs(expected['volume_mm3']),1e-9)
        record={'node':key,'operation':self.nodes[key]['op'],'expected_volume_mm3':expected['volume_mm3'],'native_volume_mm3':actual,'relative_error':error,'native_bodies':len(bodies)}
        self.diagnostic_trace.append(record)
        if abs(actual-expected['volume_mm3'])>max(.1,abs(expected['volume_mm3'])*.005):raise DiagnosticMismatch(json.dumps(record))
    def parameter(self,label,value,units='mm'):
        name=safe(self.id+'_'+label)
        p=self.design.userParameters.itemByName(name)
        if not p:p=self.design.userParameters.add(name,core.ValueInput.createByString(f'{value:.12g} {units}'),units,'Native source dimension; '+self.id)
        return core.ValueInput.createByString(name)
    def named(self,feature,name):
        feature.name=name;self.features.append(feature)
        now=time.perf_counter();self.timings.append({'feature':name,'seconds_since_previous_feature':now-self.last_feature_time});self.last_feature_time=now
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
    def boolean(self,target,tools,operation,label,copy_target=True,keep_tools=True):
        targets=self.copy(target,label+' target') if copy_target else list(target)
        if not tools:return targets
        if not targets:return self.copy(tools,label+' union stock') if operation==fusion.FeatureOperations.JoinFeatureOperation else []
        if operation==fusion.FeatureOperations.JoinFeatureOperation:
            used_tools=(self.copy(tools,label+' reusable tools') if keep_tools else list(tools))+targets[1:]
            groups=[(targets[0],used_tools)]
        else:
            groups=[(body,self.copy(tools,label+' reusable tools '+str(i)) if keep_tools or i<len(targets)-1 else list(tools)) for i,body in enumerate(targets)]
        result=[]
        for body,used_tools in groups:
            before=list(self.c.bRepBodies);inputs=[body]+used_tools
            inp=self.c.features.combineFeatures.createInput(body,collection(used_tools));inp.operation=operation;inp.isKeepToolBodies=False
            try:self.named(self.c.features.combineFeatures.add(inp),label)
            except RuntimeError as error:raise RuntimeError('Native operation '+label+' failed: '+str(error)) from error
            # Cuts can split a solid, and joins can retain disconnected stock.
            # Return every surviving input/result body, never just the first.
            result.extend(b for b in self.c.bRepBodies if b not in before or b in inputs)
        return result
    def transform(self,bodies,matrix,label,copy_source=True):
        result=self.copy(bodies,label+' source') if copy_source else bodies;inp=self.c.features.moveFeatures.createInput2(collection(result));inp.defineAsFreeMove(matrix)
        self.named(self.c.features.moveFeatures.add(inp),label);return result
    def build(self,key):
        self.usage[key]=self.usage.get(key,1)-1
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
        elif op=='makeSphere':
            if n['dir']!=[0,0,1]:raise ValueError('Review oriented sphere '+label)
            center=n['pnt'];r=n['radius'];a,b=[math.radians(n[k]) for k in ['angleDegrees1','angleDegrees2']]
            def polar(t):return add(center,[r*math.cos(t),0,r*math.sin(t)])
            start,end,mid=polar(a),polar(b),polar((a+b)/2)
            low=add(center,[0,0,r*math.sin(a)]);high=add(center,[0,0,r*math.sin(b)])
            edges=[{'kind':'arc','start':start,'mid':mid,'end':end}]
            for u,vv in [(end,high),(high,low),(low,start)]:
                if norm([x-y for x,y in zip(u,vv)])>1e-7:edges.append({'kind':'line','start':u,'end':vv})
            sk=self.sketch({'origin':center,'normal':[0,1,0],'edges':edges},label)
            p1=sk.modelToSketchSpace(pt(add(center,[0,0,-r*1.1])));p2=sk.modelToSketchSpace(pt(add(center,[0,0,r*1.1])))
            axis=sk.sketchCurves.sketchLines.addByTwoPoints(p1,p2);axis.isConstruction=True
            inp=self.c.features.revolveFeatures.createInput(sk.profiles.item(0),axis,fusion.FeatureOperations.NewBodyFeatureOperation)
            inp.setAngleExtent(False,self.parameter(label+'_sweep',n['angleDegrees3'],'deg'))
            f=self.named(self.c.features.revolveFeatures.add(inp),label+' spherical revolve');result=[f.bodies.item(0)];sk.isVisible=False
        elif op=='extrudeLinear':
            if n['innerWires']:raise ValueError('Review nested extruded profiles '+label)
            if n['taper']!=0:raise ValueError('Review tapered extrusion '+label)
            s=self.sketch(n['outerWire'],label);normal=s.referencePlane.geometry.normal
            distance=dot(n['vecNormal'],[normal.x,normal.y,normal.z]);result=self.extrude(s,distance,label+' extrusion')
        elif op=='makeLoft':
            sketches=[self.sketch(p,label+' section '+str(i)) for i,p in enumerate(n['profiles'])]
            groups=[sketches] if not n['ruled'] else [sketches[i:i+2] for i in range(len(sketches)-1)]
            result=[]
            for i,group in enumerate(groups):
                inp=self.c.features.loftFeatures.createInput(fusion.FeatureOperations.NewBodyFeatureOperation)
                for sk in group:inp.loftSections.add(sk.profiles.item(0))
                f=self.named(self.c.features.loftFeatures.add(inp),label+' loft section '+str(i));segment=[f.bodies.item(j) for j in range(f.bodies.count)]
                if result:result=self.boolean(result,segment,fusion.FeatureOperations.JoinFeatureOperation,label+' join ruled sections',False,False)
                else:result=segment
            for sk in sketches:sk.isVisible=False
        elif op=='ruledAnnularRevolve':
            axis=n['axis'];radial=(axis+2)%3;normal_axis=next(i for i in range(3) if i not in [axis,radial]);normal=[0,0,0];normal[normal_axis]=1
            def offset(center,radius):
                p=list(center);p[radial]+=radius;return p
            points=[offset(c,r) for c,r in zip(n['centers'],n['outer_radii'])]+[offset(c,r) for c,r in reversed(list(zip(n['centers'],n['inner_radii'])))]
            profile={'origin':n['centers'][0],'normal':normal,'edges':[{'kind':'line','start':a,'end':b} for a,b in zip(points,points[1:]+points[:1])]}
            sk=self.sketch(profile,label+' shoulder wall')
            line=sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(pt(n['centers'][0])),sk.modelToSketchSpace(pt(n['centers'][-1])));line.isConstruction=True
            inp=self.c.features.revolveFeatures.createInput(sk.profiles.item(0),line,fusion.FeatureOperations.NewBodyFeatureOperation);inp.setAngleExtent(False,core.ValueInput.createByString('360 deg'))
            f=self.named(self.c.features.revolveFeatures.add(inp),label+' revolved shoulder cuff');result=[f.bodies.item(0)];sk.isVisible=False
        elif op=='circularCutPattern':
            target=self.build(n['target']);result=self.copy(target,label+' stock') if self.usage.get(n['target'],0)>0 else target
            assert len(result)==1
            seed=n['seed'];sk=self.circle(seed['pnt'],seed['dir'],seed['radius'],label+' bolt-circle seed')
            normal=sk.referencePlane.geometry.normal;distance=seed['height']*(1 if dot(seed['dir'],[normal.x,normal.y,normal.z])>0 else -1)
            inp=self.c.features.extrudeFeatures.createInput(sk.profiles.item(0),fusion.FeatureOperations.CutFeatureOperation)
            inp.setDistanceExtent(False,self.parameter(label+'_hole_depth',distance));inp.participantBodies=result
            hole=self.named(self.c.features.extrudeFeatures.add(inp),label+' first clearance hole');sk.isVisible=False
            axis=[self.c.xConstructionAxis,self.c.yConstructionAxis,self.c.zConstructionAxis][n['axis']]
            inp=self.c.features.circularPatternFeatures.createInput(collection([hole]),axis)
            inp.quantity=self.parameter(label+'_hole_count',n['quantity'],'');inp.totalAngle=core.ValueInput.createByString('360 deg');inp.isSymmetric=False
            self.named(self.c.features.circularPatternFeatures.add(inp),label+' '+str(n['quantity'])+' holes around motor axis')
        elif op=='compound':
            result=[]
            for child in n['tools']:
                bodies=self.build(child);result.extend(self.copy(bodies,label+' shared stock') if self.usage.get(child,0)>0 else bodies)
        elif op in ['cut','fuse','intersect']:
            outer=self.nodes[n['target']];inner=self.nodes[n['tools'][0]] if len(n['tools'])==1 else {}
            annular=False
            if op=='cut' and outer['op']=='makeCylinder' and inner.get('op')=='makeCylinder' and outer['dir']==inner['dir'] and inner['radius']<outer['radius']:
                axis=unit(outer['dir']);delta=[b-a for a,b in zip(outer['pnt'],inner['pnt'])];along=dot(delta,axis);lateral=[v-along*a for v,a in zip(delta,axis)]
                annular=norm(lateral)<1e-7 and along<=1e-7 and along+inner['height']>=outer['height']-1e-7 and outer['angleDegrees']==360 and inner['angleDegrees']==360
            if annular:
                sk=self.circle(outer['pnt'],axis,outer['radius'],label+' annulus outer')
                center=sk.modelToSketchSpace(pt(outer['pnt']));hole=sk.sketchCurves.sketchCircles.addByCenterRadius(center,inner['radius']*MM)
                sk.geometricConstraints.addCoincident(hole.centerSketchPoint,sk.sketchCurves.sketchCircles.item(0).centerSketchPoint)
                dim=sk.sketchDimensions.addDiameterDimension(hole,core.Point3D.create(center.x+inner['radius']*MM*1.3,center.y,0));dim.parameter.expression=self.parameter(label+'_bore',inner['radius']*2).stringValue
                profile=next(sk.profiles.item(i) for i in range(sk.profiles.count) if sk.profiles.item(i).profileLoops.count==2)
                inp=self.c.features.extrudeFeatures.createInput(profile,fusion.FeatureOperations.NewBodyFeatureOperation);normal=sk.referencePlane.geometry.normal
                signed=outer['height']*(1 if dot(axis,[normal.x,normal.y,normal.z])>0 else -1);inp.setDistanceExtent(False,self.parameter(label+'_thickness',signed))
                f=self.named(self.c.features.extrudeFeatures.add(inp),label+' annular extrusion');result=[f.bodies.item(0)];sk.isVisible=False
                self.check_node(key,result);self.cache[key]=result;return result
            target=self.build(n['target']);tools=[b for t in n['tools'] for b in self.build(t)]
            operation={'cut':fusion.FeatureOperations.CutFeatureOperation,'fuse':fusion.FeatureOperations.JoinFeatureOperation,'intersect':fusion.FeatureOperations.IntersectFeatureOperation}[op]
            result=self.boolean(target,tools,operation,label,self.usage.get(n['target'],0)>0,any(self.usage.get(t,0)>0 for t in n['tools']))
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
            result=self.transform(self.build(n['target']),m,label,self.usage.get(n['target'],0)>0)
        elif op=='mirror':
            if n['origin']!=[0,0,0]:raise ValueError('Review offset mirror plane '+label)
            plane={'XY':self.c.xYConstructionPlane,'XZ':self.c.xZConstructionPlane,'YZ':self.c.yZConstructionPlane}[n['plane']]
            source=self.build(n['target']);before=list(self.c.bRepBodies)
            inp=self.c.features.mirrorFeatures.createInput(collection(source),plane);inp.isCombine=False
            self.named(self.c.features.mirrorFeatures.add(inp),label+' handed part')
            result=[body for body in self.c.bRepBodies if body not in before]
            assert len(result)==len(source),(label,'Native mirror did not create the expected separate bodies')
        elif op=='fillet':
            result=self.copy(self.build(n['target']),label+' stock') if self.usage.get(n['target'],0)>1 else self.build(n['target']);edges=[]
            for expected in n['edges']:
                best=None;error=float('inf')
                for body in result:
                    for e in body.edges:
                        geometry=e.geometry
                        if expected['kind']=='circle' and hasattr(geometry,'center') and hasattr(geometry,'radius'):
                            d=geometry.center.distanceTo(pt(expected['center']))+abs(geometry.radius-expected['radius']*MM)+abs(e.length-expected['length']*MM)
                        elif e.startVertex and e.endVertex:
                            a=e.startVertex.geometry;b=e.endVertex.geometry
                            d=min(a.distanceTo(pt(expected['start']))+b.distanceTo(pt(expected['end'])),a.distanceTo(pt(expected['end']))+b.distanceTo(pt(expected['start'])))+abs(e.length-expected['length']*MM)
                        else:continue
                        if d<error:best,error=e,d
                if best is None or error>.015:raise RuntimeError(label+' could not identify fillet edge within 0.15 mm')
                if best not in edges:edges.append(best)
            inp=self.c.features.filletFeatures.createInput();inp.addConstantRadiusEdgeSet(collection(edges),self.parameter(label+'_radius',n['radius']),True)
            self.named(self.c.features.filletFeatures.add(inp),label+' edge rounds')
        else:raise NotImplementedError('Native operation requires reviewed implementation: '+op)
        self.check_node(key,result);self.cache[key]=result;return result
    def finish(self,root):
        visited=set()
        def count(k):
            if k in visited:return
            visited.add(k);n=self.nodes[k]
            for child in ([n['target']] if 'target' in n else [])+n.get('tools',[]):
                self.usage[child]=self.usage.get(child,0)+1;count(child)
        count(root)
        result=self.build(root)
        if len(result)!=1:raise RuntimeError('Manufactured part must have one final body')
        final=result[0];final.name=self.id
        # Remove intermediate construction bodies via native timeline features.
        extras=[b for b in self.c.bRepBodies if b!=final and b.isValid]
        for b in extras:self.named(self.c.features.removeFeatures.add(b),'Remove consumed construction stock')
        final.isVisible=True
        return final

def create_part(design,part_id,graph,root):
    occ=design.rootComponent.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name=part_id.replace('_',' ');c.partNumber=part_id
    b=Builder(design,c,part_id,graph);body=b.finish(root)
    return c,body


def run(_context: str):
    import tempfile,os,time
    app=core.Application.get();d=fusion.Design.cast(app.activeProduct)
    assert app.activeDocument.name.startswith('Tinfox - Native Master Assembly'),'Wrong active document'
    graph={'root': 964, 'nodes': [{'id': 964, 'op': 'intersect', 'target': 951, 'tools': [957]}, {'id': 951, 'op': 'cut', 'target': 949, 'tools': [950]}, {'id': 949, 'op': 'fuse', 'target': 935, 'tools': [948]}, {'id': 935, 'op': 'cut', 'target': 933, 'tools': [934]}, {'id': 933, 'op': 'fuse', 'target': 919, 'tools': [932]}, {'id': 919, 'op': 'cut', 'target': 917, 'tools': [918]}, {'id': 917, 'op': 'cut', 'target': 915, 'tools': [916]}, {'id': 915, 'op': 'cut', 'target': 913, 'tools': [914]}, {'id': 913, 'op': 'cut', 'target': 911, 'tools': [912]}, {'id': 911, 'op': 'cut', 'target': 909, 'tools': [910]}, {'id': 909, 'op': 'cut', 'target': 907, 'tools': [908]}, {'id': 907, 'op': 'cut', 'target': 905, 'tools': [906]}, {'id': 905, 'op': 'cut', 'target': 903, 'tools': [904]}, {'id': 903, 'op': 'cut', 'target': 901, 'tools': [902]}, {'id': 901, 'op': 'fuse', 'target': 893, 'tools': [900]}, {'id': 893, 'op': 'cut', 'target': 891, 'tools': [892]}, {'id': 891, 'op': 'fuse', 'target': 883, 'tools': [890]}, {'id': 883, 'op': 'cut', 'target': 881, 'tools': [882]}, {'id': 881, 'op': 'fuse', 'target': 879, 'tools': [880]}, {'id': 879, 'op': 'cut', 'target': 877, 'tools': [878]}, {'id': 877, 'op': 'fuse', 'target': 875, 'tools': [876]}, {'id': 875, 'op': 'cut', 'target': 873, 'tools': [874]}, {'id': 873, 'op': 'fuse', 'target': 871, 'tools': [872]}, {'id': 871, 'op': 'cut', 'target': 869, 'tools': [870]}, {'id': 869, 'op': 'fuse', 'target': 867, 'tools': [868]}, {'id': 867, 'op': 'fuse', 'target': 845, 'tools': [866]}, {'id': 845, 'op': 'cut', 'target': 837, 'tools': [844]}, {'id': 837, 'op': 'cut', 'target': 829, 'tools': [836]}, {'id': 829, 'op': 'cut', 'target': 821, 'tools': [828]}, {'id': 821, 'op': 'fillet', 'target': 965, 'edges': [{'start': [-130.0, -103.0, -19.0], 'end': [-130.0, -103.0, 35.0], 'length': 54.0, 'kind': 'line'}, {'start': [-130.0, -103.0, 35.0], 'end': [-130.0, -101.0, 35.0], 'length': 2.0, 'kind': 'line'}, {'start': [-130.0, -101.0, 35.0], 'end': [-130.0, -101.0, -19.0], 'length': 54.0, 'kind': 'line'}, {'start': [-130.0, -101.0, -19.0], 'end': [-130.0, -103.0, -19.0], 'length': 2.0, 'kind': 'line'}, {'start': [130.0, -103.0, 35.0], 'end': [130.0, -103.0, -19.0], 'length': 54.0, 'kind': 'line'}, {'start': [130.0, -101.0, 35.0], 'end': [130.0, -103.0, 35.0], 'length': 2.0, 'kind': 'line'}, {'start': [130.0, -101.0, -19.0], 'end': [130.0, -101.0, 35.0], 'length': 54.0, 'kind': 'line'}, {'start': [130.0, -103.0, -19.0], 'end': [130.0, -101.0, -19.0], 'length': 2.0, 'kind': 'line'}, {'start': [-130.0, -103.0, -19.0], 'end': [130.0, -103.0, -19.0], 'length': 260.0, 'kind': 'line'}, {'start': [130.0, -103.0, 35.0], 'end': [-130.0, -103.0, 35.0], 'length': 260.0, 'kind': 'line'}, {'start': [130.0, -101.0, -19.0], 'end': [-130.0, -101.0, -19.0], 'length': 260.0, 'kind': 'line'}, {'start': [-130.0, -101.0, 35.0], 'end': [130.0, -101.0, 35.0], 'length': 260.0, 'kind': 'line'}], 'radius': 0.7, 'source_translation_folded': 820}, {'id': 965, 'op': 'makeBox', 'length': 260, 'width': 2, 'height': 54, 'pnt': [-130.0, -103.0, -19.0], 'dir': [0.0, 0.0, 1.0], 'source_translation_folded': 815}, {'id': 828, 'op': 'fillet', 'target': 826, 'edges': [{'start': [-119.0, -105.0, 26.0], 'end': [-119.0, -99.0, 26.0], 'length': 6.0, 'kind': 'line'}, {'start': [-119.0, -99.0, -26.0], 'end': [-119.0, -105.0, -26.0], 'length': 6.0, 'kind': 'line'}, {'start': [-63.0, -99.0, 26.0], 'end': [-63.0, -105.0, 26.0], 'length': 6.0, 'kind': 'line'}, {'start': [-63.0, -105.0, -26.0], 'end': [-63.0, -99.0, -26.0], 'length': 6.0, 'kind': 'line'}], 'radius': 4}, {'id': 826, 'op': 'makeBox', 'length': 56, 'width': 6, 'height': 52, 'pnt': [-119.0, -105.0, -26.0], 'dir': [0.0, 0.0, 1.0], 'source_translation_folded': 822}, {'id': 836, 'op': 'fillet', 'target': 834, 'edges': [{'start': [63.0, -105.0, 26.0], 'end': [63.0, -99.0, 26.0], 'length': 6.0, 'kind': 'line'}, {'start': [63.0, -99.0, -26.0], 'end': [63.0, -105.0, -26.0], 'length': 6.0, 'kind': 'line'}, {'start': [119.0, -99.0, 26.0], 'end': [119.0, -105.0, 26.0], 'length': 6.0, 'kind': 'line'}, {'start': [119.0, -105.0, -26.0], 'end': [119.0, -99.0, -26.0], 'length': 6.0, 'kind': 'line'}], 'radius': 4}, {'id': 834, 'op': 'makeBox', 'length': 56, 'width': 6, 'height': 52, 'pnt': [63.0, -105.0, -26.0], 'dir': [0.0, 0.0, 1.0], 'source_translation_folded': 830}, {'id': 844, 'op': 'fillet', 'target': 842, 'edges': [{'start': [-40.0, -105.0, 19.0], 'end': [-40.0, -99.0, 19.0], 'length': 6.0, 'kind': 'line'}, {'start': [-40.0, -99.0, -9.0], 'end': [-40.0, -105.0, -9.0], 'length': 6.0, 'kind': 'line'}, {'start': [40.0, -99.0, 19.0], 'end': [40.0, -105.0, 19.0], 'length': 6.0, 'kind': 'line'}, {'start': [40.0, -105.0, -9.0], 'end': [40.0, -99.0, -9.0], 'length': 6.0, 'kind': 'line'}], 'radius': 6}, {'id': 842, 'op': 'makeBox', 'length': 80, 'width': 6, 'height': 28, 'pnt': [-40.0, -105.0, -9.0], 'dir': [0.0, 0.0, 1.0], 'source_translation_folded': 838}, {'id': 866, 'op': 'fuse', 'target': 858, 'tools': [865]}, {'id': 858, 'op': 'cut', 'target': 852, 'tools': [857]}, {'id': 852, 'op': 'fillet', 'target': 966, 'edges': [{'start': [-130.0, -103.0, 32.0], 'end': [-130.0, -103.0, 34.0], 'length': 2.0, 'kind': 'line'}, {'start': [-130.0, -103.0, 34.0], 'end': [-130.0, -95.0, 34.0], 'length': 8.0, 'kind': 'line'}, {'start': [-130.0, -95.0, 34.0], 'end': [-130.0, -95.0, 32.0], 'length': 2.0, 'kind': 'line'}, {'start': [-130.0, -95.0, 32.0], 'end': [-130.0, -103.0, 32.0], 'length': 8.0, 'kind': 'line'}, {'start': [130.0, -103.0, 34.0], 'end': [130.0, -103.0, 32.0], 'length': 2.0, 'kind': 'line'}, {'start': [130.0, -95.0, 34.0], 'end': [130.0, -103.0, 34.0], 'length': 8.0, 'kind': 'line'}, {'start': [130.0, -95.0, 32.0], 'end': [130.0, -95.0, 34.0], 'length': 2.0, 'kind': 'line'}, {'start': [130.0, -103.0, 32.0], 'end': [130.0, -95.0, 32.0], 'length': 8.0, 'kind': 'line'}, {'start': [-130.0, -103.0, 32.0], 'end': [130.0, -103.0, 32.0], 'length': 260.0, 'kind': 'line'}, {'start': [130.0, -103.0, 34.0], 'end': [-130.0, -103.0, 34.0], 'length': 260.0, 'kind': 'line'}, {'start': [130.0, -95.0, 32.0], 'end': [-130.0, -95.0, 32.0], 'length': 260.0, 'kind': 'line'}, {'start': [-130.0, -95.0, 34.0], 'end': [130.0, -95.0, 34.0], 'length': 260.0, 'kind': 'line'}], 'radius': 0.5, 'source_translation_folded': 851}, {'id': 966, 'op': 'makeBox', 'length': 260, 'width': 8, 'height': 2, 'pnt': [-130.0, -103.0, 32.0], 'dir': [0.0, 0.0, 1.0], 'source_translation_folded': 846}, {'id': 857, 'op': 'makeBox', 'length': 138, 'width': 20, 'height': 6, 'pnt': [-69.0, -109.0, 30.0], 'dir': [0.0, 0.0, 1.0], 'source_translation_folded': 853}, {'id': 865, 'op': 'fillet', 'target': 967, 'edges': [{'start': [-69.0, -108.0, 32.0], 'end': [-69.0, -108.0, 34.0], 'length': 2.0, 'kind': 'line'}, {'start': [-69.0, -108.0, 34.0], 'end': [-69.0, -102.0, 34.0], 'length': 6.0, 'kind': 'line'}, {'start': [-69.0, -102.0, 34.0], 'end': [-69.0, -102.0, 32.0], 'length': 2.0, 'kind': 'line'}, {'start': [-69.0, -102.0, 32.0], 'end': [-69.0, -108.0, 32.0], 'length': 6.0, 'kind': 'line'}, {'start': [69.0, -108.0, 34.0], 'end': [69.0, -108.0, 32.0], 'length': 2.0, 'kind': 'line'}, {'start': [69.0, -102.0, 34.0], 'end': [69.0, -108.0, 34.0], 'length': 6.0, 'kind': 'line'}, {'start': [69.0, -102.0, 32.0], 'end': [69.0, -102.0, 34.0], 'length': 2.0, 'kind': 'line'}, {'start': [69.0, -108.0, 32.0], 'end': [69.0, -102.0, 32.0], 'length': 6.0, 'kind': 'line'}, {'start': [-69.0, -108.0, 32.0], 'end': [69.0, -108.0, 32.0], 'length': 138.0, 'kind': 'line'}, {'start': [69.0, -108.0, 34.0], 'end': [-69.0, -108.0, 34.0], 'length': 138.0, 'kind': 'line'}, {'start': [69.0, -102.0, 32.0], 'end': [-69.0, -102.0, 32.0], 'length': 138.0, 'kind': 'line'}, {'start': [-69.0, -102.0, 34.0], 'end': [69.0, -102.0, 34.0], 'length': 138.0, 'kind': 'line'}], 'radius': 0.5, 'source_translation_folded': 864}, {'id': 967, 'op': 'makeBox', 'length': 138, 'width': 6, 'height': 2, 'pnt': [-69.0, -108.0, 32.0], 'dir': [0.0, 0.0, 1.0], 'source_translation_folded': 859}, {'id': 868, 'op': 'makeCylinder', 'radius': 5.5, 'height': 5, 'pnt': [-125.5, -101.0, -12.0], 'dir': [0.0, -1.0, 0.0], 'angleDegrees': 360}, {'id': 870, 'op': 'makeCylinder', 'radius': 1.7, 'height': 9, 'pnt': [-125.5, -99.0, -12.0], 'dir': [0.0, -1.0, 0.0], 'angleDegrees': 360}, {'id': 872, 'op': 'makeCylinder', 'radius': 5.5, 'height': 5, 'pnt': [-125.5, -101.0, 24.0], 'dir': [0.0, -1.0, 0.0], 'angleDegrees': 360}, {'id': 874, 'op': 'makeCylinder', 'radius': 1.7, 'height': 9, 'pnt': [-125.5, -99.0, 24.0], 'dir': [0.0, -1.0, 0.0], 'angleDegrees': 360}, {'id': 876, 'op': 'makeCylinder', 'radius': 5.5, 'height': 5, 'pnt': [125.5, -101.0, -12.0], 'dir': [0.0, -1.0, 0.0], 'angleDegrees': 360}, {'id': 878, 'op': 'makeCylinder', 'radius': 1.7, 'height': 9, 'pnt': [125.5, -99.0, -12.0], 'dir': [0.0, -1.0, 0.0], 'angleDegrees': 360}, {'id': 880, 'op': 'makeCylinder', 'radius': 5.5, 'height': 5, 'pnt': [125.5, -101.0, 24.0], 'dir': [0.0, -1.0, 0.0], 'angleDegrees': 360}, {'id': 882, 'op': 'makeCylinder', 'radius': 1.7, 'height': 9, 'pnt': [125.5, -99.0, 24.0], 'dir': [0.0, -1.0, 0.0], 'angleDegrees': 360}, {'id': 890, 'op': 'fillet', 'target': 968, 'edges': [{'start': [-116.5, -106.0, 17.5], 'end': [-116.5, -106.0, 26.5], 'length': 9.0, 'kind': 'line'}, {'start': [-116.5, -106.0, 26.5], 'end': [-116.5, -101.0, 26.5], 'length': 5.0, 'kind': 'line'}, {'start': [-116.5, -101.0, 26.5], 'end': [-116.5, -101.0, 17.5], 'length': 9.0, 'kind': 'line'}, {'start': [-116.5, -101.0, 17.5], 'end': [-116.5, -106.0, 17.5], 'length': 5.0, 'kind': 'line'}, {'start': [-107.5, -106.0, 26.5], 'end': [-107.5, -106.0, 17.5], 'length': 9.0, 'kind': 'line'}, {'start': [-107.5, -101.0, 26.5], 'end': [-107.5, -106.0, 26.5], 'length': 5.0, 'kind': 'line'}, {'start': [-107.5, -101.0, 17.5], 'end': [-107.5, -101.0, 26.5], 'length': 9.0, 'kind': 'line'}, {'start': [-107.5, -106.0, 17.5], 'end': [-107.5, -101.0, 17.5], 'length': 5.0, 'kind': 'line'}, {'start': [-116.5, -106.0, 17.5], 'end': [-107.5, -106.0, 17.5], 'length': 9.0, 'kind': 'line'}, {'start': [-107.5, -106.0, 26.5], 'end': [-116.5, -106.0, 26.5], 'length': 9.0, 'kind': 'line'}, {'start': [-107.5, -101.0, 17.5], 'end': [-116.5, -101.0, 17.5], 'length': 9.0, 'kind': 'line'}, {'start': [-116.5, -101.0, 26.5], 'end': [-107.5, -101.0, 26.5], 'length': 9.0, 'kind': 'line'}], 'radius': 0.5, 'source_translation_folded': 889}, {'id': 968, 'op': 'makeBox', 'length': 9, 'width': 5, 'height': 9, 'pnt': [-116.5, -106.0, 17.5], 'dir': [0.0, 0.0, 1.0], 'source_translation_folded': 884}, {'id': 892, 'op': 'makeCylinder', 'radius': 1.25, 'height': 9, 'pnt': [-112.0, -100.0, 22.0], 'dir': [0.0, -1.0, 0.0], 'angleDegrees': 360}, {'id': 900, 'op': 'fillet', 'target': 969, 'edges': [{'start': [107.5, -106.0, 17.5], 'end': [107.5, -106.0, 26.5], 'length': 9.0, 'kind': 'line'}, {'start': [107.5, -106.0, 26.5], 'end': [107.5, -101.0, 26.5], 'length': 5.0, 'kind': 'line'}, {'start': [107.5, -101.0, 26.5], 'end': [107.5, -101.0, 17.5], 'length': 9.0, 'kind': 'line'}, {'start': [107.5, -101.0, 17.5], 'end': [107.5, -106.0, 17.5], 'length': 5.0, 'kind': 'line'}, {'start': [116.5, -106.0, 26.5], 'end': [116.5, -106.0, 17.5], 'length': 9.0, 'kind': 'line'}, {'start': [116.5, -101.0, 26.5], 'end': [116.5, -106.0, 26.5], 'length': 5.0, 'kind': 'line'}, {'start': [116.5, -101.0, 17.5], 'end': [116.5, -101.0, 26.5], 'length': 9.0, 'kind': 'line'}, {'start': [116.5, -106.0, 17.5], 'end': [116.5, -101.0, 17.5], 'length': 5.0, 'kind': 'line'}, {'start': [107.5, -106.0, 17.5], 'end': [116.5, -106.0, 17.5], 'length': 9.0, 'kind': 'line'}, {'start': [116.5, -106.0, 26.5], 'end': [107.5, -106.0, 26.5], 'length': 9.0, 'kind': 'line'}, {'start': [116.5, -101.0, 17.5], 'end': [107.5, -101.0, 17.5], 'length': 9.0, 'kind': 'line'}, {'start': [107.5, -101.0, 26.5], 'end': [116.5, -101.0, 26.5], 'length': 9.0, 'kind': 'line'}], 'radius': 0.5, 'source_translation_folded': 899}, {'id': 969, 'op': 'makeBox', 'length': 9, 'width': 5, 'height': 9, 'pnt': [107.5, -106.0, 17.5], 'dir': [0.0, 0.0, 1.0], 'source_translation_folded': 894}, {'id': 902, 'op': 'makeCylinder', 'radius': 1.25, 'height': 9, 'pnt': [112.0, -100.0, 22.0], 'dir': [0.0, -1.0, 0.0], 'angleDegrees': 360}, {'id': 904, 'op': 'makeCylinder', 'radius': 1.7, 'height': 8, 'pnt': [-52.0, -99.0, -6.0], 'dir': [0.0, -1.0, 0.0], 'angleDegrees': 360}, {'id': 906, 'op': 'makeCylinder', 'radius': 1.7, 'height': 8, 'pnt': [52.0, -99.0, -6.0], 'dir': [0.0, -1.0, 0.0], 'angleDegrees': 360}, {'id': 908, 'op': 'makeCylinder', 'radius': 1.7, 'height': 8, 'pnt': [-124.0, -99.0, 29.0], 'dir': [0.0, 0.0, 1.0], 'angleDegrees': 360}, {'id': 910, 'op': 'makeCylinder', 'radius': 1.7, 'height': 8, 'pnt': [-118.0, -99.0, 29.0], 'dir': [0.0, 0.0, 1.0], 'angleDegrees': 360}, {'id': 912, 'op': 'makeCylinder', 'radius': 1.7, 'height': 8, 'pnt': [118.0, -99.0, 29.0], 'dir': [0.0, 0.0, 1.0], 'angleDegrees': 360}, {'id': 914, 'op': 'makeCylinder', 'radius': 1.7, 'height': 8, 'pnt': [124.0, -99.0, 29.0], 'dir': [0.0, 0.0, 1.0], 'angleDegrees': 360}, {'id': 916, 'op': 'makeCylinder', 'radius': 40.75, 'height': 49.4, 'pnt': [-70.3, -68.0, 0.0], 'dir': [-1.0, 0.0, 0.0], 'angleDegrees': 360}, {'id': 918, 'op': 'makeCylinder', 'radius': 40.75, 'height': 49.4, 'pnt': [70.3, -68.0, 0.0], 'dir': [1.0, 0.0, 0.0], 'angleDegrees': 360}, {'id': 932, 'op': 'cut', 'target': 926, 'tools': [931]}, {'id': 926, 'op': 'fillet', 'target': 970, 'edges': [{'start': [-69.0, -103.0, -3.5], 'end': [-69.0, -103.0, 0.5], 'length': 4.0, 'kind': 'line'}, {'start': [-69.0, -103.0, 0.5], 'end': [-69.0, -93.0, 0.5], 'length': 10.0, 'kind': 'line'}, {'start': [-69.0, -93.0, 0.5], 'end': [-69.0, -93.0, -3.5], 'length': 4.0, 'kind': 'line'}, {'start': [-69.0, -93.0, -3.5], 'end': [-69.0, -103.0, -3.5], 'length': 10.0, 'kind': 'line'}, {'start': [-57.0, -103.0, 0.5], 'end': [-57.0, -103.0, -3.5], 'length': 4.0, 'kind': 'line'}, {'start': [-57.0, -93.0, 0.5], 'end': [-57.0, -103.0, 0.5], 'length': 10.0, 'kind': 'line'}, {'start': [-57.0, -93.0, -3.5], 'end': [-57.0, -93.0, 0.5], 'length': 4.0, 'kind': 'line'}, {'start': [-57.0, -103.0, -3.5], 'end': [-57.0, -93.0, -3.5], 'length': 10.0, 'kind': 'line'}, {'start': [-69.0, -103.0, -3.5], 'end': [-57.0, -103.0, -3.5], 'length': 12.0, 'kind': 'line'}, {'start': [-57.0, -103.0, 0.5], 'end': [-69.0, -103.0, 0.5], 'length': 12.0, 'kind': 'line'}, {'start': [-57.0, -93.0, -3.5], 'end': [-69.0, -93.0, -3.5], 'length': 12.0, 'kind': 'line'}, {'start': [-69.0, -93.0, 0.5], 'end': [-57.0, -93.0, 0.5], 'length': 12.0, 'kind': 'line'}], 'radius': 0.4, 'source_translation_folded': 925}, {'id': 970, 'op': 'makeBox', 'length': 12, 'width': 10, 'height': 4, 'pnt': [-69.0, -103.0, -3.5], 'dir': [0.0, 0.0, 1.0], 'source_translation_folded': 920}, {'id': 931, 'op': 'makeBox', 'length': 13, 'width': 11.3, 'height': 17, 'pnt': [-58.5, -99.80000000000001, -16.5], 'dir': [0.0, 0.0, 1.0], 'source_translation_folded': 927}, {'id': 934, 'op': 'makeCylinder', 'radius': 1.25, 'height': 7, 'pnt': [-63.0, -97.0, -4.0], 'dir': [0.0, 0.0, 1.0], 'angleDegrees': 360}, {'id': 948, 'op': 'cut', 'target': 942, 'tools': [947]}, {'id': 942, 'op': 'fillet', 'target': 971, 'edges': [{'start': [57.0, -103.0, -3.5], 'end': [57.0, -103.0, 0.5], 'length': 4.0, 'kind': 'line'}, {'start': [57.0, -103.0, 0.5], 'end': [57.0, -93.0, 0.5], 'length': 10.0, 'kind': 'line'}, {'start': [57.0, -93.0, 0.5], 'end': [57.0, -93.0, -3.5], 'length': 4.0, 'kind': 'line'}, {'start': [57.0, -93.0, -3.5], 'end': [57.0, -103.0, -3.5], 'length': 10.0, 'kind': 'line'}, {'start': [69.0, -103.0, 0.5], 'end': [69.0, -103.0, -3.5], 'length': 4.0, 'kind': 'line'}, {'start': [69.0, -93.0, 0.5], 'end': [69.0, -103.0, 0.5], 'length': 10.0, 'kind': 'line'}, {'start': [69.0, -93.0, -3.5], 'end': [69.0, -93.0, 0.5], 'length': 4.0, 'kind': 'line'}, {'start': [69.0, -103.0, -3.5], 'end': [69.0, -93.0, -3.5], 'length': 10.0, 'kind': 'line'}, {'start': [57.0, -103.0, -3.5], 'end': [69.0, -103.0, -3.5], 'length': 12.0, 'kind': 'line'}, {'start': [69.0, -103.0, 0.5], 'end': [57.0, -103.0, 0.5], 'length': 12.0, 'kind': 'line'}, {'start': [69.0, -93.0, -3.5], 'end': [57.0, -93.0, -3.5], 'length': 12.0, 'kind': 'line'}, {'start': [57.0, -93.0, 0.5], 'end': [69.0, -93.0, 0.5], 'length': 12.0, 'kind': 'line'}], 'radius': 0.4, 'source_translation_folded': 941}, {'id': 971, 'op': 'makeBox', 'length': 12, 'width': 10, 'height': 4, 'pnt': [57.0, -103.0, -3.5], 'dir': [0.0, 0.0, 1.0], 'source_translation_folded': 936}, {'id': 947, 'op': 'makeBox', 'length': 13, 'width': 11.3, 'height': 17, 'pnt': [45.5, -99.80000000000001, -16.5], 'dir': [0.0, 0.0, 1.0], 'source_translation_folded': 943}, {'id': 950, 'op': 'makeCylinder', 'radius': 1.25, 'height': 7, 'pnt': [63.0, -97.0, -4.0], 'dir': [0.0, 0.0, 1.0], 'angleDegrees': 360}, {'id': 957, 'op': 'extrudeLinear', 'outerWire': {'edges': [{'start': [-132.0, -89.4720779386456, 46.09999999998819], 'end': [-132.0, 89.4720779386456, 46.09999999998819], 'length': 178.94415587729122, 'kind': 'line'}, {'start': [-132.0, 89.4720779386456, 46.09999999998819], 'end': [-132.0, 93.43187591329026, 44.459797974632856], 'length': 4.398229715025705, 'kind': 'arc', 'center': [-132.0, 89.4720779386456, 40.49999999998819], 'radius': 5.6, 'normal': [-1.0, -0.0, -0.0], 'mid': [-132.0, 91.61510515989009, 45.6737253820514]}, {'start': [-132.0, 93.43187591329026, 44.459797974632856], 'end': [-132.0, 106.15979797464466, 31.73187591327846], 'length': 17.99999999999511, 'kind': 'line'}, {'start': [-132.0, 106.15979797464466, 31.73187591327846], 'end': [-132.0, 107.8, 27.772077938633796], 'length': 4.398229715025715, 'kind': 'arc', 'center': [-132.0, 102.2, 27.772077938633796], 'radius': 5.6, 'normal': [-1.0, -0.0, -0.0], 'mid': [-132.0, 107.37372538206321, 29.9151051598783]}, {'start': [-132.0, 107.8, 27.772077938633796], 'end': [-132.0, 107.79999999999998, -27.27207793864212], 'length': 55.04415587727591, 'kind': 'line'}, {'start': [-132.0, 107.79999999999998, -27.27207793864212], 'end': [-132.0, 106.15979797464466, -31.231875913286785], 'length': 4.398229715025705, 'kind': 'arc', 'center': [-132.0, 102.19999999999999, -27.27207793864212], 'radius': 5.6, 'normal': [-1.0, -0.0, -0.0], 'mid': [-132.0, 107.3737253820632, -29.41510515988662]}, {'start': [-132.0, 106.15979797464466, -31.231875913286785], 'end': [-132.0, 94.43187591328682, -42.959797974644665], 'length': 16.58578643762691, 'kind': 'line'}, {'start': [-132.0, 94.43187591328682, -42.959797974644665], 'end': [-132.0, 90.47207793864214, -44.6], 'length': 4.398229715025715, 'kind': 'arc', 'center': [-132.0, 90.47207793864214, -39.0], 'radius': 5.6, 'normal': [-1.0, -0.0, -0.0], 'mid': [-132.0, 92.61510515988665, -44.1737253820632]}, {'start': [-132.0, 90.47207793864214, -44.6], 'end': [-132.0, -90.47207793864214, -44.6], 'length': 180.9441558772843, 'kind': 'line'}, {'start': [-132.0, -90.47207793864214, -44.6], 'end': [-132.0, -94.43187591328682, -42.959797974644665], 'length': 4.398229715025715, 'kind': 'arc', 'center': [-132.0, -90.47207793864214, -39.0], 'radius': 5.6, 'normal': [-1.0, -0.0, -0.0], 'mid': [-132.0, -92.61510515988665, -44.1737253820632]}, {'start': [-132.0, -94.43187591328682, -42.959797974644665], 'end': [-132.0, -106.15979797464466, -31.231875913286785], 'length': 16.585786437626915, 'kind': 'line'}, {'start': [-132.0, -106.15979797464466, -31.231875913286785], 'end': [-132.0, -107.79999999999998, -27.27207793864212], 'length': 4.398229715025705, 'kind': 'arc', 'center': [-132.0, -102.19999999999999, -27.27207793864212], 'radius': 5.6, 'normal': [-1.0, -0.0, -0.0], 'mid': [-132.0, -107.3737253820632, -29.415105159886622]}, {'start': [-132.0, -107.79999999999998, -27.27207793864212], 'end': [-132.0, -107.8, 27.772077938633796], 'length': 55.04415587727592, 'kind': 'line'}, {'start': [-132.0, -107.8, 27.772077938633796], 'end': [-132.0, -106.15979797464466, 31.73187591327846], 'length': 4.398229715025715, 'kind': 'arc', 'center': [-132.0, -102.2, 27.772077938633796], 'radius': 5.6, 'normal': [-1.0, -0.0, -0.0], 'mid': [-132.0, -107.37372538206321, 29.9151051598783]}, {'start': [-132.0, -106.15979797464466, 31.73187591327846], 'end': [-132.0, -93.43187591329026, 44.459797974632856], 'length': 17.99999999999511, 'kind': 'line'}, {'start': [-132.0, -93.43187591329026, 44.459797974632856], 'end': [-132.0, -89.4720779386456, 46.09999999998819], 'length': 4.398229715025705, 'kind': 'arc', 'center': [-132.0, -89.4720779386456, 40.49999999998819], 'radius': 5.6, 'normal': [-1.0, -0.0, -0.0], 'mid': [-132.0, -91.61510515989009, 45.673725382051394]}], 'origin': [-132.00000000000009, 8.78302712206012e-16, 0.6889204999910592], 'normal': [-1.0, -0.0, -0.0]}, 'innerWires': [], 'vecNormal': [264.0, 0.0, 0.0], 'taper': 0}], 'volume_mm3': 17500.40542618884, 'profile_curve_simplifications': {'spline_to_line': 0, 'spline_to_arc': 0, 'remaining_splines': 0}}
    group=next(o.component for o in d.rootComponent.occurrences if o.component.name=='Body and chassis')
    assert not any(o.component.partNumber=='chassis_beam_-102' for o in group.occurrences),'Part already exists'
    start=d.timeline.count
    occ=group.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Chassis beam -102';c.partNumber='chassis_beam_-102'
    phase_start=time.perf_counter();phase_times={}
    builder=Builder(d,c,'chassis_beam_-102',graph['nodes'])
    if 'chassis_beam_-102'.startswith('pod_sleeve_'):
        # The source item is a two-piece cut-tube kit, separated by the stator
        # plate. Preserve both physical pieces as separately named native bodies.
        moved=builder.nodes[graph['root']];pair=builder.nodes[moved['target']]
        assert moved['op']=='moved' and pair['op']=='fuse' and len(pair['tools'])==1
        bodies=builder.build(pair['target'])+builder.build(pair['tools'][0])
        assert len(bodies)==2
        transform=core.Matrix3D.create();values=[]
        for row in moved['matrix']:values+=row[:3]+[row[3]*MM]
        transform.setWithArray(values+[0,0,0,1])
        builder.transform(bodies,transform,'Position two-piece tube kit',False)
        for body,label in zip(bodies,['Long compression tube','Short stand-off tube']):body.name=label
    else:bodies=[builder.finish(graph['root'])]
    phase_times['native_construction']=time.perf_counter()-phase_start;phase_start=time.perf_counter()
    volume=sum(body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume for body in bodies)*1000;err=abs(volume-graph['volume_mm3'])/graph['volume_mm3']
    phase_times['physical_properties']=time.perf_counter()-phase_start;phase_start=time.perf_counter()
    # This is only a gross authoring check against the source recipe's low
    # accuracy mass properties. The exported STEP must separately pass the
    # stricter 0.1% adaptive-volume and 0.05 mm surface migration gates.
    assert err<.01,('Gross native/source recipe volume differs','chassis_beam_-102',volume,graph['volume_mm3'],err)
    d.timeline.timelineGroups.add(start,d.timeline.count-1).name='Chassis beam -102'
    path=os.path.join(tempfile.gettempdir(),'tinfox-native');os.makedirs(path,exist_ok=True)
    step=os.path.join(path,'chassis_beam_-102'+'.step');stl=os.path.join(path,'chassis_beam_-102'+'.stl')
    ex=d.exportManager;assert ex.execute(ex.createSTEPExportOptions(step,c))
    phase_times['step_export']=time.perf_counter()-phase_start;phase_start=time.perf_counter()
    opts=ex.createSTLExportOptions(c,stl);opts.meshRefinement=fusion.MeshRefinementSettings.MeshRefinementHigh
    opts.unitType=fusion.DistanceUnits.MillimeterDistanceUnits
    assert ex.execute(opts)
    phase_times['stl_export']=time.perf_counter()-phase_start;phase_start=time.perf_counter()
    app.activeDocument.save('V0 native part: '+'chassis_beam_-102'+'; full migration audit remains open.')
    phase_times['cloud_save']=time.perf_counter()-phase_start
    print(json.dumps({'part':'chassis_beam_-102','label':'Chassis beam -102','sketches':c.sketches.count,'feature_count':c.features.count,'parameter_count':sum(1 for p in d.userParameters if p.name.startswith(safe('chassis_beam_-102'+'_'))),'volume_mm3':volume,'source_volume_mm3':graph['volume_mm3'],'relative_volume_error':err,'body_count':c.bRepBodies.count,'phase_seconds':phase_times,'slowest_native_features':sorted(builder.timings,key=lambda item:item['seconds_since_previous_feature'],reverse=True)[:10],'paths':[step,stl]}))
