"""Parametric solid assembly and a browser mesh export, in millimetres.

STEP preserves separate solids. STL files are geometry prototypes, not qualified
production parts. Motor solids are dimensioned envelopes, not vendor internals.
"""
import json, math, hashlib
from pathlib import Path
from functools import cache
import cadquery as cq
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull
from kinematics import P, ROOT, LEGS, POSES, matrix, rotation

OUT=ROOT/'output';OUT.mkdir(exist_ok=True)
(OUT/'stl').mkdir(exist_ok=True)
COLORS={'shell':'#d9d6cc','dark':'#202321','metal':'#b4b5b0','orange':'#f66c27','rubber':'#191e1b','glass':'#080f12','plate':'#545c58'}
DENSITY={'petg':1.27e-6,'aluminum':2.70e-6,'steel':7.85e-6,'rubber':1.15e-6,'envelope':0,'fabric':0}
parts=[];meshes={};solids={};prototypes={}

def box(x,y,z,center=(0,0,0),r=0):
    w=cq.Workplane('XY').box(x,y,z)
    if r:w=w.edges().fillet(r)
    return w.val().translate(center)

def cyl(r,h,at=(0,0,0),axis=(0,1,0)):
    return cq.Solid.makeCylinder(r,h,cq.Vector(*at),cq.Vector(*axis))

def motor_envelope(face=(0,0,0),axis=(0,1,0)):
    # Vendor CAD: body -41.4..0, output pilot 0..4 along its shaft axis.
    # The supplied face is the output face; connectors and detailed fasteners are omitted.
    v=np.array(axis,dtype=float);o=np.array(face,dtype=float)
    body=cyl(P['motor_radius'],41.4,tuple(o-v*45.4),axis)
    return body.fuse(cyl(21.9,4,tuple(o-v*4),axis))

def ring(ro,ri,h,y=0,z=0,x=0):return cyl(ro,h,(x,y,z)).cut(cyl(ri,h+2,(x,y-1,z)))

def profile(y,shrink=0):
    # A continuous curved load path: circular shoulder, tapered web, small knee.
    wp=cq.Workplane(cq.Plane(origin=(0,y,0),xDir=(1,0,0),normal=(0,-1,0)))
    w=(wp.moveTo(-49,0).threePointArc((0,49),(49,0))
       .spline([(38,-40),(29,-65),(20,-106),(18,-142),(22,-170)],includeCurrent=True)
       .threePointArc((1,-189),(-20,-170))
       .spline([(-20,-142),(-23,-106),(-30,-65),(-38,-43),(-41,-35),(-49,0)],includeCurrent=True).close())
    if shrink:
        w=w.wires().toPending().offset2D(-shrink)
        # Convert offset boundary curves before extrusion so STEP retains every face.
        w=cq.Workplane(w.plane).add(w.wires().val().toNURBS()).toPending()
    return w

POD_TIE_ANGLES=[90,210,330]
POD_TIE_RADIUS=43.5

SHELL_BOLTS=[(-34,-43),(26,-48)]

def cheek_roof(z):
    # Smooth depth reduction through the thigh web, retaining full joint seats.
    return min(105.0,105.5-2*math.exp(-((z+98)/37)**4))

@cache
def cheek_envelope(offset=0):
    # Extend past the flat joint seats to avoid coincident trimming surfaces.
    pts=[(float(z),105.5-2*math.exp(-((z+98)/37)**4)-offset) for z in np.linspace(-210,60,55)]
    wp=cq.Workplane(cq.Plane(origin=(-80,0,0),xDir=(0,0,1),normal=(-1,0,0)))
    return (wp.moveTo(-210,0).lineTo(*pts[0]).spline(pts[1:],includeCurrent=True)
            .lineTo(60,0).close().extrude(-160).val())

@cache
def shell_half(outer=False):
    y=83 if outer else 61;depth=22;skin=P['shell_skin']
    envelope=profile(y).extrude(-depth).val()
    if outer:
        s=cq.Workplane(obj=envelope).faces('>Y').edges().fillet(5).val()
    else:s=envelope
    if outer:s=s.intersect(cheek_envelope())
    structural_blank=s
    cavity_y=y if outer else y+skin
    cavity=profile(cavity_y,P['shell_wall']).extrude(-(depth-skin)).val()
    if outer:cavity=cavity.intersect(cheek_envelope(skin))
    s=s.cut(cavity)
    s=s.cut(cyl(6.1,depth+2,(0,y-1,-170))).cut(cyl(10,depth+2,(0,y-1,0)))
    for z in [-57,-103]:
        s=s.fuse(box(27,depth-1,4,(-14,y+depth/2,z)).intersect(structural_blank))
    for x,z in SHELL_BOLTS:
        s=s.fuse(cyl(6,depth,(x,y,z)).intersect(structural_blank))
        s=s.cut(cyl(4.1,depth+2,(x,y-1,z)))
        yy=cheek_roof(z)-2 if outer else y
        s=s.cut(cyl(4.4,3.1,(x,yy,z)))
    if not outer:
        for a in POD_TIE_ANGLES:
            x,z=POD_TIE_RADIUS*math.cos(math.radians(a)),POD_TIE_RADIUS*math.sin(math.radians(a))
            s=s.cut(cyl(1.8,6,(x,60,z)))
    opening=box(130,40,155,(0,85,-142.5))
    if outer:opening=opening.intersect(cheek_envelope(4))
    else:opening=box(130,36,155,(0,83,-142.5))
    s=s.cut(opening)
    if outer:s=s.cut(cyl(40.3,5,(0,103.5,0)))
    if not outer:s=s.cut(cyl(20,5,(0,60,0)))
    s=s.cut(box(25,10.2,230,(-17.5,86,-80)))
    return s.cut(cyl(6.1,depth+2,(0,y-1,-170))).clean()

def shin_center(z):
    t=-z/P['shank_to_foot_center']
    return 14*t*(1-t)

@cache
def shin_blank():
    wires=[]
    for z in [-18,-42,-66,-90,-114,-136]:
        x=shin_center(z)
        w=34-12*(-z-18)/118
        d=25+7*math.exp(-(-z-18)/35)
        wire=cq.Workplane('XY',origin=(x,83,z)).rect(w,d).val()
        wires.append(wire.fillet2D(6 if z>=-122 else 6.5,wire.Vertices()))
    s=cq.Solid.makeLoft(wires,ruled=False)
    for y in [67,91]:s=s.fuse(ring(22,17.2,8,y))
    return s.clean()

@cache
def shin_half(outer=False,cavity_width=16):
    if outer:return shin_half(False,cavity_width).mirror('XZ',(0,83,0))
    s=shin_blank()
    # The first part of the shin is an open fork around the crank sweep.
    s=s.cut(box(70,16,100,(0,83,-30)))
    cavity=[]
    for z in [-82,-103,-124]:
        x=shin_center(z)
        wire=cq.Workplane('XY',origin=(x,83,z)).rect(cavity_width,17).val()
        cavity.append(wire.fillet2D(3,wire.Vertices()))
    s=s.cut(cq.Solid.makeLoft(cavity,ruled=False))
    for x,z in [(shin_center(-90)+4,-90),(shin_center(-130),-130)]:
        s=s.fuse(cyl(4.5,32,(x,67,z)).intersect(shin_blank()))
        s=s.cut(cyl(1.7,34,(x,66,z)))
    channel=[]
    path=[(z,shin_center(z)-3.5,82-(25+7*math.exp(-(-z-18)/35))/2) for z in [-49,-73,-97,-121]]
    for z,x,y in path:
        w=cq.Workplane('XY',origin=(x,y,z)).rect(5,5.4).val()
        channel.append(w.fillet2D(1.3,w.Vertices()))
    channel_cut=cq.Solid.makeLoft(channel,ruled=False)
    for z,x,y in [path[0],path[-1]]:
        channel_cut=channel_cut.fuse(cq.Solid.makeSphere(2.5,cq.Vector(x,y,z),angleDegrees1=-90,angleDegrees2=90))
    s=s.cut(channel_cut)
    s=s.cut(cyl(17.2,36,(0,65,0)))
    s=s.intersect(box(100,30,220,(0,98 if outer else 68,-85)))
    return s.clean()

def crank(y=77,output=False):
    a=cyl(18 if not output else 22,5,(0,y,0)).fuse(cyl(7,5,(P['crank_radius'],y,0)))
    a=a.fuse(box(P['crank_radius'],5,16,(P['crank_radius']/2,y+2.5,0)))
    if not output:
        a=a.cut(cyl(5,7,(0,y-1,0)))
        for angle in range(0,360,60):
            x,z=12*math.cos(math.radians(angle)),12*math.sin(math.radians(angle))
            a=a.cut(cyl(2.2,7,(x,y-1,z))).cut(cyl(4,3.2,(x,y+2,z)))
    if output:
        a=a.cut(cyl(8.2,7,(0,y-1,0)))
        for angle in [60,180,300]:
            a=a.cut(cyl(1.7,7,(17.5*math.cos(math.radians(angle)),y-1,17.5*math.sin(math.radians(angle)))))
    return a.cut(cyl(3,7,(P['crank_radius'],y-1,0))).clean()

def rod():
    wp=cq.Workplane(cq.Plane(origin=(0,83,0),xDir=(1,0,0),normal=(0,-1,0)))
    s=(wp.moveTo(-6,0).threePointArc((0,6),(6,0))
       .lineTo(3,-10).lineTo(3,-160).lineTo(6,-170)
       .threePointArc((0,-176),(-6,-170)).lineTo(-3,-160)
       .lineTo(-3,-10).close().extrude(-6).val())
    for z in [0,-170]:s=s.cut(cyl(3,8,(0,82,z)))
    return s.clean()

def add(name,shape,material='petg',color='shell',group='body',leg=None,mass=None,check=True,prototype=None,note=''):
    if leg and group in ['thigh','crank','rod','knee'] and not name.endswith('_hip_hub') and '_hip_output_bolt_' not in name:
        motor_parts=('_knee_motor','_motor_mount_ring')
        inset=P['motor_stack_inset_mm'] if name.endswith(motor_parts) or '_pod_' in name or name.endswith('_thigh_inner') or name.endswith('_knee_drive_adapter') else P['motor_stack_inset_mm']+P['limb_recess_mm']
        shape=shape.moved(cq.Location(cq.Vector(0,-inset,0)))
    # Mirror local transverse coordinates for the right side before rigid transforms.
    if leg and LEGS[leg][1]<0:shape=shape.mirror('XZ')
    if not shape.isValid():shape=shape.fix()
    if not shape.isValid():raise RuntimeError('Invalid solid: '+name)
    if material=='petg' and len(shape.Solids())!=1:raise RuntimeError('Printed part must be one solid: '+name)
    key=(prototype or name)+('_right' if leg and LEGS[leg][1]<0 else '')
    if key not in meshes:
        vs,fs=shape.tessellate(.025,.05) if name.startswith(('lens_','iris_','camera_','front_fascia','sensor_bezel','sensor_window')) else shape.tessellate(.38,.18)
        meshes[key]={'vertices':[[round(v.x,5),round(v.y,5),round(v.z,5)] for v in vs], 'faces':[list(f) for f in fs]}
    center=shape.Center();b=shape.BoundingBox()
    p={'name':name,'mesh':key,'group':group,'leg':leg,'material':material,'color':COLORS[color],
       'mass_kg':round(mass if mass is not None else shape.Volume()*DENSITY[material],6),
       'com_mm':[center.x,center.y,center.z], 'bounds_mm':[b.xlen,b.ylen,b.zlen],
       'check':check,'note':note,'volume_mm3':round(shape.Volume(),3)}
    parts.append(p);solids[name]=shape
    if prototype and material not in ['envelope','fabric']:
        prototypes.setdefault(key,shape)
    return shape

def body_dimensions(x):
    distance=abs(x)
    if distance<=132:return np.array([222.4,49.5,-48.0])
    if distance<=185:
        f=(1-math.cos(math.pi*(distance-132)/53))/2
        return np.array([222.4,49.5+6*f,-48.0])
    end=245.4 if x>0 else 232
    f=(1-math.cos(math.pi*(distance-185)/(end-185)))/2
    return np.array([222.4-(20.4 if x>0 else 72.4)*f,
                     55.5-(10 if x>0 else 13)*f,-48+(4 if x>0 else 7)*f])

def body_corner(x):
    t=max(0,min(1,(x-214)/(245.4-214)))
    f=(1-math.cos(math.pi*t))/2
    return np.array([18-7.2*f,17-6.2*f,9+9*f])

def body_section(x,inset=0):
    width,top,bottom=body_dimensions(x)
    dw,dt,db=(body_dimensions(x+.001)-body_dimensions(x-.001))/.002
    yy=width/2;dy=dw/2
    bevel_top,bevel_bottom,corner_radius=body_corner(x)
    dbt,dbb,_=(body_corner(x+.001)-body_corner(x-.001))/.002
    # Offset the transverse half-planes by their full 3D normal lengths.
    side=yy-inset*math.sqrt(1+dy*dy)
    roof=top-inset*math.sqrt(1+dt*dt)
    floor=bottom+inset*math.sqrt(1+db*db)
    upper=yy+top-bevel_top-inset*math.sqrt(2+(dy+dt-dbt)**2)
    lower=yy-bottom-bevel_bottom-inset*math.sqrt(2+(dy-db-dbb)**2)
    points=[(-(upper-roof),roof),(upper-roof,roof),(side,upper-side),
            (side,side-lower),(lower+floor,floor),(-(lower+floor),floor),
            (-side,side-lower),(-side,upper-side)]
    wire=cq.Workplane('YZ',origin=(x,0,0)).polyline(points).close().val()
    return wire.fillet2D(max(.8,corner_radius-inset),wire.Vertices())

@cache
def torso(inset=0):
    # The center remains planar; cosine-defined end sections provide one controlled wrap.
    front=[132,138,148,160,172,180,185,192,202,214,226,236,242,245.4-inset]
    rear=[-232+inset,-228,-221,-212,-202,-192,-185,-180,-172,-160,-148,-138,-132]
    front=sorted(set(x for x in front if x<=245.4-inset))
    rear=sorted(set(x for x in rear if x>=-232+inset))
    nose=cq.Solid.makeLoft([body_section(x,inset) for x in front],ruled=False)
    tail=cq.Solid.makeLoft([body_section(x,inset) for x in rear],ruled=False)
    center=cq.Solid.extrudeLinear(body_section(-132,inset),[],cq.Vector(264,0,0))
    solid=nose.fuse(center).fuse(tail).clean()
    for x,radius in [(245.4-inset,max(.3,5-inset)),(-232+inset,max(.3,4-inset))]:
        edges=[edge for edge in solid.Edges() if edge.BoundingBox().xlen<1e-4 and abs(edge.Center().x-x)<.01]
        solid=cq.Workplane(obj=solid).newObject(edges).fillet(radius).val()
    if not solid.isValid() or len(solid.Solids())!=1:raise RuntimeError('Body envelope is not a single valid solid')
    return solid


def build_body():
    length=P['body_length'];width=P['body_width'];height=P['body_height']
    outer=torso()
    inner=torso(P['body_skin'])
    shell=outer.cut(inner)
    window_mask=cq.Workplane(obj=box(48,28,20,(20,0,48))).edges('|Z').fillet(4).val()
    status_window=outer.cut(torso(.6)).intersect(window_mask)
    shell=shell.cut(status_window)
    for x in [-55,55]:shell=shell.fuse(box(2.4,176,12,(x,0,46)).intersect(outer))
    # Local inside reliefs preserve clearance to the fixed roll-motor cartridges.
    for front in [-1,1]:
        for side in [-1,1]:
            shell=shell.cut(cyl(41.25,49.4,(front*70.3,side*68,0),(front,0,0)))
            shell=shell.cut(cyl(42,7,(front*111.7,side*68,0),(front,0,0)))
            shell=shell.cut(cyl(38,20,(front*113.5,side*68,0),(front,0,0)))
            for z in [-12,24]:shell=shell.cut(box(14,16,14,(front*125.5,side*94.5,z)))
    for y in [-102,102]:shell=shell.cut(box(268,3,55,(0,y,8),.8))
    shell=shell.cut(box(148,198,70,(0,0,-55),8))
    nose_return_fasteners=[]
    for x in [218,228]:
        top=outer.intersect(cyl(.01,30,(x,0,30),(0,0,1))).BoundingBox().zmax
        derivative=(body_dimensions(x+.001)[1]-body_dimensions(x-.001)[1])/.002
        normal=np.array([-derivative,0,1]);normal/=np.linalg.norm(normal)
        point=np.array([x,0,top]);nose_return_fasteners.append((x,point,normal))
        shell=shell.cut(cyl(1.7,18,tuple(point-normal*15),tuple(normal)))
        shell=shell.cut(cyl(2.8,1.1,tuple(point-normal*.6),tuple(normal)))
    nominal_shell=shell
    # The corner pockets follow the roll swept volume, including the thigh root.
    samples=[]
    for a in np.deg2rad(np.arange(-61,62)):
        for yy,zz in [(-51,-55),(-51,55),(111,-55),(111,55)]:
            samples.append([yy*np.cos(a)-zz*np.sin(a),yy*np.sin(a)+zz*np.cos(a)])
    pts=np.array(samples);hull=pts[ConvexHull(pts).vertices].tolist()
    blank=cq.Workplane(cq.Plane(origin=(-57,0,0),xDir=(0,1,0),normal=(1,0,0))).polyline(hull).close().extrude(114).val()
    body_sweep_cuts=[]
    for front in [-1,1]:
        for side in [-1,1]:
            cut=blank if side>0 else blank.mirror('XZ')
            cut=cut.translate((front*P['hip_x'],side*P['roll_y'],0))
            if front>0:cut=cut.intersect(box(500,500,500,(-9.0,0,0)))
            body_sweep_cuts.append(cut)
            shell=shell.cut(cut)
    for front in [-1,1]:
        for side in [-1,1]:
            shell=shell.cut(box(100,50,122,(front*205,side*135,0)))
    # The fixed sensor face narrows toward the motors behind its outer edge.
    face_region=(cq.Workplane('XY').polyline([(230,-38),(232.2,-42),(232.2,42),(230,38)])
                 .close().extrude(140).val().translate((0,0,-70)))
    for front in [-1,1]:
        region=face_region if front>0 else face_region.mirror('YZ')
        shell=shell.fuse(nominal_shell.intersect(region))
    for front in [-1,1]:
        for side in [-1,1]:
            removed=nominal_shell.cut(shell).intersect(box(116,124,120,(front*P['hip_x'],side*62,0)))
            removed=removed.cut(cyl(45.5,52,(front*P['hip_x'],side*18,0),(0,side,0)))
            removed=removed.cut(cyl(54.5,120,(front*P['hip_x'],side*67,0),(0,side,0)))
            if removed.Volume()>1:
                for label,z,h,col in [('upper',25,70,'shell'),('lower',-35,50,'dark')]:
                    patch=removed.intersect(box(120,150,h,(front*P['hip_x'],side*68,z)))
                    if patch.Volume()>1:add(f'flexible_gaiter_{label}_{front}_{side}',patch,'fabric',col,mass=.018,check=False,note='Neutral flexible gaiter envelope; not a rigid shoulder. Deformation and attachment remain to be developed.')
    for tag,x0,x1 in [('aft',-232,-126),('center',-125.4,125.4),('front',126,232)]:
        for label,z,h in [('body',25,70),('belly',-35,50)]:
            pieces=shell.intersect(box(x1-x0,240,h,((x0+x1)/2,0,z)))
            if tag=='center' and label=='body':
                # Separate the roof and side panels so each broad face can lie on the bed.
                roof=pieces.intersect(box(270,250,40,(0,0,51.8)))
                for side in [-1,1]:
                    panel=pieces.intersect(box(270,30,80,(0,side*111, -8.7)))
                    for x in [-112,112]:
                        boss=box(8,4.6,18,(x,side*107.1,27),.6)
                        roof=roof.fuse(boss.intersect(outer)).cut(cyl(1.25,9,(x,side*103,22),(0,side,0)))
                        panel=panel.cut(cyl(1.7,10,(x,side*105,22),(0,side,0)))
                    roof=roof.cut(panel.translate((0,-side*.2,0)))
                    add(f'body_center_side_{side}',panel.clean(),color='shell',prototype=f'body_center_side_{side}',note='Separate broad-face side panel; two upper M3 pilot-boss connections to the roof. Lower fastener retention remains provisional.')
                add('body_center_0',roof.clean(),color='shell',prototype='body_center_0',note='Roof with four integral side-panel bosses; print broad exterior face down, ribs and bosses upward.')
            else:
                for i,solid in enumerate(pieces.Solids()):
                    add(f'{label}_{tag}_{i}',solid,color='shell' if label=='body' else 'dark',prototype=f'{label}_{tag}_{i}')
    # The service-panel perimeter and identification are actual solids.
    for side in [-1,1]:
        for x,z in [(-112,22),(112,22),(-112,-18),(112,-18)]:
            head=cyl(2.6,.7,(x,side*111.3,z),(0,side,0)).cut(cyl(1.1,1,(x,side*111.5,z),(0,side,0)))
            add(f'body_service_screw_{side}_{x}_{z}',head,'steel','dark',check=False,note='Visible M3 head envelope; panel clips and screw engagement remain to be detailed.')
    word=cq.Workplane('XZ',origin=(-30,-111.28,-4)).text('tinfox',10,.12,combine=True).val()
    add('body_wordmark',word,'envelope','dark',check=False,mass=.002)
    mark=cq.Workplane('XZ',origin=(96,-111.28,-17)).text('01',4,.12,combine=True).val()
    add('body_serial',mark,'envelope','dark',check=False,mass=.001)
    add('body_status_dot',cyl(2,.7,(-81,-111.3,-13),(0,-1,0)),'envelope','orange',check=False,mass=.001)
    for side in [-1,1]:
        wp=cq.Workplane(cq.Plane(origin=(0,side*97.2,0),xDir=(1,0,0),normal=(0,-1,0)))
        outline=wp.polyline([(-120,-44),(-69,-44),(-64,-6),(64,-6),(69,-44),(120,-44),(104,-55),(65,-68),(-65,-68),(-104,-55)]).close().val()
        outline=outline.fillet2D(2.5,outline.Vertices())
        panel=cq.Solid.extrudeLinear(outline,[],cq.Vector(0,side*2.4,0))
        panel=cq.Workplane(obj=panel).edges().fillet(.5).val()
        add(f'battery_side_panel_{side}',panel,'petg','dark',prototype=f'battery_side_panel_{side}',note='Removable lower service panel around the existing battery cassette. Latch details remain provisional.')
        for x in [-50,50]:add(f'battery_access_screw_{side}_{x}',cyl(2.5,.7,(x,side*99.8,-59),(0,side,0)).cut(cyl(1,1,(x,side*100,-59),(0,side,0))),'steel','metal',check=False)
        add(f'battery_access_latch_{side}',box(22,1.8,4,(0,side*100.0,-52),.5),'petg','orange',check=False,prototype=f'battery_access_latch_{side}')
    # Two removable packs sit alongside one another between the four motor stations.
    for side in [-1,1]:
        y=side*44.5
        add(f'battery_{side}',box(*P['battery_envelope_mm'],(0,y,P['battery_center_z']),7),'envelope','dark',mass=P['battery_each_mass_kg_assumed'],note='Pack plus adapter envelope; exact commercial pack remains unselected.')
        add(f'battery_latch_{side}',box(18,5,9,(0,side*91,-50),2),'petg','orange',check=False,prototype=f'battery_latch_{side}')
    for y in [-90.5,90.5]:
        rail=box(134,5,61,(0,y,-36),2).cut(cq.Workplane(obj=box(112,7,45,(0,y,-34))).edges('|Y').fillet(7).val())
        add(f'battery_rail_{y}',rail,color='dark',prototype=f'battery_rail_{y}')
    cassette=box(140,194,69.5,(0,0,-34.75),12).cut(box(136,190,70,(0,0,-32.5),10))
    add('battery_cassette',cassette,color='dark',prototype='battery_cassette',note='Rounded structural underside enclosure; pack adapters and contacts remain unselected.')
    skid_wire=cq.Workplane('XY',origin=(0,0,-71)).rect(138,190).val()
    skid_wire=skid_wire.fillet2D(15,skid_wire.Vertices())
    add('battery_skid',cq.Solid.extrudeLinear(skid_wire,[],cq.Vector(0,0,1.5)),'aluminum','plate',prototype='battery_skid')
    # Aluminum longitudinal members join the four roll cartridges to the torso.
    for y in [-102,102]:
        beam=box(260,2,54,(0,y,8),.8)
        for x in [-91,91]:
            beam=beam.cut(cq.Workplane(obj=box(56,6,52,(x,y,0))).edges('|Y').fillet(4).val())
        beam=beam.cut(cq.Workplane(obj=box(80,6,32,(0,y,8))).edges('|Y').fillet(8).val())
        for xx in [-125.5,125.5]:
            for zz in [-12,24]:beam=beam.cut(cyl(2.2,6,(xx,y-3,zz)))
        add(f'chassis_beam_{y}',beam,'aluminum','plate',prototype=f'chassis_beam_{y}')
    for side in [-1,1]:
        for xx in [-125.5,125.5]:
            for zz in [-12,24]:
                bolt=cyl(2,12,(xx,side*103,zz),(0,-side,0)).fuse(cyl(3.5,2.5,(xx,side*103,zz),(0,side,0)))
                add(f'chassis_bolt_{side}_{xx}_{zz}',bolt,'steel','dark',check=False)
    add('electronics_shelf',box(134,198,1.5,(0,0,3),.5).cut(cq.Workplane(obj=box(96,155,4,(0,0,3))).edges('|Z').fillet(12).val()),'aluminum','plate',prototype='electronics_shelf')
    add('electronics_clearance',box(*P['electronics_clearance_mm'],(0,0,22),2),'envelope','dark',check=True,note='Reserved 130 x 135 x 32 mm computer volume; mass is in the electronics allowance. Exact computer and heat sink are unselected.')
    add('lidar_base',cyl(31,4,(112,0,48),(0,0,1)),'envelope','dark',mass=.04,check=False)
    add('lidar',cyl(27,18,(112,0,52),(0,0,1)),'envelope','glass',mass=.15,check=False)
    add('lidar_lid',cyl(27,2,(112,0,70),(0,0,1)),'aluminum','metal',check=False,prototype='lidar_lid')
    # The wrap and service face share the body's actual outer envelope.
    nose=shell.intersect(box(10.2,250,150,(237.7,0,0)))
    tongue=torso(1.9).cut(torso(4.7)).intersect(box(22.5,11,30,(225.25,0,45)))
    bridge=outer.cut(torso(4.7)).intersect(box(5.2,11,30,(235.8,0,45)))
    nose=nose.fuse(tongue).fuse(bridge)
    for cut in body_sweep_cuts:nose=nose.cut(cut)
    for x,point,normal in nose_return_fasteners:
        nose=nose.cut(cyl(1.25,18,tuple(point-normal*15),tuple(normal)))
        head=cyl(2.6,.4,tuple(point-normal*.5),tuple(normal)).cut(cyl(1,.8,tuple(point-normal*.6),tuple(normal)))
        add(f'nose_return_screw_{x}',head,'steel','dark',check=False)
    # Analytic rounded sections give the curved face a stable manufacturing solid.
    face_crown=3.4;face_half_width=98.0;face_half_height=42.0
    def face_x(y,z=2):
        return 245.4+face_crown*(1-(y/face_half_width)**2)*(1-((z-2)/face_half_height)**4)
    @cache
    def bowed_volume(offset=0):
        wires=[]
        for zz in np.linspace(-53,57,19):
            points=[(face_x(float(y),float(zz))-offset,float(y)) for y in np.linspace(-110,110,13)]
            wire=(cq.Workplane('XY',origin=(0,0,float(zz))).moveTo(230,-110).lineTo(*points[0])
                  .spline(points[1:],includeCurrent=True).lineTo(230,110).close().val())
            wires.append(wire)
        return cq.Solid.makeLoft(wires,ruled=False)
    def fascia_blank(inset=0):
        wires=[]
        for x,w,h,r in [(241.3,200.3,87.7,18),(243.5,196.5,83.5,17),(251,192.5,80,16)]:
            wire=cq.Workplane('YZ',origin=(x,0,2)).rect(w-2*inset,h-2*inset).val()
            wires.append(wire.fillet2D(r-inset,wire.Vertices()))
        return cq.Solid.makeLoft(wires,ruled=True)
    fascia=fascia_blank().intersect(bowed_volume()).cut(fascia_blank(1.8).intersect(bowed_volume(1.8))).clean()
    aperture=cq.Workplane('YZ',origin=(240,0,5)).rect(168,40).extrude(13).edges('|X').fillet(10).val()
    fascia=fascia.cut(aperture)
    for y in [-89,89]:
        for z in [-27,27]:
            tab=box(3.8,17,3.2,(240.8,y/abs(y)*94,z),.6).intersect(outer)
            post=cyl(3.5,9,(239,y,z),(1,0,0)).intersect(bowed_volume(1.8))
            nose=nose.fuse(tab).fuse(post).cut(cyl(1.25,7,(238.5,y,z),(1,0,0)))
            fascia=fascia.cut(cyl(1.7,14,(239,y,z),(1,0,0))).cut(cyl(2.7,1.8,(face_x(y,z)-.6,y,z),(1,0,0)))
            add(f'front_fascia_screw_{y}_{z}',cyl(2.5,.35,(face_x(y,z)-.15,y,z),(1,0,0)).cut(cyl(1,.8,(face_x(y,z)-.3,y,z),(1,0,0))),'steel','dark',check=False)
    nose=nose.clean();fascia=fascia.cut(nose).clean()
    # The rear rim trim can leave a tiny detached strip above the body return.
    # Remove that offcut; it has no connection to the manufactured face.
    face_pieces=sorted(fascia.Solids(),key=lambda item:item.Volume(),reverse=True)
    for offcut in face_pieces[1:]:
        if offcut.Volume()>10 or offcut.BoundingBox().xmax>242:raise RuntimeError('Unexpected disconnected fascia material')
    fascia=face_pieces[0]
    if len(nose.Solids())!=1:raise RuntimeError('Nose wrap and return tabs must form one connected solid')
    add('body_nose_surround',nose,'petg','shell',prototype='body_nose_surround',note='Shared-envelope front wrap with a central body-return tongue and four fascia posts. Two M3-sized body holes and four fascia holes provide assembly access; final inserts, screws and load qualification remain unselected.')
    add('front_fascia',fascia,'petg','shell',prototype='front_fascia',note='Removable compound-curved face with a 3.4 mm nominal crown and a curved recessed sensor bezel. The rim preserves the body service gap.')
    bezel_mask=cq.Workplane('YZ',origin=(239,0,5)).rect(174,46).extrude(13).edges('|X').fillet(12).val()
    recess_mask=cq.Workplane('YZ',origin=(239,0,5)).rect(162,34).extrude(13).edges('|X').fillet(8).val()
    bezel=bezel_mask.intersect(bowed_volume(.7)).cut(bowed_volume(3.5))
    bezel=bezel.cut(recess_mask.cut(bowed_volume(2.4)))
    add('sensor_bezel',bezel,'petg','dark',check=False,prototype='sensor_bezel')
    visor=recess_mask.intersect(bowed_volume(1.9)).cut(bowed_volume(2.4))
    for y in [-52,52]:visor=visor.cut(cyl(11.2,13,(239,y,5),(1,0,0)))
    add('sensor_window',visor,'envelope','glass',mass=.09,check=False,note='Provisional dark sensor backing with lens apertures; selected protective glazing and seals remain unmodeled.')
    for y in [-52,52]:
        optic_shift=face_x(y,5)-245.4
        barrel=cyl(10.8,2.8,(240.9,y,5),(1,0,0)).cut(cyl(9.3,2.5,(242,y,5),(1,0,0)))
        add(f'camera_{y}',barrel.translate((optic_shift,0,0)),'envelope','dark',mass=.025,check=False)
        ring=cyl(9.2,.8,(243.1,y,5),(1,0,0)).cut(cyl(6.9,1.2,(243,y,5),(1,0,0)))
        add(f'lens_ring_{y}',ring.translate((optic_shift,0,0)),'envelope','plate',check=False)
        iris=cyl(7.5,.35,(242.2,y,5),(1,0,0)).cut(cyl(3.4,.6,(242.1,y,5),(1,0,0)))
        add(f'iris_{y}',iris.translate((optic_shift,0,0)),'envelope','dark',check=False)
        glass=cq.Solid.makeSphere(50,cq.Vector(194.2,y,5),angleDegrees1=-90,angleDegrees2=90).intersect(box(.65,19,19,(243.875,y,5)))
        add(f'lens_{y}',glass.translate((optic_shift-.8,0,0)),'envelope','glass',check=False)
    add('depth_sensor',cyl(3.5,.6,(face_x(0)-2.15,0,-1),(1,0,0)),'envelope','dark',check=False)
    add('status_display',status_window,'envelope','glass',mass=.03,check=False)
    dial=cyl(7.6,.12,(12,0,49.55),(0,0,1)).cut(cyl(7.2,.3,(12,0,49.5),(0,0,1)))
    add('status_display_dial',dial,'envelope','metal',check=False,mass=.001)
    button_z=outer.intersect(cyl(4.5,100,(55,-27,0),(0,0,1))).BoundingBox().zmax-.2
    add('power_button',cyl(4.5,1,(55,-27,button_z),(0,0,1)),'petg','orange',check=False,prototype='power_button')

def build_leg(leg):
    front,side=LEGS[leg]
    # Fixed fore/aft actuator, supported flange cartridge, short perpendicular carrier.
    def handed(shape):
        shape=shape.translate((-10,0,0))
        return shape if front>0 else shape.mirror('YZ')
    rollmotor=motor_envelope((-57.3,0,0),(1,0,0))
    add(leg+'_roll_motor',handed(rollmotor),'envelope','dark','mount',leg,P['motor_mass_kg'],True,'roll_motor_'+str(front))
    stator=cyl(41,3,(-61.3,0,0),(1,0,0)).cut(cyl(27,6,(-62.3,0,0),(1,0,0)))
    for a in range(0,360,40):stator=stator.cut(cyl(1.7,6,(-62.3,36.5*math.cos(math.radians(a)),36.5*math.sin(math.radians(a))),(1,0,0)))
    housing=cyl(36,16.3,(-60.3,0,0),(1,0,0)).cut(cyl(33.1,18.3,(-61.3,0,0),(1,0,0)))
    housing=housing.fuse(cyl(36,1,(-55,0,0),(1,0,0)).cut(cyl(30.5,3,(-56,0,0),(1,0,0))))
    # Mounting ears bolt the stationary bearing cartridge to the chassis beams.
    for z in [-12,24]:
        ear=box(11,13,11,(-49.5,26.5,z),2)
        ear=ear.cut(cyl(1.7,30,(-49.5,7,z),(0,1,0)))
        housing=housing.fuse(ear)
    housing=housing.fuse(stator).clean()
    # Drill the finished bore after adding mounting ears so no ear enters the rotating journal.
    housing=housing.cut(cyl(33.1,17,(-60,0,0),(1,0,0)))
    housing=housing.fuse(cyl(36,1,(-55,0,0),(1,0,0)).cut(cyl(30.5,3,(-56,0,0),(1,0,0)))).clean()
    if len(housing.Solids())!=1:raise RuntimeError('Fixed roll mount must be one solid')
    add(leg+'_roll_cartridge',handed(housing),'aluminum','plate','mount',leg,prototype='roll_cartridge_'+str(front),note='50 x 66 x 8 RA5008-size crossed-roller bearing envelope; preload, retention and moment capacity require supplier review.')
    bearing=cyl(33,8,(-54,0,0),(1,0,0)).cut(cyl(25,10,(-55,0,0),(1,0,0)))
    add(leg+'_roll_bearing',handed(bearing),'steel','metal','mount',leg,mass=.08,check=False)
    hub=cyl(24.95,13.3,(-57.3,0,0),(1,0,0)).fuse(cyl(29,3,(-44,0,0),(1,0,0)))
    for a in range(0,360,60):hub=hub.cut(cyl(2.2,19,(-58.3,12*math.cos(math.radians(a)),12*math.sin(math.radians(a))),(1,0,0)))
    flange=ring(44,27,3,-3.9)
    for a in range(0,360,40):flange=flange.cut(cyl(1.7,5,(36.5*math.cos(math.radians(a)),-4.9,36.5*math.sin(math.radians(a)))))
    bridge=box(18,28,40,(-49,-11,0),2).cut(box(22,15,23,(-49,-13,0),4))
    drive_plate=cyl(29,1.5,(-51,0,0),(1,0,0))
    carrier=flange.fuse(bridge if front>0 else bridge.mirror('YZ')).fuse(drive_plate if front>0 else drive_plate.mirror('YZ'))
    carrier=carrier.fuse(handed(hub)).clean()
    for a in range(0,360,60):carrier=carrier.cut(cyl(2.2,23,(-front*68,12*math.cos(math.radians(a)),12*math.sin(math.radians(a))),(front,0,0)))
    carrier=carrier.cut(cyl(7,23,(-front*68,0,0),(front,0,0)))
    if len(carrier.Solids())!=1:raise RuntimeError('Carrier must be one machined solid')
    if carrier.intersect(handed(housing)).Volume()>1e-3:raise RuntimeError('Fixed cartridge intersects rotating carrier')
    add(leg+'_motor_carrier',carrier,'aluminum','plate','roll',leg,prototype='motor_carrier_'+str(front),note='Single machined elbow carrier includes the roll-output coupling, bearing journal and perpendicular hip-stator mounting flange.')
    add(leg+'_hip_motor',motor_envelope(),'envelope','dark','roll',leg,P['motor_mass_kg'],True,'hip_motor')
    cover=ring(43.5,41.5,44.4,-48.4).fuse(ring(43.5,12,2,-48.4))
    collar=ring(52.2,50.3,45.4,-2.2).fuse(ring(52.2,41.5,2.2,-4.4))
    cover=cover.fuse(collar).cut(box(20,54,46,(-front*45,-24,0),2)).clean()
    add(leg+'_shoulder_cover',cover,'petg','dark','roll',leg,prototype='shoulder_cover_'+str(front),note='Annular cowling rotates with the roll carrier, clearing the pitch cradle radially and stopping before the thigh web. It does not bridge the fixed body to the moving limb.')
    # The rotating output hub clears the stationary stator flange radially and axially.
    hub=ring(20,6,5,0).fuse(ring(48,6,3,5))
    for angle in [30,150,270]:
        x,z=31*math.cos(math.radians(angle)),31*math.sin(math.radians(angle))
        hub=hub.cut(cyl(9,5,(x,4,z)))
    for a in range(0,360,60):
        x,z=12*math.cos(math.radians(a)),12*math.sin(math.radians(a))
        hub=hub.cut(cyl(2.2,13,(x,0,z))).cut(cyl(3.8,4.5,(x,3.7,z)))
        add(leg+f'_hip_output_bolt_{a}',cyl(3.5,4,(x,3.8,z)),'steel','metal','thigh',leg,check=False,note='Recessed M4 socket-head envelope; screw length and actuator thread engagement require supplier confirmation.')
    for a in POD_TIE_ANGLES:
        x,z=POD_TIE_RADIUS*math.cos(math.radians(a)),POD_TIE_RADIUS*math.sin(math.radians(a))
        hub=hub.cut(cyl(1.7,8,(x,0,z)))
    add(leg+'_hip_hub',hub,'aluminum','metal','thigh',leg,check=True,prototype='hip_hub')
    add(leg+'_knee_motor',motor_envelope((0,58.4,0)),'envelope','dark','thigh',leg,P['motor_mass_kg'],True,'knee_motor')
    mounting=ring(48,30,3,54.5)
    for a in range(0,360,40):mounting=mounting.cut(cyl(1.7,5,(36.5*math.cos(math.radians(a)),53.5,36.5*math.sin(math.radians(a)))))
    for a in POD_TIE_ANGLES:
        x,z=POD_TIE_RADIUS*math.cos(math.radians(a)),POD_TIE_RADIUS*math.sin(math.radians(a))
        mounting=mounting.cut(cyl(1.7,5,(x,53.5,z)))
    add(leg+'_motor_mount_ring',mounting,'aluminum','metal','thigh',leg,prototype='motor_mount_ring')
    # Smooth flare around the motor instead of an exposed constant-diameter can.
    planes=[(13,46.5),(28,47),(43,48),(50,48.5)]
    wires=[cq.Wire.makeCircle(rad,cq.Vector(0,y,0),cq.Vector(0,1,0)) for y,rad in planes]
    cup_blank=cq.Solid.makeLoft(wires,ruled=False)
    # Three axial metal ties join both motor flanges, outside the motor envelope.
    for a in POD_TIE_ANGLES:
        x,z=POD_TIE_RADIUS*math.cos(math.radians(a)),POD_TIE_RADIUS*math.sin(math.radians(a))
        # Two metal sleeve segments stop against the stator carrier plate.
        sleeve=ring(2.5,1.7,42.5,12,z,x).fuse(ring(2.5,1.7,3.5,57.5,z,x))
        add(leg+f'_pod_sleeve_{a}',sleeve,'aluminum','metal','thigh',leg,check=False,prototype=f'pod_sleeve_{a}')
        tie=cyl(1.5,58,(x,7,z)).fuse(cyl(2.8,3,(x,65,z)))
        add(leg+f'_pod_tie_{a}',tie,'steel','dark','thigh',leg,check=False,prototype=f'pod_tie_{a}')
    # Continuous printed cradle and thigh; motor flanges retain metal load spreaders.
    inner=shell_half().moved(cq.Location(cq.Vector(0,-12,0)))
    integrated=cup_blank.fuse(inner,tol=1e-5)
    integrated=integrated.cut(cyl(41.25,43,(0,12,0)))
    integrated=integrated.cut(cyl(23.9,7,(0,54,0)))
    integrated=integrated.cut(cyl(20,7,(0,59,0)))
    for a in POD_TIE_ANGLES:
        x,z=POD_TIE_RADIUS*math.cos(math.radians(a)),POD_TIE_RADIUS*math.sin(math.radians(a))
        boss=ring(5.2,2.8,15,49,z,x)
        integrated=integrated.fuse(boss,tol=1e-5)
    integrated=integrated.cut(ring(48.3,24,3.4,54.3))
    for a in POD_TIE_ANGLES:
        x,z=POD_TIE_RADIUS*math.cos(math.radians(a)),POD_TIE_RADIUS*math.sin(math.radians(a))
        integrated=integrated.cut(cyl(2.8,53,(x,12,z)))
    integrated=integrated.cut(box(25,10.2,230,(-17.5,74,-80)))
    integrated=integrated.cut(cyl(40.25,43,(0,12,0))).cut(ring(50,47.0,1.2,33)).clean()
    bb=integrated.BoundingBox()
    if not integrated.isValid() or len(integrated.Solids())!=1 or bb.ymin>13.1 or bb.zmin>-188:raise RuntimeError('Integrated motor cradle lost its motor seat or limb')
    if integrated.intersect(motor_envelope((0,58.4,0))).Volume()>1e-4:raise RuntimeError('Motor cradle overlaps actuator')
    add(leg+'_thigh_inner',integrated,'petg','dark','thigh',leg,prototype='thigh_inner',note='One structural motor cradle and thigh cheek. Knee actuator is recessed 12 mm into the limb root; metal flange and compression sleeves spread mounting loads.')
    outer_cheek=shell_half(True)
    add(leg+'_thigh_outer',outer_cheek,'petg','shell','thigh',leg,prototype='thigh_outer')
    disc=cyl(40,1.1,(0,103.7,0))
    disc=disc.cut(box(.8,.5,45,(0,104.75,0)).rotate((0,0,0),(0,1,0),15))
    digits=cq.Workplane('XY').text('170',5,.3,combine=True).val().rotate((0,0,0),(1,0,0),90).translate((0,104.9,-27))
    disc=disc.cut(digits)
    add(leg+'_hip_disc',disc,'aluminum','metal','thigh',leg,check=False,prototype='hip_disc')
    add(leg+'_hip_index',box(2,.5,8,(41,104.6,8),.2),'petg','orange','thigh',leg,check=False,prototype='hip_index')
    for j,(x,z) in enumerate(SHELL_BOLTS):
        add(leg+f'_sleeve_{j}',ring(4,2.2,cheek_roof(z)-67,64,z,x),'aluminum','metal','thigh',leg,check=False,prototype=f'sleeve_{j}')
        add(leg+f'_bolt_{j}',cyl(2,cheek_roof(z)-59,(x,59,z)).fuse(cyl(3.8,2,(x,cheek_roof(z)-2,z))),'steel','dark','thigh',leg,check=False,prototype=f'bolt_{j}')
    adapter=ring(18,5,5,58.4).fuse(ring(8,5,1.6,63.4))
    for a in range(0,360,60):adapter=adapter.cut(cyl(2.2,7,(12*math.cos(math.radians(a)),57.4,12*math.sin(math.radians(a)))))
    add(leg+'_knee_drive_adapter',adapter,'aluminum','metal','crank',leg,prototype='knee_drive_adapter')
    add(leg+'_input_crank',crank(),'aluminum','plate','crank',leg,prototype='input_crank')
    for a in range(0,360,60):
        x,z=12*math.cos(math.radians(a)),12*math.sin(math.radians(a))
        add(leg+f'_input_bolt_{a}',cyl(3.8,2.2,(x,79.2,z)),'steel','metal','crank',leg,check=False,note='Recessed M4 low-head envelope; 0.6 mm below crank face. Select screw length after confirming motor engagement.')
    add(leg+'_pushrod',rod(),'steel','metal','rod',leg,prototype='pushrod')
    out=crank(output=True).rotate((0,0,0),(0,1,0),P['crank_phase_deg'])
    add(leg+'_output_crank',out,'aluminum','plate','knee',leg,prototype='output_crank')
    add(leg+'_knee_axle',ring(6,4,44,61,-170),'steel','metal','thigh',leg,check=False,prototype='knee_axle',note='Fixed 12 x 8 mm tubular shaft ties the thigh cheeks; shin rotates on two bearings.')
    add(leg+'_knee_inner_spacer',ring(8,6.05,16,75,-170),'steel','metal','thigh',leg,check=False,prototype='knee_inner_spacer')
    for y in [67,91]:
        carrier=ring(17,14.1,8,y)
        if y==67:
            carrier=carrier.fuse(ring(22,8.2,2,75))
            for angle in [138,258,378]:
                carrier=carrier.cut(cyl(1.25,12,(17.5*math.cos(math.radians(angle)),66,17.5*math.sin(math.radians(angle)))))
        add(leg+f'_shin_carrier_{y}',carrier,'aluminum','metal','knee',leg,prototype=f'shin_carrier_{y}',check=False)
        add(leg+f'_bearing_{y}',ring(14,6,8,y),'steel','metal','knee',leg,mass=.022,prototype=f'bearing_{y}',check=False)
    add(leg+'_shin_inner',shin_half(),'petg','dark','knee',leg,prototype='shin_inner')
    add(leg+'_shin_outer',shin_half(True),'petg','dark','knee',leg,prototype='shin_outer')
    add(leg+'_knee_bezel',ring(18,11.2,1.6,105,-170),'petg','dark','thigh',leg,check=False,prototype='knee_bezel')
    add(leg+'_knee_end_cap',ring(11,3.2,1.5,105,-170),'aluminum','metal','thigh',leg,check=False,prototype='knee_end_cap')
    center=cq.Vector(0,83,-P['shank_to_foot_center'])
    sole=cq.Solid.makeSphere(P['foot_radius'],center,angleDegrees1=-90,angleDegrees2=0)
    sole=sole.rotate(center.toTuple(),(0,84,-P['shank_to_foot_center']),30)
    base=cq.Wire.makeCircle(P['foot_radius'],center,cq.Vector(.5,0,math.sqrt(3)/2))
    neck=cq.Wire.makeCircle(9,center+cq.Vector(0,0,20),cq.Vector(0,0,1))
    boot=cq.Solid.makeLoft([base,neck],ruled=True)
    foot=sole.fuse(boot,tol=1e-5).clean()
    add(leg+'_foot',foot,'rubber','rubber','knee',leg,prototype='foot',note='Rounded boot envelope with a shin-aligned neck. Attachment cavity and retaining fastener remain to be detailed.')

def export():
    step_checks=[]
    (OUT/'print-stl').mkdir(exist_ok=True)
    (OUT/'step-parts').mkdir(exist_ok=True)
    printable={name for name in prototypes if next(p for p in parts if p['mesh']==name)['material']=='petg'}
    for folder,extension,expected in [('stl','stl',set(prototypes)),('step-parts','step',set(prototypes)),('print-stl','stl',printable)]:
        for old in (OUT/folder).glob('*.'+extension):
            if old.stem not in expected:old.unlink()
    print_manifest=[]
    for name,s in prototypes.items():
        print('Checking STEP',name,flush=True)
        target=OUT/'step-parts'/f'{name}.step'
        original=s
        expected=len(s.Solids())
        cq.exporters.export(s,str(target))
        reopened=cq.importers.importStep(str(target)).val()
        converted=False
        if len(reopened.Solids())!=expected:
            # Convert offset/extrusion geometry to supported spline surfaces when
            # the STEP writer otherwise drops trimmed faces. Validate the result.
            s=s.toNURBS();cq.exporters.export(s,str(target))
            reopened=cq.importers.importStep(str(target)).val();converted=True
        if len(reopened.Solids())!=expected or not reopened.isValid():raise RuntimeError('STEP lost solid topology: '+name)
        relative_error=abs(reopened.Volume(1e-5)-s.Volume(1e-5))/max(s.Volume(1e-5),1)
        if relative_error>1e-4:raise RuntimeError('STEP changed volume: '+name)
        a=original.BoundingBox();b=s.BoundingBox()
        delta=max(abs(getattr(a,k)-getattr(b,k)) for k in ['xmin','xmax','ymin','ymax','zmin','zmax'])
        if delta>.01:raise RuntimeError('Spline conversion changed envelope: '+name)
        if converted:
            prototypes[name]=s
            vertices,faces=s.tessellate(.025,.05) if name=='front_fascia' else s.tessellate(.38,.18)
            meshes[name]={'vertices':[[round(v.x,5),round(v.y,5),round(v.z,5)] for v in vertices],'faces':[list(f) for f in faces]}
            for part in parts:
                if part['mesh']!=name:continue
                solids[part['name']]=s
                part['mass_kg']=round(part['mass_kg']*s.Volume()/original.Volume(),6)
                part['volume_mm3']=round(s.Volume(),3);part['com_mm']=list(s.Center().toTuple());part['bounds_mm']=[b.xlen,b.ylen,b.zlen]
        step_checks.append({'part':name,'expected_solids':expected,'reopened_solids':len(reopened.Solids()),'valid':reopened.isValid(),'spline_conversion':converted,'conversion_bounds_delta_mm':delta,'roundtrip_relative_volume_error':relative_error,'volume_integration_tolerance':1e-5})
        cq.exporters.export(s,str(OUT/'stl'/f'{name}.stl'),tolerance=.05 if name in ['front_fascia','sensor_bezel'] else .15,angularTolerance=.1)
        prototype_part=next(p for p in parts if p['mesh']==name)
        if prototype_part['material']=='petg':
            oriented=s
            if name in ['body_nose_surround','front_fascia','sensor_bezel']:
                oriented=s.rotate((0,0,0),(0,1,0),90)
            elif not name.startswith(('body_','belly_','rail_')):
                base_name=name.removesuffix('_right')
                angle=(-90 if base_name.endswith('_outer') else 90)*(-1 if name.endswith('_right') else 1)
                oriented=s.rotate((0,0,0),(1,0,0),angle)
            b=oriented.BoundingBox()
            oriented=oriented.translate((-(b.xmin+b.xmax)/2,-(b.ymin+b.ymax)/2,-b.zmin))
            cq.exporters.export(oriented,str(OUT/'print-stl'/f'{name}.stl'),tolerance=.15,angularTolerance=.15)
            print_mesh=trimesh.load_mesh(OUT/'print-stl'/f'{name}.stl')
            print_mesh.merge_vertices(digits_vertex=4)
            print_mesh.update_faces(print_mesh.nondegenerate_faces())
            print_mesh.remove_unreferenced_vertices()
            print_mesh.apply_translation([0,0,-print_mesh.bounds[0,2]])
            print_mesh.export(OUT/'print-stl'/f'{name}.stl')
            print_manifest.append({'part':name,'file':f'print-stl/{name}.stl','orientation':'Leg parting planes can be oriented parallel to the bed. Compound-curved skins and body covers require a support and bridge review in the slicer.','status':'geometry prototype; load qualification required'})
    poses=POSES['stand'];assembly=cq.Assembly(name='Tinfox_170')
    for p in parts:
        m=matrix(p,poses)
        rv=Rotation.from_matrix(m[:3,:3]).as_rotvec();angle=np.linalg.norm(rv)
        axis=rv/angle if angle>1e-12 else np.array([1,0,0])
        loc=cq.Location(cq.Vector(*m[:3,3]),cq.Vector(*axis),math.degrees(angle))
        s=solids[p['name']]
        c=p['color'];rgb=tuple(int(c[i:i+2],16)/255 for i in (1,3,5))
        assembly.add(s,name=p['name'],loc=loc,color=cq.Color(*rgb))
    assembly.export(str(OUT/'tinfox-assembly.step'))
    assembly.export(str(OUT/'tinfox.glb'))
    print('STEP assembly exported',flush=True)
    # Separate-part STEP geometry also preserves machining candidates for Fusion.
    cq.exporters.export(cq.Compound.makeCompound(list(prototypes.values())),str(OUT/'leg-and-panel-parts.step'))
    data={'parameters':P,'parts':parts,'meshes':meshes,'poses':POSES,'units':'mm','status':'engineering prototype; not load-qualified'}
    raw=json.dumps(data,separators=(',',':'))
    (OUT/'model.json').write_text(raw)
    (ROOT/'review'/'model.json').write_text(raw)
    (OUT/'manifest.json').write_text(json.dumps({'parameters':P,'parts':parts,'model_sha256':hashlib.sha256(raw.encode()).hexdigest()},indent=2))
    (OUT/'print-manifest.json').write_text(json.dumps(print_manifest,indent=2))
    (OUT/'step-roundtrip.json').write_text(json.dumps({'model_sha256':hashlib.sha256(raw.encode()).hexdigest(),'parts':step_checks,'scope':'Every individual STEP reopened as the expected number of valid solids; volume and conversion envelope checked. Does not qualify machining tolerances or tool paths.'},indent=2))
    fit=[]
    for a,b in [('FL_thigh_inner','FL_knee_motor'),('FL_thigh_inner','FL_motor_mount_ring'),('FL_hip_hub','FL_knee_motor'),('FL_thigh_inner','FL_thigh_outer'),('FL_thigh_outer','FL_hip_disc'),('body_nose_surround','front_fascia'),('body_nose_surround','body_front_0'),('FL_shoulder_cover','FL_thigh_inner')]:
        sa,sb=solids[a],solids[b]
        overlap=sa.intersect(sb).Volume()
        fit.append({'parts':[a,b],'intersection_mm3':max(0,overlap),'distance_mm':sa.distance(sb)})
    (OUT/'mounting-fit.json').write_text(json.dumps({'model_sha256':hashlib.sha256(raw.encode()).hexdigest(),'pairs':fit,'scope':'Exact nominal solids for selected rigidly attached interfaces. Does not qualify fits, screw engagement, thermal growth or strength.'},indent=2))

    print(f'{len(parts)} parts; {len(meshes)} unique meshes; {len(prototypes)} part prototypes; model {len(raw)/1e6:.1f} MB',flush=True)

if __name__=='__main__':
    print('Building body',flush=True);build_body()
    for leg in LEGS:print('Building '+leg,flush=True);build_leg(leg)
    export()
