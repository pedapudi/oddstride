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
       .spline([(35,-43),(25,-72),(18,-112),(19,-150),(20,-170)],includeCurrent=True)
       .threePointArc((0,-189),(-20,-170))
       .spline([(-19,-145),(-20,-110),(-28,-72),(-41,-35),(-49,0)],includeCurrent=True).close())
    if shrink:w=w.wires().toPending().offset2D(-shrink)
    return w

POD_TIE_ANGLES=[90,210,330]
POD_TIE_RADIUS=43.5

SHELL_BOLTS=[(-34,-43),(26,-48)]

def cheek_roof(z):
    # Smooth depth reduction through the thigh web, retaining full joint seats.
    return min(105.0,105.5-3*math.exp(-((z+98)/37)**4))

@cache
def cheek_envelope(offset=0):
    # Extend past the flat joint seats to avoid coincident trimming surfaces.
    pts=[(float(z),105.5-3*math.exp(-((z+98)/37)**4)-offset) for z in np.linspace(-210,60,55)]
    wp=cq.Workplane(cq.Plane(origin=(-80,0,0),xDir=(0,0,1),normal=(-1,0,0)))
    return (wp.moveTo(-210,0).lineTo(*pts[0]).spline(pts[1:],includeCurrent=True)
            .lineTo(60,0).close().extrude(-160).val())

@cache
def shell_half(outer=False):
    y=83 if outer else 61;depth=22;skin=P['shell_skin']
    envelope=profile(y).extrude(-depth).val()
    if outer:
        s=cq.Workplane(obj=envelope).faces('>Y').edges().fillet(4).val()
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
    if outer:s=s.cut(cyl(40.3,5,(0,103.5,0))).cut(ring(42,40.1,3,104.5))
    if not outer:s=s.cut(cyl(20,5,(0,60,0)))
    s=s.cut(box(25,10.2,230,(-17.5,86,-80)))
    return s.cut(cyl(6.1,depth+2,(0,y-1,-170))).clean()

# One shallow sagittal arc gives a compact tapered beam without a lower kink.
# Knee and foot centers are fixed. The final hidden station seats in the boot.
def shin_centerline(z):
    t=min(1,max(0,-z/P['shank_to_foot_center']))
    return 4*3.5*t*(1-t)

SHIN_STATIONS=[(z,shin_centerline(z),w,d) for z,w,d in
               [(-18,34,32),(-34,31,29),(-60,27,27),(-88,24,27.5),
                (-112,22,28),(-133,21,27),(-147,20,25),(-159,18,23)]]

def shin_station(z):
    # Interpolation is used for holes and cavity stations, while the exterior
    # loft provides a smooth surface through the same reference sections.
    a=list(reversed(SHIN_STATIONS))
    return tuple(float(np.interp(z,[p[0] for p in a],[p[i] for p in a])) for i in [1,2,3])

@cache
def shin_blank():
    wires=[]
    for z,x,w,d in SHIN_STATIONS:
        wire=cq.Workplane('XY',origin=(x,83,z)).rect(w,d).val()
        wires.append(wire.fillet2D(5,wire.Vertices()))
    s=cq.Solid.makeLoft(wires,ruled=False)
    for y in [67,91]:s=s.fuse(ring(22,17.2,8,y))
    return s.clean()

@cache
def shin_half(outer=False):
    if outer:return shin_half(False).mirror('XZ',(0,83,0))
    s=shin_blank()
    # The root remains an open fork around the unchanged crank sweep.
    s=s.cut(box(90,16,100,(8,83,-30)))
    cavity=[]
    for z in [-79,-90,-110,-130,-141]:
        x,_,_=shin_station(z)
        wire=cq.Workplane('XY',origin=(x,83,z)).rect(10,17).val()
        cavity.append(wire.fillet2D(3,wire.Vertices()))
    s=s.cut(cq.Solid.makeLoft(cavity,ruled=False))
    for z in [-91,-132]:
        x,_,_=shin_station(z)
        s=s.fuse(cyl(4.5,32,(x,67,z)).intersect(shin_blank()))
        s=s.cut(cyl(1.7,34,(x,66,z)))
    s=s.cut(cyl(17.2,36,(0,65,0)))
    channel=[]
    for z,w in [(-76,.8),(-81,5.5),(-95,5.5),(-112,5.5),(-129,5.5),(-140,5.5),(-145,.8)]:
        x,_,d=shin_station(z)
        channel.append(cq.Workplane('XY',origin=(x,83-d/2-.45,z)).rect(w,2.3).val())
    s=s.cut(cq.Solid.makeLoft(channel,ruled=False))
    s=s.intersect(box(130,30,220,(8,98 if outer else 68,-85)))
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
        vs,fs=shape.tessellate(.05,.08) if name.startswith(('lens_','camera_')) else shape.tessellate(.38,.18)
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

@cache
def torso(inset=0):
    # Controlled planar center bay, locally smooth crowns and a broader nose.
    # Rounded cross-sections preserve a shallow roof bevel without hard corners.
    center=[(-135,212,100,9),(-75,212,100,9),(0,208,96,9),(75,212,100,9),(135,212,100,9)]
    rear=[(-236,134,78,12),(-225,166,92,11),(-205,194,103,10),(-180,207,106,10),(-155,212,103,9),(135*-1,212,100,9)]
    front=[(135,212,100,9),(155,212,103,9),(180,207,106,10),(205,194,103,11),(225,190,99,13),(243,178,92,14)]
    def wire(station):
        x,w,h,r=station
        if x==243:x-=inset
        if x==-236:x+=inset
        yy=w/2;top=h/2;bottom=-h/2;bevel=14;lower=10.8 if station[0]==243 else 18
        lower_height=10.8 if station[0]==243 else 16
        wp=cq.Workplane(cq.Plane(origin=(x,0,0),xDir=(0,1,0),normal=(1,0,0)))
        profile=(wp.polyline([(-yy+bevel,top),(yy-bevel,top),(yy,top-12),(yy,bottom+lower_height),(yy-lower,bottom),(-yy+lower,bottom),(-yy,bottom+lower_height),(-yy,top-12)]).close().val())
        if station[0]==243:
            profile=profile.fillet2D(18,[v for v in profile.Vertices() if v.Z<0])
            profile=profile.fillet2D(r,[v for v in profile.Vertices() if v.Z>0])
        else:profile=profile.fillet2D(r,profile.Vertices())
        if inset:
            extra=P['nose_corner_extra_skin_mm']*max(0,(station[0]-205)/38) if inset>0 else 0
            profile=profile.offset2D(-inset-extra)[0]
        return profile
    middle=cq.Solid.makeLoft([wire(v) for v in center],ruled=True)
    aft=cq.Solid.makeLoft([wire(v) for v in rear],ruled=False)
    nose=cq.Solid.makeLoft([wire(v) for v in front],ruled=False)
    shape=middle.fuse(aft,nose).clean()
    shape=cq.Workplane(obj=shape).faces('>X').edges().fillet(4.5-inset).val()
    return cq.Workplane(obj=shape).faces('<X').edges().fillet(4.5-inset).val()


def build_body():
    length=P['body_length'];width=P['body_width'];height=P['body_height']
    outer=torso()
    inner=torso(P['body_skin']).intersect(box(P['body_length']-2*P['body_skin'],300,150,(3.5,0,0)))
    shell=outer.cut(inner)
    window_mask=cq.Workplane(obj=box(48,28,20,(20,0,48))).edges('|Z').fillet(4).val()
    status_window=outer.cut(torso(.6)).intersect(window_mask)
    shell=shell.cut(status_window)
    for x in [-55,55]:shell=shell.fuse(box(2.4,176,12,(x,0,46)).intersect(outer))
    # Local inside reliefs preserve clearance to the fixed roll-motor cartridges.
    for front in [-1,1]:
        for side in [-1,1]:
            shell=shell.cut(cyl(41.25,49.4,(front*70.3,side*P['roll_y'],0),(front,0,0)))
            shell=shell.cut(cyl(42,7,(front*111.7,side*P['roll_y'],0),(front,0,0)))
            shell=shell.cut(cyl(38,20,(front*113.5,side*P['roll_y'],0),(front,0,0)))
            for z in [-12,24]:shell=shell.cut(box(14,16,14,(front*125.5,side*89.5,z)))
    for y in [-97,97]:shell=shell.cut(box(268,3,55,(0,y,8),.8))
    shell=shell.cut(box(148,198,70,(0,0,-55),8))
    visor_cut=cq.Workplane('YZ',origin=(237,0,3)).rect(150,42).extrude(8).edges('|X').fillet(10).val()
    shell=shell.cut(visor_cut)
    nominal_shell=shell
    # The corner pockets follow the roll swept volume, including the thigh root.
    samples=[]
    for a in np.deg2rad(np.arange(-61,62)):
        for yy,zz in [(-51,-53),(-51,53),(111,-53),(111,53)]:
            samples.append([yy*np.cos(a)-zz*np.sin(a),yy*np.sin(a)+zz*np.cos(a)])
    pts=np.array(samples);hull=pts[ConvexHull(pts).vertices].tolist()
    blank=cq.Workplane(cq.Plane(origin=(-65,0,0),xDir=(0,1,0),normal=(1,0,0))).polyline(hull).close().extrude(130).val()
    for front in [-1,1]:
        for side in [-1,1]:
            cut=blank if side>0 else blank.mirror('XZ')
            shell=shell.cut(cut.translate((front*P['hip_x'],side*P['roll_y'],0)))
    for front in [-1,1]:
        for side in [-1,1]:
            shell=shell.cut(box(100,50,122,(front*205,side*125,0)))
    # The fixed sensor face narrows toward the motors behind its outer edge.
    face_region=(cq.Workplane('XY').polyline([(230,-47),(239.7,-54),(241.6,-90),(243.2,-90),(243.2,90),(241.6,90),(239.7,54),(230,47)])
                 .close().extrude(140).val().translate((0,0,-70)))
    upper_return=(cq.Workplane('XY').polyline([(230,-47),(238,-54),(240.7,-90),(243.2,-90),(243.2,90),(240.7,90),(238,54),(230,47)])
                  .close().extrude(140).val().translate((0,0,-70)))
    face_region=face_region.fuse(upper_return.intersect(box(400,300,160,(150,0,45))))
    for front in [-1,1]:
        region=face_region if front>0 else (cq.Workplane('XY').polyline([(230,-47),(234.6,-54),(234.6,-80),(236.2,-80),(236.2,80),(234.6,80),(234.6,54),(230,47)]).close().extrude(140).val().translate((0,0,-70))).mirror('YZ')
        shell=shell.fuse(nominal_shell.intersect(region))
    nose_aperture=cq.Workplane('YZ',origin=(240.9,0,0)).rect(157.2,77.2).extrude(5).edges('|X').fillet(16.6).val()
    shell=shell.cut(nose_aperture)
    nominal_shell=nominal_shell.cut(nose_aperture)
    for yy in [-81.5,81.5]:
        for zz in [-25,25]:
            bore=cyl(1.7,5,(240.5,yy,zz),(1,0,0))
            recess=cyl(2.6,1.4,(242.2,yy,zz),(1,0,0))
            shell=shell.cut(bore).cut(recess);nominal_shell=nominal_shell.cut(bore).cut(recess)
    for front in [-1,1]:
        for side in [-1,1]:
            removed=nominal_shell.cut(shell).intersect(box(132,124,120,(front*P['hip_x'],side*57,0)))
            removed=removed.cut(cyl(45.5,52,(front*P['hip_x'],side*13,0),(0,side,0)))
            removed=removed.cut(cyl(50.5,120,(front*P['hip_x'],side*62,0),(0,side,0)))
            if removed.Volume()>1:
                for label,z,h,col in [('upper',25,70,'shell'),('lower',-35,50,'dark')]:
                    patch=removed.intersect(box(132,150,h,(front*P['hip_x'],side*63,z)))
                    patch=patch.intersect(box(122.8 if front>0 else 115.8,300,160,(181.6 if front>0 else -178.1,0,0)))
                    if patch.Volume()>1:add(f'flexible_gaiter_{label}_{front}_{side}',patch,'fabric',col,mass=.018,check=False,note='Neutral flexible gaiter envelope; not a rigid shoulder. Deformation and attachment remain to be developed.')
    # Ivory wrap follows the nose's lower corners; only a thin underside lip
    # remains dark. The split is real part geometry, not a material overlay.
    wrap=(cq.Workplane(cq.Plane(origin=(0,-130,0),xDir=(1,0,0),normal=(0,-1,0)))
          .moveTo(216,-10).spline([(223,-12),(230,-31),(236,-40)],includeCurrent=True)
          .lineTo(245,-40).lineTo(245,0).lineTo(216,0).close().extrude(-260).val())
    for tag,x0,x1 in [('aft',-236,-120.2),('center',-119.8,119.8),('front',120.2,243)]:
        for label,z,h in [('body',25,70),('belly',-35,50)]:
            pieces=shell.intersect(box(x1-x0,240,h,((x0+x1)/2,0,z)))
            if tag=='front':
                added=shell.intersect(wrap)
                pieces=pieces.fuse(added) if label=='body' else pieces.cut(wrap)
            for i,solid in enumerate(pieces.Solids()):
                add(f'{label}_{tag}_{i}',solid,color='shell' if label=='body' else 'dark',prototype=f'{label}_{tag}_{i}')
    for side in [-1,1]:
        for x,z in [(-114,27),(114,27),(-114,-5),(114,-5)]:
            head=cyl(3.4,1.2,(x,side*105,z),(0,side,0)).cut(cyl(1.5,2,(x,side*105.1,z),(0,side,0)))
            add(f'panel_fastener_{side}_{x}_{z}',head,'steel','metal',check=False,note='Visible panel screw envelope; bosses and final screw selection require detail design.')
        lettering=cq.Workplane(cq.Plane(origin=(-40,side*100,7),xDir=(-side,0,0),normal=(0,side,0))).text('tinfox   01',9,9,combine=True).val()
        mark=torso(-.12).cut(outer).intersect(lettering)
        if mark.Volume()>0:add(f'body_mark_{side}',mark,'aluminum','plate',check=False,note='0.12 mm finish marking follows the body surface.')
        add(f'body_index_{side}',cyl(2.7,.6,(45,side*104.7,9),(0,side,0)),'aluminum','orange',check=False)
    # Two removable packs sit alongside one another between the four motor stations.
    for side in [-1,1]:
        y=side*44.5
        add(f'battery_{side}',box(*P['battery_envelope_mm'],(0,y,P['battery_center_z']),7),'envelope','dark',mass=P['battery_each_mass_kg_assumed'],note='Pack plus adapter envelope; exact commercial pack remains unselected.')
        add(f'battery_latch_{side}',box(18,1.4,7,(0,side*97.2,-37),.6),'petg','orange',check=False,prototype=f'battery_latch_{side}')
    for y in [-90.5,90.5]:
        rail=box(134,5,61,(0,y,-36),2).cut(cq.Workplane(obj=box(112,7,45,(0,y,-34))).edges('|Y').fillet(7).val())
        add(f'battery_rail_{y}',rail,color='dark',prototype=f'battery_rail_{y}')
    cassette=box(140,194,69.5,(0,0,-34.75),12).cut(box(136,190,70,(0,0,-32.5),10))
    add('battery_cassette',cassette,color='dark',prototype='battery_cassette',note='Rounded structural underside enclosure; pack adapters and contacts remain unselected.')
    skid_wire=cq.Workplane('XY',origin=(0,0,-71)).rect(138,190).val()
    skid_wire=skid_wire.fillet2D(15,skid_wire.Vertices())
    add('battery_skid',cq.Solid.extrudeLinear(skid_wire,[],cq.Vector(0,0,1.5)),'aluminum','plate',prototype='battery_skid')
    # Aluminum longitudinal members join the four roll cartridges to the torso.
    for y in [-97,97]:
        beam=box(264,2,54,(0,y,8),.8).cut(box(150,6,40,(0,y,-22)))
        for x in [-91,91]:
            beam=beam.cut(cq.Workplane(obj=box(56,6,52,(x,y,0))).edges('|Y').fillet(4).val())
        beam=beam.cut(cq.Workplane(obj=box(80,6,32,(0,y,8))).edges('|Y').fillet(8).val())
        for xx in [-125.5,125.5]:
            for zz in [-12,24]:beam=beam.cut(cyl(2.2,6,(xx,y-3,zz)))
        add(f'chassis_beam_{y}',beam,'aluminum','plate',prototype=f'chassis_beam_{y}')
    for side in [-1,1]:
        for xx in [-125.5,125.5]:
            for zz in [-12,24]:
                bolt=cyl(2,12,(xx,side*98,zz),(0,-side,0)).fuse(cyl(3.5,2.5,(xx,side*98,zz),(0,side,0)))
                add(f'chassis_bolt_{side}_{xx}_{zz}',bolt,'steel','dark',check=False)
    add('electronics_shelf',box(134,188,1.5,(0,0,3),.5).cut(cq.Workplane(obj=box(96,155,4,(0,0,3))).edges('|Z').fillet(12).val()),'aluminum','plate',prototype='electronics_shelf')
    add('electronics_clearance',box(*P['electronics_clearance_mm'],(0,0,22),2),'envelope','dark',check=True,note='Reserved 130 x 135 x 32 mm computer volume; mass is in the electronics allowance. Exact computer and heat sink are unselected.')
    add('lidar_base',cyl(31,4,(95,0,49.5),(0,0,1)),'envelope','dark',mass=.04,check=False)
    add('lidar',cyl(27,18,(95,0,53.5),(0,0,1)),'envelope','glass',mass=.15,check=False)
    add('lidar_lid',cyl(27,2,(95,0,71.5),(0,0,1)),'aluminum','metal',check=False,prototype='lidar_lid')
    visor=cq.Workplane('YZ',origin=(238.4,0,3)).rect(146,38).extrude(1.4).edges('|X').fillet(9).val()
    bezel=(cq.Workplane('YZ',origin=(239.6,0,3)).rect(150,42).extrude(2.2).edges('|X').fillet(10).val()
           .cut(cq.Workplane('YZ',origin=(238.8,0,3)).rect(146,38).extrude(5).edges('|X').fillet(9).val()))
    nose=(cq.Workplane('YZ',origin=(241.4,0,0)).rect(156,76).extrude(1.6).edges('|X').fillet(16).val()
          .cut(cq.Workplane('YZ',origin=(240,0,3)).rect(148,40).extrude(6).edges('|X').fillet(9.5).val()))
    for yy in [-68,68]:
        for zz in [-30,30]:
            nose=nose.cut(cyl(1.7,4,(241,yy,zz),(1,0,0))).cut(cyl(3.1,1.1,(242.45,yy,zz),(1,0,0)))
            end_y=81.5 if yy>0 else -81.5;end_z=25 if zz>0 else -25
            angle=math.degrees(math.atan2(end_z-zz,end_y-yy))
            tab=(cq.Workplane('YZ',origin=(238.8,(yy+end_y)/2,(zz+end_z)/2))
                 .slot2D(math.hypot(end_y-yy,end_z-zz)+5,5,angle).extrude(2.6).val())
            post=cyl(2.7,2.6,(238.8,yy,zz),(1,0,0)).fuse(tab)
            for y_h,z_h in [(yy,zz),(end_y,end_z)]:post=post.cut(cyl(1.5,4,(238,y_h,z_h),(1,0,0)))
            head=cyl(2.5,.65,(242.25,end_y,end_z),(1,0,0)).cut(cyl(1.1,1,(242.3,end_y,end_z),(1,0,0)))
            add(f'nose_rim_fastener_{yy}_{zz}',head,'steel','dark',check=False)
            add(f'nose_standoff_{yy}_{zz}',post,'aluminum','metal',prototype=f'nose_standoff_{yy}_{zz}',note='Two-hole support tab joins the inset service face to the rear face of the rounded nose rim; final screws and nuts remain to be selected.')
            screw=cyl(3,.5,(242.5,yy,zz),(1,0,0)).cut(cyl(1.2,1.5,(242.6,yy,zz),(1,0,0)))
            add(f'nose_fastener_{yy}_{zz}',screw,'steel','dark',check=False)
    add('nose_panel',nose,'petg','shell',prototype='nose_panel',note='1.6 mm removable cosmetic face sits flush inside the rounded body rim; counterbores clear the provisional low-head screw envelopes. Final optics and screws remain unselected.')
    add('sensor_bezel',bezel,'aluminum','plate',check=False,prototype='sensor_bezel')
    add('sensor_window',visor,'envelope','glass',mass=.09,check=False)
    for y in [-50,50]:
        add(f'camera_{y}',cyl(9.5,2.2,(239.6,y,3),(1,0,0)).cut(cyl(7,4,(238.8,y,3),(1,0,0))),'envelope','dark',mass=.025,check=False)
        add(f'camera_aperture_{y}',cyl(6.8,.7,(240,y,3),(1,0,0)).cut(cyl(4.7,1.5,(239.8,y,3),(1,0,0))),'envelope','dark',check=False,note='Provisional concentric aperture envelope; no selected camera module.')
        glass=cq.Solid.makeSphere(45,cq.Vector(195.9,y,3),angleDegrees1=-90,angleDegrees2=90).intersect(cyl(6.6,1,(240.3,y,3),(1,0,0)))
        add(f'lens_{y}',glass,'envelope','glass',check=False,note='Shallow curved optical envelope inside the recessed aperture; final lens geometry is unselected.')
    add('status_display',status_window,'envelope','glass',mass=.03,check=False)
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
    cover=ring(41.5,40,41.9,-45.9)
    cover=cover.cut(box(20,54,46,(-front*45,-24,0),2))
    add(leg+'_shoulder_cover',cover,'petg','dark','roll',leg,prototype='shoulder_cover_'+str(front),note='Open-back protective sleeve rotates with the roll carrier. Its 1.5 mm wall and short rear overhang preserve opposite-shoulder clearance; it carries no joint load.')
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
        boss=ring(5.2,2.7,15,49,z,x)
        integrated=integrated.fuse(boss,tol=1e-5)
    integrated=integrated.cut(ring(48.3,24,3.4,54.3))
    for a in POD_TIE_ANGLES:
        x,z=POD_TIE_RADIUS*math.cos(math.radians(a)),POD_TIE_RADIUS*math.sin(math.radians(a))
        integrated=integrated.cut(cyl(2.7,53,(x,12,z)))
    integrated=integrated.cut(box(25,10.2,230,(-17.5,74,-80)))
    integrated=integrated.cut(cyl(40.25,43,(0,12,0))).clean()
    bb=integrated.BoundingBox()
    if not integrated.isValid() or len(integrated.Solids())!=1 or bb.ymin>13.1 or bb.zmin>-188:raise RuntimeError('Integrated motor cradle lost its motor seat or limb')
    if integrated.intersect(motor_envelope((0,58.4,0))).Volume()>1e-4:raise RuntimeError('Motor cradle overlaps actuator')
    add(leg+'_thigh_inner',integrated,'petg','dark','thigh',leg,prototype='thigh_inner',note='One structural motor cradle and thigh cheek. Knee actuator is recessed 12 mm into the limb root; metal flange and compression sleeves spread mounting loads.')
    cheek=shell_half(True)
    add(leg+'_thigh_outer',cheek,'petg','shell','thigh',leg,prototype='thigh_outer')
    disc=cyl(40,1.1,(0,103.7,0))
    disc=disc.cut(box(.65,.7,53,(0,104.7,0)).rotate((0,0,0),(0,1,0),15))
    digits=cq.Workplane('XY').text('170',6,.5,combine=True).val().rotate((0,0,0),(1,0,0),90).translate((0,104.9,-27))
    disc=disc.cut(digits)
    add(leg+'_cap_bezel',ring(42,40.15,.4,104.6),'rubber','dark','thigh',leg,prototype='cap_bezel',note='Thin seated finish gasket around the removable cap.')
    slash=box(.65,.15,53,(0,104.475,0)).rotate((0,0,0),(0,1,0),15)
    add(leg+'_cap_mark',slash,'aluminum','dark','thigh',leg,check=False,note='Recessed finish in the engraved cap index.')
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
    add(leg+'_knee_bezel',ring(17.6,11.2,1.2,105,-170),'petg','dark','thigh',leg,check=False,prototype='knee_bezel')
    add(leg+'_knee_end_cap',ring(11,3.2,1.5,105,-170),'aluminum','metal','thigh',leg,check=False,prototype='knee_end_cap')
    foot=cq.Solid.makeSphere(P['foot_radius'],cq.Vector(0,83,-P['shank_to_foot_center']),angleDegrees1=-90,angleDegrees2=0)
    foot=foot.fuse(cq.Solid.makeCone(16,9,14,cq.Vector(0,83,-P['shank_to_foot_center']),cq.Vector(0,0,1)))
    add(leg+'_foot',foot,'rubber','rubber','knee',leg,prototype='foot')

def require_legacy_export_authority():
    import runpy
    project = next(parent for parent in Path(__file__).resolve().parents if parent.name == 'tinfox')
    guard = project / 'proposals/sculpted/model/cad_authority.py'
    runpy.run_path(str(guard))['require_generated_authority']()

def export():
    require_legacy_export_authority()
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
    (OUT/'print-stl').mkdir(exist_ok=True)
    (OUT/'step-parts').mkdir(exist_ok=True)
    printable={name for name in prototypes if next(p for p in parts if p['mesh']==name)['material']=='petg'}
    for folder,extension,expected in [('stl','stl',set(prototypes)),('step-parts','step',set(prototypes)),('print-stl','stl',printable)]:
        for old in (OUT/folder).glob('*.'+extension):
            if old.stem not in expected:old.unlink()
    print_manifest=[]
    for name,s in prototypes.items():
        cq.exporters.export(s,str(OUT/'stl'/f'{name}.stl'),tolerance=.15,angularTolerance=.15)
        cq.exporters.export(s,str(OUT/'step-parts'/f'{name}.step'))
        prototype_part=next(p for p in parts if p['mesh']==name)
        if prototype_part['material']=='petg':
            oriented=s
            if name=='nose_panel':
                oriented=s.rotate((0,0,0),(0,1,0),90)
            elif name in ['power_button','battery_cassette']:
                pass
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
    # Separate-part STEP geometry also preserves machining candidates for Fusion.
    cq.exporters.export(cq.Compound.makeCompound(list(prototypes.values())),str(OUT/'leg-and-panel-parts.step'))
    data={'parameters':P,'parts':parts,'meshes':meshes,'poses':POSES,'units':'mm','status':'engineering prototype; not load-qualified'}
    raw=json.dumps(data,separators=(',',':'))
    (OUT/'model.json').write_text(raw)
    (ROOT/'review'/'model.json').write_text(raw)
    (OUT/'manifest.json').write_text(json.dumps({'parameters':P,'parts':parts,'model_sha256':hashlib.sha256(raw.encode()).hexdigest()},indent=2))
    (OUT/'print-manifest.json').write_text(json.dumps(print_manifest,indent=2))
    fit=[]
    for a,b in [('FL_thigh_inner','FL_knee_motor'),('FL_thigh_inner','FL_motor_mount_ring'),('FL_hip_hub','FL_knee_motor'),('FL_thigh_inner','FL_thigh_outer'),('FL_thigh_outer','FL_hip_disc')]:
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
