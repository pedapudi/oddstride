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
from mesh_cleanup import clean_mesh
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
    for y in [67,91]:s=s.fuse(ring(24.5,19.2,8,y))
    return s.clean()

def shin_head_clearance(part):
    x=22*math.cos(math.radians(P["crank_phase_deg"]));z=-22*math.sin(math.radians(P["crank_phase_deg"]))
    part=part.cut(cyl(10.8,27,(x,71.5,z)))
    for y,h in [(74.7,7.4),(89.9,8.4)]:
        part=part.cut(box(13.6,h,16.6,(x/2,y+h/2,13),1.6))
    return part.cut(box(7.4,18.4,14.4,(-13,83,-2),1.6))

@cache
def shin_half(outer=False):
    # A fore/aft split passes through both bearing axes. Opening the structural
    # halves releases the bearings radially without a third access cover.
    blank=shin_blank()
    shell=blank.cut(box(70,16,100,(0,83,-30),3))
    wire=cq.Workplane('XZ',origin=(3.3,74.5,-105)).rect(14,62).val()
    wire=wire.fillet2D(3,wire.Vertices())
    shell=shell.cut(cq.Solid.extrudeLinear(wire,[],cq.Vector(0,17,0)))
    shell=shell.fuse(integrated_knee_head(),box(16.6,16.8,37.4,(-2,83,-30.5),3.2))
    for y in [70,90]:shell=shell.fuse(ring(19.4,14,8,y))
    for y in [67,98]:shell=shell.fuse(ring(19.4,12.8,3,y))
    for zz in [-29,-44]:shell=shell.fuse(cyl(3.2,24.8,(-2,70.4,zz)))
    for zz in [-37,-105]:
        # Broad contact lands are hard closure stops; sleeves carry clamp preload.
        shell=shell.fuse(box(32,16,16,(2,83,zz),3).intersect(blank))
        shell=shell.cut(cyl(2.2,42,(-20,83,zz),(1,0,0)))
        shell=shell.cut(cyl(4.05,16,(-4,83,zz),(1,0,0)))
        shell=shell.cut(cyl(3.8,12,(12,83,zz),(1,0,0)))
        pocket=cq.Workplane(cq.Plane(origin=(-7.3,83,zz),xDir=(0,1,0),normal=(1,0,0))).polygon(6,7.2/(3**.5/2)).extrude(7.4).val()
        shell=shell.cut(pocket)
    x=22*math.cos(math.radians(P['crank_phase_deg']));z=-22*math.sin(math.radians(P['crank_phase_deg']))
    shell=shell.cut(hex_nut(8.2,4.3,x,71.6,z,.01)).cut(cyl(2.8,6.4,(x,71.6,z)))
    for y in [70,90]:shell=shell.cut(cyl(14,8,(0,y,0)))
    # Finish functional bores after joining the structural webs.
    shell=shell.cut(cyl(3.025,4.1,(x,77.9,z))).cut(cyl(3.05,8.2,(x,90,z)))
    shell=shell.cut(cyl(6.3,8.4,(x,81.8,z))).cut(cyl(5.3,6,(x,98,z)))
    # Preserve a continuous axle/spacer passage after fusing the rocker webs.
    shell=shell.cut(cyl(8.2,48,(0,60,0)))
    # Insert the M5 nut from the open structural split; the rear half closes it.
    shell=shell.cut(box(9.4,4.3,8.2,(4.6,73.75,z)))
    return shell.intersect(box(60,120,230,(30 if outer else -30,83,-85))).clean()

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
    s=(wp.moveTo(-7.5,0).threePointArc((0,7.5),(7.5,0))
       .lineTo(3,-12).lineTo(3,-158).lineTo(7.5,-170)
       .threePointArc((0,-177.5),(-7.5,-170)).lineTo(-3,-158)
       .lineTo(-3,-12).close().extrude(-6).val())
    for z in [0,-170]:s=s.cut(cyl(4,8,(0,82,z)))
    return s.clean()

def hex_nut(af,depth,x,y,z,bore):
    wp=cq.Workplane(cq.Plane(origin=(x,y,z),xDir=(1,0,0),normal=(0,1,0)))
    return wp.polygon(6,af/(3**.5/2)).extrude(depth).val().cut(cyl(bore,depth+2,(x,y-1,z)))

def pivot_ears(x,z):
    # 16 mm shoulder pin seats at Y78; M5 thread remains inside the inner ear.
    inner=cyl(10.5,10,(x,71.8,z))
    outer=cyl(10.5,7.8,(x,90.2,z))
    inner=inner.cut(cyl(2.1,6.4,(x,71.6,z))).cut(cyl(3.025,4.1,(x,77.9,z)))
    outer=outer.cut(cyl(3.05,8.2,(x,90,z)))
    return inner,outer

@cache
def integrated_input_crank():
    # A common solid replaces the output adapter, crank and separate fork brackets.
    base=ring(18,5,7.4,70.4)
    for angle in range(0,360,60):
        x,z=12*math.cos(math.radians(angle)),12*math.sin(math.radians(angle))
        base=base.cut(cyl(2.2,12,(x,70,z))).cut(cyl(4,4,(x,77,z)))
    plate=crank().intersect(box(100,4.8,100,(0,79.4,0)))
    inner,outer=pivot_ears(P['crank_radius'],0)
    # The rod leaves the eye toward +Z in the crank frame over the specified range.
    bridge=box(14,22.2,4.8,(21,86.9,-10.3),.7)
    for yy,depth in [(78.8,6),(94.1,7.8)]:
        bridge=bridge.fuse(box(14,depth,5.2,(21,yy,-7.7),.8))
    s=base.fuse(plate,inner,outer,bridge).clean()
    s=s.cut(cyl(2.1,6.4,(22,71.6,0))).cut(cyl(3.025,4.1,(22,77.9,0)))
    return s

@cache
def integrated_knee_head():
    # Two opposed bearing pockets, integral rocker/fork and keyed shin attachment.
    inner=ring(19,14,8,70).fuse(ring(19,8.2,1.8,78))
    outer=ring(19,14,8,90).fuse(ring(19,12.8,.8,89.2))
    rear_bridge=box(7,18,14,(-13,83,-2),2)
    tongue=box(16,15.6,37,(-2,83,-30.5),3.2)
    head=inner.fuse(outer,rear_bridge,tongue)
    x=22*math.cos(math.radians(P['crank_phase_deg']));z=-22*math.sin(math.radians(P['crank_phase_deg']))
    a,b=pivot_ears(x,z)
    # Short radial webs meet the bearing housings; the center stays open for the rod.
    for y,h in [(75,6.8),(90.2,7.8)]:
        web=box(13,h,16,(x/2,y+h/2,13),1.8)
        head=head.fuse(web)
    head=head.fuse(a,b)
    head=head.cut(cyl(6.3,8.4,(x,81.8,z)))
    head=head.cut(cyl(2.1,6.4,(x,71.6,z))).cut(cyl(3.025,4.1,(x,77.9,z))).cut(cyl(3.05,8.2,(x,90,z)))
    # Finish the bearing pockets after joining the webs. Opposed inner shoulders.
    for y in [70,90]:head=head.cut(cyl(14,8,(0,y,0)))
    for zz in [-29,-44]:
        head=head.fuse(cyl(3,24.8,(-2,70.4,zz))).cut(cyl(1.7,34,(-2,66,zz)))
    return head.clean()

def pivot_pin(x,z):
    head=cyl(5,5,(x,98,z))
    socket=cq.Workplane(cq.Plane(origin=(x,100.5,z),xDir=(1,0,0),normal=(0,1,0))).polygon(6,3/(3**.5/2)).extrude(3).val()
    return cyl(2.5,6,(x,72,z)).fuse(cyl(3,20,(x,78,z)),head.cut(socket))

def rod_bush(z,outer=False):
    # GFM-0608-04: 3 mm sleeve + 1 mm flange, installed from opposite faces.
    if not outer:return ring(4,3.02,3,83,z).fuse(ring(6,3.02,1,82,z))
    return ring(4,3.02,3,86,z).fuse(ring(6,3.02,1,89,z))

def add(name,shape,material='petg',color='shell',group='body',leg=None,mass=None,check=True,prototype=None,note=''):
    if leg and group in ['thigh','crank','rod','knee'] and not name.endswith('_hip_hub') and '_hip_output_bolt_' not in name:
        motor_parts=('_knee_motor','_motor_mount_ring')
        inset=P['motor_stack_inset_mm'] if name.endswith(motor_parts) or '_pod_' in name or name.endswith(('_thigh_inner','_motor_service_ring')) or name.endswith('_knee_drive_adapter') else P['motor_stack_inset_mm']+P['limb_recess_mm']
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

def face_x(y,z=2):
    # Independent crowns preserve the lateral bow at every height while adding
    # a pronounced vertical barrel profile to the face and bezel.
    return (245.4+P['front_face_crown_mm']*(1-(y/98.0)**2)
            +P['front_face_vertical_crown_mm']*(1-((z-2)/42.0)**2))

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
    # The chassis crossmembers sit below the lid; lid ribs do not obstruct removal.
    for x in [-28,28]:shell=shell.fuse(box(2.4,170,6,(x,0,47)).intersect(outer))
    # Local inside reliefs preserve clearance to the fixed roll-motor cartridges.
    for front in [-1,1]:
        for side in [-1,1]:
            shell=shell.cut(cyl(41.25,49.4,(front*70.3,side*68,0),(front,0,0)))
            shell=shell.cut(cyl(42,7,(front*111.7,side*68,0),(front,0,0)))
            shell=shell.cut(cyl(38,20,(front*113.5,side*68,0),(front,0,0)))
            for z in [-12,24]:shell=shell.cut(box(14,16,14,(front*125.5,side*94.5,z)))
    for y in [-102,102]:shell=shell.cut(box(268,3,55,(0,y,8),.8))
    shell=shell.cut(box(148,202,70,(0,0,-55),8))
    nose_return_fasteners=[]
    nominal_shell=shell
    # The corner pockets follow the roll swept volume, including the thigh root.
    samples=[]
    for a in np.deg2rad(np.arange(-61,62)):
        for yy,zz in [(-51,-55),(-51,55),(111,-55),(111,55)]:
            samples.append([yy*np.cos(a)-zz*np.sin(a),yy*np.sin(a)+zz*np.cos(a)])
    pts=np.array(samples);hull=pts[ConvexHull(pts).vertices].tolist()
    blank=(cq.Workplane(cq.Plane(origin=(-58.5,0,0),xDir=(0,1,0),normal=(1,0,0)))
           .polyline(hull).close().wires().toPending().offset2D(2,kind='arc').extrude(117).val())
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
            shell=shell.cut(box(112,62,134,(front*205,side*135,0),6))
    # The fixed sensor face narrows toward the motors behind its outer edge.
    face_region=(cq.Workplane('XY').polyline([(230,-38),(232.2,-42),(232.2,42),(230,38)])
                 .close().extrude(140).val().translate((0,0,-70)))
    for front in [-1,1]:
        region=face_region if front>0 else face_region.mirror('YZ')
        shell=shell.fuse(nominal_shell.intersect(region))
    end_caps={}
    for tag,x0,x1 in [('aft',-232,-126),('center',-125.4,125.4),('front',126,233.0)]:
        section=shell.intersect(box(x1-x0,240,140,((x0+x1)/2,0,0)))
        if tag=='center':
            # One top-and-side clamshell, open underneath for printing and service.
            lid=section.intersect(box(270,250,80,(0,0,30)))
            for side in [-1,1]:
                for x in [-112,112]:
                    boss=box(9,7.5,14,(x,side*106.25,22),.5).intersect(outer)
                    lid=lid.fuse(boss).cut(box(9.4,5.4,80,(x,side*103.5,-13.3),.3)).cut(box(10,4,100,(x,side*101.5,-5))).cut(cyl(1.7,12,(x,side*101,22),(0,side,0)))
            # Slots are open downward; no inboard tabs can trap the lifted shell.
            for front in [-1,1]:
                for side in [-1,1]:lid=lid.cut(cyl(42,7,(front*111.7,side*68,0),(front,0,0)))
            for front in [-1,1]:
                lid=lid.cut(box(32,260,100,(front*125.4,0,-35.8),2))
            add('body_center_0',lid.clean(),prototype='body_center_0',note='One 2.8 mm top-and-side clamshell. Four lateral screws attach to chassis bosses. Lift straight upward after removing screws; print roof-down, interior open upward.')
            belly=section.intersect(box(270,250,38,(0,0,-29.3)))
            add('belly_center_0',belly.clean(),color='dark',prototype='belly_center_0',note='Separate lower protective shell around the removable battery opening; does not carry actuator loads.')
        else:
            # Deep longitudinal return rib turns the end skins into connected caps.
            rib=outer.cut(torso(9)).intersect(box(x1-x0,28,40,((x0+x1)/2,0,40)))
            rib=rib.cut(box(14,184,90,((1 if tag=="front" else -1)*121,0,-2.2)))
            section=section.fuse(rib)
            front=1 if tag=='front' else -1
            lap=box(26,48,3.5,(front*127,0,44.55),.5)
            for yy in [-18,18]:
                lap=lap.cut(cyl(1.7,8,(front*121,yy,40),(0,0,1)))
                lap=lap.cut(cq.Solid.makeCone(1.7,3,1.3,cq.Vector(front*121,yy,45),cq.Vector(0,0,1)))
                nut=hex_nut(5.5,2.4,0,0,0,1.5).rotate((0,0,0),(1,0,0),90).translate((front*121,yy,40.8))
                add(f'end_cap_nut_{front}_{yy}',nut,'steel','metal',check=False)
                screw=cyl(1.5,6.7,(front*121,yy,38.3),(0,0,1)).fuse(cq.Solid.makeCone(1.5,2.9,1.3,cq.Vector(front*121,yy,45),cq.Vector(0,0,1)))
                add(f'end_cap_screw_{front}_{yy}',screw,'steel','dark',check=False,note='M3 x 8 countersunk screw joins end-cap lap to chassis crossmember independently of the removable lid.')
            end_caps[tag]=section.fuse(lap).clean()
    add('body_aft_0',end_caps['aft'],prototype='body_aft_0',note='Combined rear upper/lower shell, 2.8 mm nominal skin with a deep central return rib. Motor loads bypass this protective module.')
    # The service-panel perimeter and identification are actual solids.
    for side in [-1,1]:
        for x,z in [(-112,22),(112,22)]:
            head=cyl(2.6,.7,(x,side*111.3,z),(0,side,0)).cut(cyl(1.1,1,(x,side*111.5,z),(0,side,0)))
            add(f'body_service_screw_{side}_{x}_{z}',head,'steel','dark',check=False,note='Upper M3 cover fastener; panel is located by two integral tabs. Pilot-boss screw specification remains provisional.')
    word=cq.Workplane('XZ',origin=(-30,-111.28,-4)).text('tinfox',10,.12,combine=True).val()
    add('body_wordmark',word,'envelope','dark',check=False,mass=.002)
    mark=cq.Workplane('XZ',origin=(96,-111.28,-17)).text('01',4,.12,combine=True).val()
    add('body_serial',mark,'envelope','dark',check=False,mass=.001)
    add('body_status_dot',cyl(2,.7,(-81,-111.3,-13),(0,-1,0)),'envelope','orange',check=False,mass=.001)
    for side in [-1,1]:
        wp=cq.Workplane(cq.Plane(origin=(0,side*97.2,0),xDir=(1,0,0),normal=(0,-1,0)))
        outline=wp.polyline([(-66,-6),(66,-6),(68,-44),(61,-66),(-61,-66),(-68,-44)]).close().val()
        outline=outline.fillet2D(2.5,outline.Vertices())
        panel=cq.Solid.extrudeLinear(outline,[],cq.Vector(0,side*1.6,0))
        panel=cq.Workplane(obj=panel).edges().fillet(.5).val()
        for x in [-52,52]:panel=panel.cut(box(13,12,22,(x,side*98,-6)))
        for x in [-50,50]:panel=panel.cut(cyl(1.7,5,(x,side*96,-59),(0,side,0)))
        add(f'battery_side_panel_{side}',panel,'petg','dark',prototype=f'battery_side_panel_{side}',note='Compact lower trim panel stays within the cassette withdrawal envelope. Two M3 clearance holes align with integral cassette pilot bosses; screw specification remains provisional.')
        for x in [-50,50]:add(f'battery_access_screw_{side}_{x}',cyl(1.5,8,(x,side*98.9,-59),(0,-side,0)).fuse(cyl(2.5,.7,(x,side*98.9,-59),(0,side,0))).cut(cyl(1,1,(x,side*99.1,-59),(0,side,0))),'steel','metal',check=False)
        add(f'battery_access_latch_{side}',box(22,1.8,4,(0,side*100.0,-52),.5),'petg','orange',check=False,prototype=f'battery_access_latch_{side}')
    # Two removable packs sit alongside one another between the four motor stations.
    for side in [-1,1]:
        y=side*44.5
        add(f'battery_{side}',box(*P['battery_envelope_mm'],(0,y,P['battery_center_z']),7),'envelope','dark',mass=P['battery_each_mass_kg_assumed'],note='Pack plus adapter envelope; exact commercial pack remains unselected.')
        add(f'battery_latch_{side}',box(18,5,9,(0,side*91,-50),2),'petg','orange',check=False,prototype=f'battery_latch_{side}')
    cassette=box(140,194,69.5,(0,0,-34.75),12).cut(box(136,190,70,(0,0,-32.5),10))
    # Integral guides remove two separately installed rails. Their bridges stay
    # outside the battery envelopes and connect to the enclosure side walls.
    for side in [-1,1]:
        y=side*90.5
        rail=box(134,5,61,(0,y,-36),2).cut(cq.Workplane(obj=box(112,7,45,(0,y,-34))).edges('|Y').fillet(7).val())
        for x in [-60,60]:rail=rail.fuse(box(9,6,54,(x,side*94,-36),.5))
        cassette=cassette.fuse(rail)
        gusset=(cq.Workplane('YZ',origin=(-56,0,0)).polyline([(side*97,-20.5),(side*97,-5.5),(side*88,-5.5),(side*88,-11.5)]).close().extrude(112).val())
        cassette=cassette.fuse(gusset)
        for x in [-50,50]:
            cassette=cassette.fuse(box(9,7.5,9,(x,side*93.25,-59),.5))
            cassette=cassette.cut(cyl(1.25,9,(x,side*89,-59),(0,side,0)))
        for x in [-52,52]:
            boss=box(12,10.3,16,(x,side*94.15,-8),.7)
            cassette=cassette.fuse(boss)
            cassette=cassette.cut(cyl(1.7,15,(x,side*87,-6),(0,side,0)))
            # Top-loaded M3 nut pocket: 5.8 mm flats, 2.8 mm axial clearance.
            # Flats hold the nut against rotation; install nuts before closing the upper frame.
            pocket=box(5.8,2.8,12.4,(x,side*93.8,-3.2))
            cassette=cassette.cut(pocket)
            nut=(cq.Workplane(cq.Plane(origin=(x,side*92.6,-6),xDir=(1,0,0),normal=(0,side,0)))
                 .polygon(6,5.5/(3**.5/2)).extrude(2.4).val())
            # Rotate the hex so its two vertical flats fit the insertion slot.
            nut=nut.rotate((x,0,-6),(x,1,-6),30)
            nut=nut.cut(cyl(1.25,5,(x,side*91.5,-6),(0,side,0)))
            add(f'cassette_nut_{side}_{x}',nut,'steel','metal',check=False,note='M3 DIN 934 nut envelope, 5.5 mm flats and 2.4 mm thickness; retained in an integral top-loading pocket.')
    add('battery_cassette',cassette.clean(),color='dark',prototype='battery_cassette',note='One-piece underside cassette with integral pack guides and four captive-nut pockets. Four side-access M3 screws attach the cassette independently to the frame. Pack adapters and contacts remain unselected.')
    skid_wire=cq.Workplane('XY',origin=(0,0,-71)).rect(138,190).val()
    skid_wire=skid_wire.fillet2D(15,skid_wire.Vertices())
    add('battery_skid',cq.Solid.extrudeLinear(skid_wire,[],cq.Vector(0,0,1.5)),'aluminum','plate',prototype='battery_skid')
    # Two metal side rails and two removable transverse ties form the motor frame.
    # A fixed flat lower brace carries frame loads independently of the electronics deck.
    for y in [-102,102]:
        side=1 if y>0 else -1
        beam=box(260,2,54,(0,y,8),.7)
        for x in [-91,91]:beam=beam.cut(cq.Workplane(obj=box(56,6,52,(x,y,0))).edges('|Y').fillet(4).val())
        beam=beam.cut(cq.Workplane(obj=box(80,6,28,(0,y,5))).edges('|Y').fillet(6).val())
        top_flange=box(260,8,2,(0,side*99,33),.5).cut(box(138,20,6,(0,side*99,33)))
        top_flange=top_flange.fuse(box(138,6,2,(0,side*105,33),.5))
        beam=beam.fuse(top_flange)
        for xx in [-125.5,125.5]:
            for zz in [-12,24]:
                beam=beam.fuse(cyl(5.5,5,(xx,side*101,zz),(0,side,0)))
                beam=beam.cut(cyl(1.7,9,(xx,side*99,zz),(0,side,0)))
        for xx in [-112,112]:
            beam=beam.fuse(box(9,5,9,(xx,side*103.5,22),.5))
            beam=beam.cut(cyl(1.25,9,(xx,side*100,22),(0,side,0)))
        for x in [-52,52]:beam=beam.cut(cyl(1.7,8,(x,side*99,-6),(0,side,0)))
        for x in [-124,-118,118,124]:beam=beam.cut(cyl(1.7,8,(x,side*99,29),(0,0,1)))
        for front in [-1,1]:beam=beam.cut(cyl(40.75,49.4,(front*70.3,side*68,0),(front,0,0)))
        # Broad integral ledges support the fixed lower brace; all holes face up.
        for xx in [-63,63]:
            ledge=box(12,10,4,(xx,side*98, -1.5),.4)
            ledge=ledge.cut(box(13,11.3,17,(52 if xx>0 else -52,side*94.15,-8)))
            beam=beam.fuse(ledge)
            beam=beam.cut(cyl(1.25,7,(xx,side*97,-4),(0,0,1)))
        beam=beam.intersect(torso(3.4)).clean()
        add(f'chassis_beam_{y}',beam.clean(),'aluminum','plate',prototype=f'chassis_beam_{y}',note='Metal C-section motor rail with thickened cartridge pads and lid mounting bosses. Printed versions are unloaded fit mockups; frame strength requires analysis and testing.')
    for x in [-121,121]:
        outline=[(-101,34),(-97,34),(-90,40.8),(90,40.8),(97,34),(101,34),(101,36),(97,36),(90,42.8),(-90,42.8),(-97,36),(-101,36)]
        tie=cq.Workplane('YZ',origin=(x-6,0,0)).polyline(outline).close().extrude(12).val()
        for side in [-1,1]:
            for dx in [-3,3]:
                tie=tie.cut(cyl(1.7,6,(x+dx,side*99,31),(0,0,1))).cut(cq.Solid.makeCone(1.7,3,1.3,cq.Vector(x+dx,side*99,34.7),cq.Vector(0,0,1)))
                bolt=cyl(1.5,6.7,(x+dx,side*99,28),(0,0,1)).fuse(cq.Solid.makeCone(1.5,2.9,1.3,cq.Vector(x+dx,side*99,34.7),cq.Vector(0,0,1)))
                add(f'chassis_tie_bolt_{x}_{side}_{dx}',bolt,'steel','metal',check=False,note='M3 x 8 nominal countersunk metal-frame tie screw; nut below the rail flange.')
                nut=hex_nut(5.5,2.4,0,0,0,1.5).rotate((0,0,0),(1,0,0),90).translate((x+dx,side*99,32))
                add(f'chassis_tie_nut_{x}_{side}_{dx}',nut,'steel','metal',check=False)
        for yy in [-18,18]:tie=tie.cut(cyl(1.7,6,(x,yy,38),(0,0,1)))
        add(f'chassis_crossmember_{x}',tie,'aluminum','plate',prototype=f'chassis_crossmember_{x}',note='Removable top transverse tie. Two screws per rail resist joint rotation; caps mount independently; the computer tray lifts between the two end crossmembers.')
    for side in [-1,1]:
        for xx in [-125.5,125.5]:
            for zz in [-12,24]:
                bolt=cyl(1.5,12,(xx,side*106,zz),(0,-side,0)).fuse(cyl(2.75,3,(xx,side*106,zz),(0,side,0)))
                add(f'chassis_bolt_{side}_{xx}_{zz}',bolt,'steel','dark',check=False,note='M3 x 12 nominal cartridge screw through the thickened rail pad; confirm engagement in cartridge ear.')
    # Independent cassette attachments remain side-accessible after removing the cover.
    for side in [-1,1]:
        for x in [-52,52]:
            bolt=cyl(1.5,12,(x,side*103,-6),(0,-side,0)).fuse(cyl(2.75,3,(x,side*103,-6),(0,side,0)))
            add(f'cassette_screw_{side}_{x}',bolt,'steel','dark',check=False,note='Independent M3 x 12 cassette-to-frame screw. Does not retain the electronics deck.')
    # A flat H-shaped metal diaphragm stays with the motor frame during service.
    brace=box(22,202,3,(-56,0,2),.3).fuse(box(22,202,3,(56,0,2),.3),box(112,14,3,(0,0,2),.3))
    for side in [-1,1]:
        for x in [-63,63]:
            brace=brace.cut(cyl(1.7,6,(x,side*97,-.5),(0,0,1)))
            bolt=cyl(1.5,6,(x,side*97,-2.5),(0,0,1)).fuse(cyl(2.75,3,(x,side*97,3.5),(0,0,1)))
            add(f'chassis_brace_screw_{side}_{x}',bolt,'steel','dark',check=False,note='M3 x 6 socket screw into integral metal rail ledge; verify tapped engagement. Retained during electronics or battery service.')
        for x in [-52,52]:brace=brace.cut(cyl(1.25,6,(x,side*88,-.5),(0,0,1)))
    add('chassis_lower_brace',brace.clean(),'aluminum','plate',prototype='chassis_lower_brace',note='Flat 3 mm aluminum frame diaphragm with four rail attachments and four tapped deck mounts. Carries the lower rail connection independently of the deck. Plastic copy is an unloaded fit mockup; frame stiffness and joints require qualification.')
    # One flat extrusion prints without support, side holes or mounting ears.
    shelf=cq.Workplane('XY',origin=(0,0,3.5)).rect(134,186).extrude(4).edges('|Z').fillet(6).val()
    for x in [-26,26]:
        for y in [-49,0,49]:
            opening=cq.Workplane('XY',origin=(x,y,3)).rect(36,34).extrude(6).edges('|Z').fillet(5).val()
            shelf=shelf.cut(opening)
    for side in [-1,1]:
        for x in [-52,52]:
            shelf=shelf.cut(cyl(1.7,6,(x,side*88,3),(0,0,1)))
            bolt=cyl(1.5,8,(x,side*88,-.5),(0,0,1)).fuse(cyl(2.75,3,(x,side*88,7.5),(0,0,1)))
            add(f'tray_screw_{side}_{x}',bolt,'steel','dark',check=False,note='M3 x 8 top-access electronics-deck screw into the fixed brace. Battery and frame screws stay installed during removal.')
    for x in [-58,58]:
        for y in [-48,48]:
            shelf=shelf.cut(cq.Workplane('XY',origin=(x,y,3)).slot2D(18,3.4,angle=90).extrude(6).val())
    add('electronics_shelf',shelf.clean(),'petg','dark',prototype='electronics_shelf',note='Flat 134 x 186 x 4 mm PETG electronics deck. Six rounded openings, four top-access M3 holes and four adapter slots. Print broad face down without designed supports. Computer standoffs and wiring remain component-specific; the fixed metal brace carries frame loads.')
    add('electronics_clearance',box(*P['electronics_clearance_mm'],(0,0,25.5),2),'envelope','dark',check=True,note='Reserved 130 x 135 x 32 mm computer volume, 2 mm above the deck. Exact computer, standoffs, connectors and thermal airflow remain unselected.')
    add('lidar_base',cyl(31,4,(112,0,52),(0,0,1)),'envelope','dark',mass=.04,check=False)
    add('lidar',cyl(27,18,(112,0,56),(0,0,1)),'envelope','glass',mass=.15,check=False)
    add('lidar_lid',cyl(27,2,(112,0,74),(0,0,1)),'aluminum','metal',check=False,prototype='lidar_lid')
    # The wrap and service face share the body's actual outer envelope.
    nose=shell.intersect(box(10.2,250,150,(237.7,0,0)))
    tongue=torso(1.9).cut(torso(4.7)).intersect(box(22.5,11,30,(225.25,0,45)))
    bridge=outer.cut(torso(4.7)).intersect(box(5.2,11,30,(235.8,0,45)))
    nose=nose.fuse(tongue).fuse(bridge)
    for cut in body_sweep_cuts:nose=nose.cut(cut)
    for x,point,normal in nose_return_fasteners:
        nose=nose.cut(cyl(1.25,18,tuple(point-normal*15),tuple(normal)))
        head=cyl(2.6,.4,tuple(point-normal*.5),tuple(normal)).cut(cyl(1,.8,tuple(point-normal*.6),tuple(normal)))
        # The wrap and front return now form one part; no self-fastening screw.
    # Analytic rounded sections give the curved face a stable manufacturing solid.
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
        for x,w,h,r in [(241.3,200.3,87.7,18),(243.5,196.5,83.5,17),(276,192.5,80,16)]:
            wire=cq.Workplane('YZ',origin=(x,0,2)).rect(w-2*inset,h-2*inset).val()
            wires.append(wire.fillet2D(r-inset,wire.Vertices()))
        return cq.Solid.makeLoft(wires,ruled=True)
    fascia=fascia_blank().intersect(bowed_volume()).cut(fascia_blank(2.1).intersect(bowed_volume(2.1))).clean()
    aperture=cq.Workplane('YZ',origin=(240,0,5)).rect(168,40).extrude(40).edges('|X').fillet(10).val()
    fascia=fascia.cut(aperture)
    for y in [-89,89]:
        for z in [-27,27]:
            tab=box(3.8,17,3.2,(240.8,y/abs(y)*94,z),.6).intersect(outer)
            post=cyl(3.5,30,(239,y,z),(1,0,0)).intersect(bowed_volume(2.1))
            nose=nose.fuse(tab).fuse(post).cut(cyl(1.25,30,(238.5,y,z),(1,0,0)))
            fascia=fascia.cut(cyl(1.7,30,(239,y,z),(1,0,0))).cut(cyl(2.7,1.8,(face_x(y,z)-.6,y,z),(1,0,0)))
            add(f'front_fascia_screw_{y}_{z}',cyl(2.5,.35,(face_x(y,z)-.15,y,z),(1,0,0)).cut(cyl(1,.8,(face_x(y,z)-.3,y,z),(1,0,0))),'steel','dark',check=False)
    nose=nose.fuse(end_caps['front']).clean();fascia=fascia.cut(nose).intersect(box(100,300,150,(293,0,0))).clean()
    # The rear rim trim can leave a tiny detached strip above the body return.
    # Remove that offcut; it has no connection to the manufactured face.
    face_pieces=sorted(fascia.Solids(),key=lambda item:item.Volume(),reverse=True)
    for offcut in face_pieces[1:]:
        if offcut.Volume()>10 or offcut.BoundingBox().xmax>242:raise RuntimeError(f'Unexpected disconnected fascia material: {offcut.Volume()} {offcut.BoundingBox().xmax}')
    fascia=face_pieces[0]
    if len(nose.Solids())!=1:raise RuntimeError('Nose wrap and return tabs must form one connected solid')
    add('body_nose_surround',nose,'petg','shell',prototype='body_nose_surround',note='Combined front upper/lower cap and nose wrap with a deep central return rib and four fascia posts. Two M3-sized body holes and four fascia holes provide assembly access; final inserts, screws and load qualification remain unselected.')
    add('front_fascia',fascia,'petg','shell',prototype='front_fascia',note='Removable compound-curved face with an 8 mm horizontal crown and independent 10 mm vertical crown and a curved recessed sensor bezel. The rim preserves the body service gap.')
    bezel_mask=cq.Workplane('YZ',origin=(239,0,5)).rect(174,46).extrude(40).edges('|X').fillet(12).val()
    recess_mask=cq.Workplane('YZ',origin=(239,0,5)).rect(162,34).extrude(40).edges('|X').fillet(8).val()
    bezel=bezel_mask.intersect(bowed_volume(.7)).cut(bowed_volume(3.5))
    bezel=bezel.cut(recess_mask.cut(bowed_volume(2.4)))
    add('sensor_bezel',bezel,'petg','dark',check=False,prototype='sensor_bezel')
    visor=recess_mask.intersect(bowed_volume(1.9)).cut(bowed_volume(2.4))
    for y in [-52,52]:visor=visor.cut(cyl(11.2,40,(239,y,5),(1,0,0)))
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
    housing=housing.fuse(stator).cut(cyl(1.8,4,(-51,31,27),(0,0,1))).clean()
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
    hip_shroud=ring(43.5,41.5,44.4,-48.4).fuse(ring(43.5,12,2,-48.4),ring(44,41.5,3.5,-4.4))
    hip_shroud=hip_shroud.cut(box(20,54,46,(-front*45,-24,0),2))
    carrier=carrier.fuse(hip_shroud,tol=1e-5).clean()
    if not carrier.isValid():carrier=carrier.fix()
    if not carrier.isValid() or len(carrier.Solids())!=1:raise RuntimeError('Integrated carrier/shroud must be one solid')
    add(leg+'_motor_carrier',carrier,'aluminum','plate','roll',leg,prototype='motor_carrier_'+str(front),note='Single machined elbow carrier includes the roll-output coupling, bearing journal and perpendicular hip-stator mounting flange.')
    add(leg+'_hip_motor',motor_envelope(),'envelope','dark','roll',leg,P['motor_mass_kg'],True,'hip_motor')
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
    integrated=integrated.cut(cq.Solid.makeCone(42.0,41.25,.75,cq.Vector(0,13,0),cq.Vector(0,1,0)))
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
    # Open the captive stator-plate recess with a separate axial service ring.
    # Preserve the two structural cheek bolt bosses in the continuous thigh.
    def service_mask(radius,start,keep):
        cut=cyl(radius,40,(0,start,0))
        for x,z in SHELL_BOLTS:cut=cut.cut(cyl(keep,42,(x,start-1,z)))
        return cut
    service=integrated.intersect(service_mask(52,54.3,6.5)).clean()
    integrated=integrated.cut(service_mask(52.2,54.0,6.3)).clean()
    for piece in [integrated,service]:
        if not piece.isValid() or len(piece.Solids())!=1:raise RuntimeError('Motor service split must produce connected solids')
    # Recess the axle head flush to the inner cheek; an integral boss supports the sleeve.
    integrated=integrated.fuse(ring(11.2,6.1,5.9,51.5,-170)).cut(cyl(7.2,4.5,(0,48.9,-170))).clean()
    add(leg+'_thigh_inner',integrated,'petg','dark','thigh',leg,prototype='thigh_inner',note='Structural motor cradle and inner thigh; the stator-retaining ring is integral with the removable outer clamshell. Knee actuator is recessed 12 mm into the limb root; metal flange and compression sleeves spread mounting loads.')
    outer_cheek=shell_half(True).translate((0,4,0)).fuse(ring(18,11.2,1.6,109,-170),service.translate((0,12,0)))
    # A broad open collar replaces three narrow posts at the service-ring root.
    collar_web=ring(49.5,42,20.2,69.8)
    collar_web=collar_web.cut(box(80,40,70,(0,78,-62.5),3))
    outer_cheek=outer_cheek.fuse(collar_web)
    for a in POD_TIE_ANGLES:
        x,z=POD_TIE_RADIUS*math.cos(math.radians(a)),POD_TIE_RADIUS*math.sin(math.radians(a))
        outer_cheek=outer_cheek.cut(cyl(3.0,35,(x,76.9,z)))
    # Integral 3 mm motor face and knee surround avoid thin separate covers.
    outer_cheek=outer_cheek.fuse(cyl(40.8,3,(0,107.5,0)),ring(12.2,6.1,3,107.5,-170)).clean()
    add(leg+'_thigh_outer',outer_cheek,'petg','shell','thigh',leg,prototype='thigh_outer',note='One outer structural clamshell incorporates the motor service ring through a broad open collar outside the crank sweep. Remove this half to expose the motor and stator plate.')
    for j,(x,z) in enumerate(SHELL_BOLTS):
        add(leg+f'_sleeve_{j}',ring(4,2.2,cheek_roof(z)-63,64,z,x),'aluminum','metal','thigh',leg,check=False,prototype=f'sleeve_{j}')
        add(leg+f'_bolt_{j}',cyl(2,cheek_roof(z)-55,(x,59,z)).fuse(cyl(3.8,2,(x,cheek_roof(z)+2,z))),'steel','dark','thigh',leg,check=False,prototype=f'bolt_{j}')
    add(leg+'_input_crank',integrated_input_crank(),'aluminum','plate','crank',leg,prototype='input_crank',note='One machined output coupling and double-shear crank. Six motor-interface holes retain the vendor pattern; final screw length depends on actuator thread depth.')
    for a in range(0,360,60):
        x,z=12*math.cos(math.radians(a)),12*math.sin(math.radians(a))
        add(leg+f'_input_bolt_{a}',cyl(3.8,2.2,(x,77.2,z)),'steel','metal','crank',leg,check=False,note='Low-head M4 envelope; length and actuator engagement require vendor confirmation.')
    add(leg+'_pushrod',rod(),'steel','metal','rod',leg,prototype='pushrod',note='Steel 170 mm center-distance link with finished 8 mm bushing bores and enlarged 15 mm eyes.')
    for end,z in [('input',0),('output',-170)]:
        for outer in [False,True]:add(leg+f'_rod_bush_{end}_{int(outer)}',rod_bush(z,outer),'envelope','dark','rod',leg,mass=.000202,check=True,prototype='rod_bush_'+end+'_'+str(int(outer)),note='GFM-0608-04 dimensional envelope; paired flanges provide replaceable thrust faces. Wear life requires validation.')
    x,z=22*math.cos(math.radians(P['crank_phase_deg'])),-22*math.sin(math.radians(P['crank_phase_deg']))
    add(leg+'_input_pin',pivot_pin(22,0),'steel','metal','crank',leg,prototype='input_pin',note='Nominal 6 x 20 mm shoulder with M5 x 6 thread; alloy-steel grade and fatigue qualification required.')
    add(leg+'_output_pivot_nut',hex_nut(8,4,x,71.8,z,2.5),'steel','metal','knee',leg,prototype='output_pivot_nut',check=False,note='M5 nut seated in the integral inner-shin fork; secure in its pocket during assembly.')
    add(leg+'_output_pin',pivot_pin(x,z),'steel','metal','knee',leg,prototype='output_pin',note='Double-shear shoulder pin; M5 threaded end retained by the captive nut in the structural shin.')
    add(leg+'_knee_axle',ring(6,4.2,45.1,65.4,-170),'steel','metal','thigh',leg,check=True,prototype='knee_axle',note='Removable 12 OD x 8.4 ID x 45.1 mm precision sleeve; M8 through-bolt retains it between the thigh cheeks. Bearing fit and clamp stack require physical verification.')
    axle_bolt=cyl(4,60,(0,65.4,-170)).fuse(cyl(7,4.4,(0,61,-170)))
    add(leg+'_axle_bolt',axle_bolt,'steel','metal','thigh',leg,prototype='axle_bolt',check=True,note='M8 x 60 button-head screw envelope, 14 mm head diameter and 4.4 mm height. Head recessed flush to the inner thigh; flange nut is outboard. Withdraw after removing the nut.')
    axle_nut=hex_nut(13,8,0,110.5,-170,4).fuse(ring(8.95,4,1.6,110.5,-170))
    add(leg+'_axle_nut',axle_nut,'steel','metal','thigh',leg,prototype='axle_nut',check=True,note='M8 flange-nut envelope. Socket access and final preload require verification; no loose external axle spacer.')
    add(leg+'_knee_inner_spacer',ring(7.75,6.05,12,78,-170),'steel','metal','thigh',leg,check=True,prototype='knee_inner_spacer')
    for label,y in [('inner',70),('outer',90)]:
        add(leg+'_bearing_'+label,ring(14,6,8,y),'steel','metal','knee',leg,mass=.022,prototype='bearing_'+label,check=False)
    for outer in [False,True]:
        label='outer' if outer else 'inner'
        add(leg+'_shin_'+label,shin_half(outer),'petg','dark','knee',leg,prototype='shin_'+label,note='One of two fore/aft structural shin halves with integral split bearing seats and pushrod rocker. Opening the X=0 split releases both bearings radially. Two M4 clamps and hard mating lands control closure; bearing fit and printed strength remain unqualified.')
    for zz in [-37,-105]:
        tag=str(abs(zz))
        sleeve=cyl(4,16,(-4,83,zz),(1,0,0)).cut(cyl(2.15,18,(-5,83,zz),(1,0,0)))
        add(leg+'_shin_clamp_sleeve_'+tag,sleeve,'aluminum','metal','knee',leg,prototype='shin_clamp_sleeve_'+tag,check=True,note='Captive 8 OD x 4.3 ID x 16 mm compression sleeve; mating lands establish closure without crushing the bearing seats.')
        bolt=cyl(2,20,(-8,83,zz),(1,0,0)).fuse(cyl(3.5,4,(12,83,zz),(1,0,0)))
        add(leg+'_shin_clamp_bolt_'+tag,bolt,'steel','dark','knee',leg,prototype='shin_clamp_bolt_'+tag,check=True,note='M4 x 20 socket screw; accessible from the front of the shin, with no loose washer.')
        nut=cq.Workplane(cq.Plane(origin=(-7.2,83,zz),xDir=(0,1,0),normal=(1,0,0))).polygon(6,7/(3**.5/2)).extrude(3.2).val().cut(cyl(2,5,(-8,83,zz),(1,0,0)))
        add(leg+'_shin_clamp_nut_'+tag,nut,'steel','metal','knee',leg,prototype='shin_clamp_nut_'+tag,check=True,note='M4 hex nut captured behind the compression sleeve in the rear half; no loose nut needed during routine service.')
    center=cq.Vector(0,83,-P['shank_to_foot_center'])
    sole=cq.Solid.makeSphere(P['foot_radius'],center,angleDegrees1=-90,angleDegrees2=0)
    sole=sole.rotate(center.toTuple(),(0,84,-P['shank_to_foot_center']),30)
    base=cq.Wire.makeCircle(P['foot_radius'],center,cq.Vector(.5,0,math.sqrt(3)/2))
    neck=cq.Wire.makeCircle(9,center+cq.Vector(0,0,20),cq.Vector(0,0,1))
    boot=cq.Solid.makeLoft([base,neck],ruled=True)
    foot=sole.fuse(boot,tol=1e-5).clean()
    add(leg+'_foot',foot,'rubber','rubber','knee',leg,prototype='foot',note='Rounded boot envelope with a shin-aligned neck. Attachment cavity and retaining fastener remain to be detailed.')

def require_legacy_export_authority():
    import runpy
    project = next(parent for parent in Path(__file__).resolve().parents if parent.name == 'tinfox')
    guard = project / 'proposals/sculpted/model/cad_authority.py'
    runpy.run_path(str(guard))['require_generated_authority']()

def export():
    require_legacy_export_authority()
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
        stl_path=OUT/'stl'/f'{name}.stl'
        clean_mesh(trimesh.load_mesh(stl_path)).export(stl_path)
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
    for a,b in [('FL_thigh_inner','FL_knee_motor'),('FL_thigh_inner','FL_motor_mount_ring'),('FL_hip_hub','FL_knee_motor'),('FL_thigh_inner','FL_thigh_outer'),('body_nose_surround','front_fascia'),('FL_motor_carrier','FL_thigh_inner')]:
        sa,sb=solids[a],solids[b]
        overlap=sa.intersect(sb).Volume()
        fit.append({'parts':[a,b],'intersection_mm3':max(0,overlap),'distance_mm':sa.distance(sb)})
    (OUT/'mounting-fit.json').write_text(json.dumps({'model_sha256':hashlib.sha256(raw.encode()).hexdigest(),'pairs':fit,'scope':'Exact nominal solids for selected rigidly attached interfaces. Does not qualify fits, screw engagement, thermal growth or strength.'},indent=2))

    print(f'{len(parts)} parts; {len(meshes)} unique meshes; {len(prototypes)} part prototypes; model {len(raw)/1e6:.1f} MB',flush=True)

if __name__=='__main__':
    require_legacy_export_authority()
    print('Building body',flush=True);build_body()
    for leg in LEGS:print('Building '+leg,flush=True);build_leg(leg)
    export()
