"""Side-split shin and connector packaging revision. Dimensions are millimetres."""
import json, math, hashlib, copy
from pathlib import Path
from functools import cache
import cadquery as cq
import numpy as np
from scipy.spatial.transform import Rotation
import build as b
from kinematics import ROOT, P, LEGS, POSES, matrix
OUT=ROOT/'output/service-design';OUT.mkdir(exist_ok=True)
for d in ['step','stl','print-stl']: (OUT/d).mkdir(exist_ok=True)
box,cyl,ring=b.box,b.cyl,b.ring

@cache
def rod_clearance():
    from scipy.spatial import ConvexHull
    points=[]
    # Hull of the moving rod centerline with 9 mm allowance around its end eyes.
    for knee in range(-156,-47,2):
        a=math.radians(knee+P['crank_phase_deg']);t=math.radians(-knee)
        for zz in [0,-170]:
            x=22*math.cos(a);z=170-22*math.sin(a)+zz
            xx=math.cos(t)*x+math.sin(t)*z;zz2=-math.sin(t)*x+math.cos(t)*z
            for u in range(0,360,30):points.append((xx+9*math.cos(math.radians(u)),zz2+9*math.sin(math.radians(u))))
    points=np.array(points);h=ConvexHull(points);poly=points[h.vertices].tolist()
    wp=cq.Workplane(cq.Plane(origin=(0,81.8,0),xDir=(1,0,0),normal=(0,-1,0)))
    swept=wp.polyline(poly).close().extrude(-8.2).val()
    return swept.intersect(box(250,40,240,(0,83,-90)))

@cache
def shin(outer=False):
    blank=b.shin_blank()
    wires=[]
    for zz in [-24,-42,-66,-90,-114,-130]:
        width=34-12*(-zz-18)/118
        depth=25+7*math.exp(-(-zz-18)/35)
        wire=cq.Workplane('XY',origin=(b.shin_center(zz),83,zz)).rect(width-8,depth-8).val()
        wires.append(wire.fillet2D(2,wire.Vertices()))
    shell=blank.cut(cq.Solid.makeLoft(wires,ruled=False))
    shell=shell.fuse(b.integrated_knee_head(),box(16.6,16.8,37.4,(-2,83,-30.5),3.2))
    # Complete circular seats, open outward. Inboard shoulders remain structural.
    for y in [67,90]:shell=shell.fuse(ring(19.4,14,11,y))
    shell=shell.fuse(ring(19.4,8.2,3,78),ring(19.4,8.2,3,87))
    for y in [66,90]:shell=shell.cut(cyl(14,12,(0,y,0)))
    # Broad cross-bolt lands; metal sleeves bypass printed clamp compression.
    for zz in [-30,-105]:
        shell=shell.fuse(box(20,25,15,(2,83,zz),2).intersect(blank))
        shell=shell.cut(cyl(4.05,18,(2,74,zz)))
        shell=shell.cut(cyl(2.2,42,(2,62,zz)))
        shell=shell.cut(cyl(3.7,13,(2,92,zz)))
        shell=shell.cut(b.hex_nut(7.2,14,2,60,zz,.01))
    x=22*math.cos(math.radians(P['crank_phase_deg']));z=-22*math.sin(math.radians(P['crank_phase_deg']))
    shell=shell.cut(b.hex_nut(8.2,4.3,x,71.6,z,.01)).cut(cyl(2.8,6.4,(x,71.6,z)))
    shell=shell.cut(cyl(3.025,4.1,(x,77.9,z))).cut(cyl(3.05,8.2,(x,90,z)))
    shell=shell.cut(cyl(6.3,8.4,(x,81.8,z))).cut(cyl(5.3,6,(x,98,z)))
    shell=shell.cut(cyl(8.2,48,(0,60,0)))
    shell=shell.cut(rod_clearance()).clean()
    # Two rear access holes per shoulder reach the outer race at radius 12.7.
    for xx in [-12.7,12.7]:shell=shell.cut(cyl(1.3,16,(xx,77,0)))
    half=shell.intersect(box(120,60,240,(0,113 if outer else 53,-85)))
    # Broad alignment tongues locate halves without using screw shanks as dowels.
    for zz in [-60,-120]:
        xx=b.shin_center(zz)+(34-12*(-zz-18)/118)/2-2
        tab=box(4,4,10,(xx,83,zz),.6)
        if outer:half=half.cut(box(4.4,4.4,10.4,(xx,83,zz),.6))
        else:half=half.fuse(tab.intersect(blank))
    half=half.clean()
    
    if len(half.Solids())!=1:
        print([(round(q.Volume(),2),q.Center().toTuple()) for q in half.Solids()],flush=True)
    assert half.isValid() and len(half.Solids())==1,('shin',outer,len(half.Solids()))
    return half

def thigh_retainer(s,outer=False):
    # Existing thigh cheek supplies a backup axial stop for the outer race.
    # 0.3 mm end gap to bearing, 0.3 mm radial gap to the shin bore.
    y=98.3 if outer else 57.0;h=11.0 if outer else 12.7
    collar=ring(13.7,8.2,h,y,-170)
    # Only outer-race land approaches bearing; center remains recessed 1 mm.
    if outer:collar=collar.cut(cyl(12.4,1.0,(0,98.3,-170)))
    else:collar=collar.cut(cyl(12.4,1.0,(0,68.7,-170)))
    s=s.fuse(collar.translate((0,-16,0))).clean()
    assert s.isValid() and len(s.Solids())==1,('thigh',outer)
    return s

# Port envelope measured from the cached manufacturer RS02 STEP. The model has
# two opposed radial ports near the rear cover. Clocking remains a build datum.
PORT_ANGLE=40.0

def port_frame(face=0,sign=1,clock=None):
    clock=(-20.0 if face>0 else PORT_ANGLE) if clock is None else clock
    a=math.radians(clock-3.8)
    radial=np.array([math.sin(a),0,math.cos(a)])*sign
    tang=np.array([radial[2],0,-radial[0]])
    center=radial*35.6+np.array([0,face-37.6,0])
    return center,tang,np.array([0,1,0]),radial

def port_box(width,axial,depth,face=0,sign=1,start=0,clock=None):
    c,t,a,r=port_frame(face,sign,clock)
    plane=cq.Plane(origin=tuple(c+r*start),xDir=tuple(t),normal=tuple(r))
    return cq.Workplane(plane).rect(width,axial).extrude(depth).val()

def connector_parts(face=0,sign=1,clock=None):
    # Manufacturer plug outline: 12.30 x 4.20 x 11.80. Insertion overlap is
    # provisionally 5 mm; cable/heat-shrink envelope is intentionally larger.
    socket=port_box(15.5,5.2,6.6,face,sign,-6.6,clock)
    socket=socket.cut(port_box(12.5,4.4,5.4,face,sign,-5.2,clock))
    plug=port_box(12.3,4.2,11.8,face,sign,-5,clock)
    boot=port_box(15,9,8,face,sign,5.8,clock)
    clearance=port_box(18,12,21,face,sign,-5.5,clock)
    service=port_box(20,14,36,face,sign,-5.5,clock)
    return socket,plug,boot,clearance,service

def cable_space(face,sign):
    c,t,a,r=port_frame(face,sign)
    return cyl(5,27,tuple(c+r*11+a*2),(0,1,0))

def knee_port_cut(s):
    for sign in [-1,1]:s=s.cut(connector_parts(58.4,sign)[3])
    return s.clean()

def hip_port_cut(s):
    for sign in [-1,1]:s=s.cut(connector_parts(0,sign)[3]).cut(cable_space(0,sign))
    return s.clean()

def check_geometry():
    a,c=shin(),shin(True)
    print('shin volumes',a.Volume(),c.Volume(),'overlap',a.intersect(c).Volume(),flush=True)
    for out,part in [(False,a),(True,c)]:
        bearing=ring(14,6,8,90 if out else 70)
        direction=1 if out else -1
        for d in [0,.1,1,4,8,15,25]:
            v=max(0,part.intersect(bearing.translate((0,d*direction,0))).Volume())
            assert v<1e-4,('bearing extraction',out,d,v)
        for xx in [-12.7,12.7]:
            pin=cyl(1,9,(xx,82 if out else 75,0))
            assert max(0,part.intersect(pin).Volume())<1e-4,('pin path',out,xx)
    for d in [0,.1,1,3,10,30]:
        assert max(0,a.intersect(c.translate((0,d,0))).Volume())<1e-4,('split',d)
    return a,c

if __name__=='__main__':
    check_geometry()

def build_revision():
    model=json.loads((ROOT/'output/model.json').read_text())
    removed={'body_aft_0','end_cap_screw_-1_-18','end_cap_screw_-1_18','end_cap_nut_-1_-18','end_cap_nut_-1_18'}
    model['parts']=[p for p in model['parts'] if p['name'] not in removed]
    model['removed_parts']=sorted(removed)
    source_hash=hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest()
    originals={p['name']:p for p in model['parts']}
    meshes=model['meshes']; parts=model['parts']; changed={}; exact={}
    def load(key):return cq.importers.importStep(str(ROOT/'output/step-parts'/f'{key}.step')).val()
    def register(key,s):
        assert s.isValid(),key
        v,f=s.tessellate(.12,.12)
        meshes[key]={'vertices':[[round(c,6) for c in p.toTuple()] for p in v],'faces':[list(q) for q in f]}
        exact[key]=s
    def change(key,s,note):
        register(key,s);changed[key]=s
        for p in parts:
            if p['mesh']==key:
                p['volume_mm3']=s.Volume();p['mass_kg']=s.Volume()*b.DENSITY[p['material']]
                p['com_mm']=list(s.Center().toTuple());bb=s.BoundingBox();p['bounds_mm']=[bb.xlen,bb.ylen,bb.zlen];p['note']=note
    # Side halves contain entire bearing seats. M4 bolts now run along the axle.
    for out in [False,True]:
        key='shin_outer' if out else 'shin_inner'
        s=shin(out).translate((0,-16,0))
        note='Structural side half with a complete 28 mm bearing bore, integral pushrod ear, two rear extraction holes and broad alignment lands. Nominal fit needs printed coupons.'
        change(key,s,note);change(key+'_right',s.mirror('XZ'),note)
    # Reuse existing hardware names so old parts cannot remain ghosted in the view.
    for old,zz in [('37',-30),('105',-105)]:
        shapes={'sleeve':ring(4,2.15,18,58,zz,2),
                'bolt':cyl(2,25,(2,51,zz)).fuse(cyl(3.5,4,(2,76,zz))),
                'nut':b.hex_nut(7,3.2,2,54.8,zz,2)}
        for kind,s in shapes.items():
            key='shin_clamp_'+kind+'_'+old
            note={'sleeve':'8 OD x 4.3 ID x 18 mm metal compression sleeve.','bolt':'M4 x 25 socket screw; axis parallel to knee axle.','nut':'M4 hex nut, accessible from the inner exterior pocket.'}[kind]
            change(key,s,note);change(key+'_right',s.mirror('XZ'),note)
    for out in [False,True]:
        key='thigh_outer' if out else 'thigh_inner'
        s=thigh_retainer(load(key),out)
        # Cut locally reserved connector and cable-exit windows in the cradle.
        if not out:
            for sign in [-1,1]:s=s.cut(connector_parts(54.4,sign)[3]).cut(cable_space(54.4,sign))
        s=s.clean();assert len(s.Solids())==1,key
        note='Structural thigh half with integral knee outer-race backup stop, 0.3 mm nominal axial gap. Remove thigh cheeks and axle before extracting shin bearings.'
        change(key,s,note);change(key+'_right',s.mirror('XZ'),note)
    # Re-clock the knee stator interface by 20 degrees while preserving the three
    # structural tie positions. This changes the plate, not the actuator holes.
    plate=ring(48,30,3,50.5)
    for angle in range(20,380,40):
        x,z=36.5*math.cos(math.radians(angle)),36.5*math.sin(math.radians(angle))
        plate=plate.cut(cyl(1.7,5,(x,49.5,z)))
    for angle in b.POD_TIE_ANGLES:
        x,z=b.POD_TIE_RADIUS*math.cos(math.radians(angle)),b.POD_TIE_RADIUS*math.sin(math.radians(angle))
        plate=plate.cut(cyl(1.7,5,(x,49.5,z)))
    for key,s in [('motor_mount_ring',plate),('motor_mount_ring_right',plate.mirror('XZ'))]:
        change(key,s,'Knee stator plate with nine M3 clearance holes re-clocked 20 degrees; three structural tie holes retain their positions. Verify vendor datum orientation before fabrication.')
    for front in [-1,1]:
        key='motor_carrier_'+str(front)
        s=hip_port_cut(load(key));assert len(s.Solids())==1,key
        change(key,s,'Integrated hip carrier with opposed connector windows. Wiring fatigue and local cutout strength remain unqualified.')
        change(key+'_right',s.mirror('XZ'),'Mirrored carrier with opposed connector windows; same qualification limits.')
    for key in ['belly_center_0','body_center_0']:
        s=load(key);before=s.Volume()
        for leg,(front,side) in LEGS.items():
            for sign in [-1,1]:
                cut=connector_parts(0,sign)[3].rotate((0,0,0),(0,0,1),-90).translate((-67.3,0,0))
                if front<0:cut=cut.mirror('YZ')
                if side<0:cut=cut.mirror('XZ')
                cut=cut.translate((front*P['hip_x'],side*P['roll_y'],0))
                s=s.cut(cut)
        if before-s.Volume()>.001:
            s=s.clean();assert s.isValid() and len(s.Solids())==1,key
            change(key,s,'Body enclosure with local clearance for fixed roll-motor plug and heat-shrink envelope. Sealing remains to be designed.')
    from body_caps import end_cap
    for key,front in [('body_nose_surround',True)]:
        change(key,end_cap(load(key),front),'Chassis-mounted bridge with deep shoulder sockets. Unsupported lower ribbons removed. Broad curved central keel connects directly to the chassis crossmember through the existing two M3 screws. Local crown rises to about 68 mm; motor loads bypass this protective part. Print with removable supports; not a lifting handle.')
    # Place the head nuts below the crossmember rather than inside its thickness.
    for front in [1]:
        for yy in [-18,18]:
            key=f'end_cap_nut_{front}_{yy}'
            nut=b.hex_nut(5.5,2.4,0,0,0,1.5).rotate((0,0,0),(1,0,0),90).translate((front*121,yy,38.4))
            change(key,nut,'M3 nut below the chassis crossmember; installed before fitting the end bridge. Existing M3 x 8 countersunk screw passes through the bridge and crossmember.')
    # Move the provisional lidar onto the central cover, clear of the new bridge.
    for key,s in [('lidar_base',cyl(31,4,(82,0,52),(0,0,1))),('lidar',cyl(27,18,(82,0,56),(0,0,1))),('lidar_lid',cyl(27,2,(82,0,74),(0,0,1)))]:
        mass=originals[key]['mass_kg']
        change(key,s,'Provisional lidar envelope moved 30 mm rearward to clear the front shoulder bridge. Exact mount, cable and cooling details depend on selected sensor.')
        originals[key]['mass_kg']=mass
    added=[];connectors=[]
    def add(name,s,group,leg,color,role,check=True):
        key=name;register(key,s)
        bb=s.BoundingBox();p={'name':name,'mesh':key,'group':group,'leg':leg,'material':'envelope','color':color,'mass_kg':0,'com_mm':list(s.Center().toTuple()),'bounds_mm':[bb.xlen,bb.ylen,bb.zlen],'check':check,'note':role,'volume_mm3':s.Volume(),'service_role':role}
        parts.append(p);added.append(key);return p
    for leg,(front,side) in LEGS.items():
        for family,face,group in [('hip',0,'roll'),('knee',54.4,'thigh'),('roll',0,'mount')]:
            def place(s):
                if family=='roll':
                    s=s.rotate((0,0,0),(0,0,1),-90).translate((-67.3,0,0))
                    if front<0:s=s.mirror('YZ')
                if side<0:s=s.mirror('XZ')
                return s
            motor=b.motor_envelope((0,face,0))
            for sign in [-1,1]:motor=motor.cut(port_box(16,6,15,face,sign,-7))
            # Recesses in the simplified motor can expose the socket envelopes.
            key=originals[leg+'_'+family+'_motor']['mesh']
            register(key,place(motor))
            for sign in [-1,1]:
                pieces=connector_parts(face,sign)
                prefix=f'{leg}_{family}_port_{sign}'
                for suffix,s,color in zip(['socket','plug','boot','keepout','withdrawal'],pieces,['#424b46','#e2aa35','#363d39','#4ba9b8','#df914e']):
                    add(prefix+'_'+suffix,place(s),group,leg,color,suffix,suffix not in ['keepout','withdrawal'])
                # First cable segment is a packaging envelope, not a flex simulation.
                c,t,a,r=port_frame(face,sign)
                wire=cyl(3.5,22,tuple(c+r*11+a*4),(0,1,0))
                add(prefix+'_cable',place(wire),group,leg,'#ed7950','cable',True)
                connectors.append({'prefix':prefix,'motor':leg+'_'+family+'_motor','group':group,'leg':leg,'sign':sign,'clock_deg':-20.0 if family=='knee' else PORT_ANGLE,'socket_reference':'Two opposed ports in cached vendor STEP; approximate mouth radius 35.6 mm, rear axial station 37.6 mm behind output tip.','plug_outline_mm':[12.3,4.2,11.8],'insertion_overlap_mm_assumed':5,'cable_envelope_diameter_mm_assumed':7,'withdrawal_mm_reserved':24.2})
    # Only export the changed physical parts and connector bodies as individual CAD.
    exports=[]
    for key,s in {**changed,**{k:exact[k] for k in added if not k.endswith(('_keepout','_withdrawal'))}}.items():
        target=OUT/'step'/f'{key}.step';cq.exporters.export(s,str(target))
        reopened=cq.importers.importStep(str(target)).val()
        assert reopened.isValid() and len(reopened.Solids())==len(s.Solids()),key
        err=abs(reopened.Volume()-s.Volume())/max(s.Volume(),1);assert err<1e-4,(key,err)
        cq.exporters.export(s,str(OUT/'stl'/f'{key}.stl'),tolerance=.08,angularTolerance=.1)
        p=next(p for p in parts if p['mesh']==key)
        row={'id':key,'step':'step/'+key+'.step','stl':'stl/'+key+'.stl','volume_mm3':s.Volume(),'step_volume_error_fraction':err,'mass_g':p['mass_kg']*1000}
        if p['material']=='petg':
            side=-1 if key.endswith('_right') else 1
            angle=(-90 if key.removesuffix('_right').endswith('_outer') else 90)*side
            orient=s.rotate((0,0,0),(1,0,0),angle)
            if key in ['body_nose_surround','body_aft_0']:orient=s.rotate((0,0,0),(0,1,0),180)
            bb=orient.BoundingBox()
            orient=orient.translate((-(bb.xmin+bb.xmax)/2,-(bb.ymin+bb.ymax)/2,-bb.zmin))
            cq.exporters.export(orient,str(OUT/'print-stl'/f'{key}.stl'),tolerance=.08,angularTolerance=.1)
            bb=orient.BoundingBox();row.update(print_stl='print-stl/'+key+'.stl',print_bounds_mm=[bb.xlen,bb.ylen,bb.zlen],orientation='Exterior down, open cavity up; bearing axis vertical, long limb axis in bed plane. Local supports need slicer review.')
            if key in ['body_nose_surround','body_aft_0']:row['orientation']='Curved roof downward, channel open upward. Local removable support beneath the curved roof and end return; inspect in slicer. Supports must not fill screw holes.'
            assert bb.xlen<305 and bb.ylen<300 and bb.zlen<315,key
        exports.append(row)
    model['status']='Service and connector packaging revision; nominal fit prototype, not a manufacturing release.'
    model['source_model_sha256']=source_hash
    used={p['mesh'] for p in parts};model['meshes']={k:v for k,v in meshes.items() if k in used}
    raw=json.dumps(model,separators=(',',':'));(OUT/'model.json').write_text(raw)
    stamp=hashlib.sha256(raw.encode()).hexdigest()
    (OUT/'parts.json').write_text(json.dumps({'model_sha256':stamp,'parts':exports,'connectors':connectors},indent=2))
    # Export the updated front-left leg at standing pose, including connectors.
    assembly=cq.Assembly(name='Tinfox_service_leg')
    for p in parts:
        if p['leg']!='FL' or p.get('service_role') in ['keepout','withdrawal']:continue
        key=p['mesh']
        if key in exact:s=exact[key]
        elif (ROOT/'output/step-parts'/f'{key}.step').exists():s=load(key)
        else:continue
        m=matrix(p,POSES['stand']);rv=Rotation.from_matrix(m[:3,:3]).as_rotvec();angle=np.linalg.norm(rv);axis=rv/angle if angle>1e-12 else np.array([1,0,0])
        loc=cq.Location(cq.Vector(*m[:3,3]),cq.Vector(*axis),math.degrees(angle))
        color=p['color'];rgb=tuple(int(color[i:i+2],16)/255 for i in (1,3,5))
        assembly.add(s,name=p['name'],loc=loc,color=cq.Color(*rgb))
    assembly.export(str(OUT/'updated-leg.step'))
    print('REVISION EXPORTED',len(parts),len(exports),stamp,flush=True)

if __name__=='__main__':build_revision()
