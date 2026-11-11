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
       .spline([(35,-43),(21,-100),(21,-144),(22,-170)],includeCurrent=True)
       .threePointArc((1,-189),(-20,-170))
       .spline([(-24,-135),(-27,-85),(-41,-35),(-49,0)],includeCurrent=True).close())
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
    if outer:s=s.cut(cyl(40.3,5,(0,103.5,0)))
    if not outer:s=s.cut(cyl(20,5,(0,60,0)))
    s=s.cut(box(25,10.2,230,(-17.5,86,-80)))
    return s.cut(cyl(6.1,depth+2,(0,y-1,-170))).clean()

def shin_profile(y,shrink=0):
    wp=cq.Workplane(cq.Plane(origin=(0,y,0),xDir=(1,0,0),normal=(0,-1,0)))
    w=(wp.moveTo(-22,0).threePointArc((0,22),(22,0))
       .spline([(6,-40),(3,-95),(11,-145)],includeCurrent=True)
       .threePointArc((0,-159),(-11,-145))
       .spline([(-20,-95),(-23,-40),(-22,0)],includeCurrent=True).close())
    if shrink:w=w.wires().toPending().offset2D(-shrink)
    return w

@cache
def shin_blank():
    wires=[]
    for z,x,w,d in [(-18,-1,34,32),(-34,-4,31,31),(-60,-8,27,28),(-92,-9,24,26),(-122,-5,23,29),(-148,0,22,31),(-159,0,18,27)]:
        wire=cq.Workplane('XY',origin=(x,83,z)).rect(w,d).val()
        wires.append(wire.fillet2D(5 if z>=-122 else 6.5,wire.Vertices()))
    s=cq.Solid.makeLoft(wires,ruled=False)
    for y in [67,91]:s=s.fuse(ring(22,17.2,8,y))
    return s.clean()

@cache
def shin_half(outer=False):
    if outer:return shin_half(False).mirror('XZ',(0,83,0))
    s=shin_blank()
    # The first part of the shin is an open fork around the crank sweep.
    s=s.cut(box(70,16,100,(0,83,-30)))
    s=s.cut(box(10,17,48,(-5,83,-115),3))
    for x,z in [(-8,-90),(-4,-130)]:
        s=s.fuse(cyl(4.5,32,(x,67,z)).intersect(shin_blank()))
        s=s.cut(cyl(1.7,34,(x,66,z)))
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
        vs,fs=shape.tessellate(.38,.18)
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

def torso(inset=0):
    # A shallow continuous crown, rounded flanks and short tapered end caps.
    stations=[(-232,140,76),(-216,188,90),(-185,206,100),(-140,220,96),(-100,222.4,96),(-72,222.4,96),(0,218,92),(72,222.4,96),(100,222.4,96),(140,220,96),(185,206,100),(216,188,90),(232,140,76)]
    wires=[]
    for x,w,h in stations:
        yy=w/2-inset;top=h/2-inset;bottom=-h/2+inset
        rt=float(np.interp(abs(x),[0,72,100,140,185,232],[21,23,25,26,28,28]))-inset
        rb=28-inset
        wp=cq.Workplane(cq.Plane(origin=(x,0,0),xDir=(0,1,0),normal=(1,0,0)))
        wire=(wp.moveTo(-yy+rt,top-2).threePointArc((0,top+1.5),(yy-rt,top-2))
          .threePointArc((yy-rt+rt*.707,top-rt+rt*.707-2),(yy,top-rt-2))
          .lineTo(yy,bottom+rb)
          .threePointArc((yy-rb+rb*.707,bottom+rb-rb*.707),(yy-rb,bottom))
          .lineTo(-yy+rb,bottom)
          .threePointArc((-yy+rb-rb*.707,bottom+rb-rb*.707),(-yy,bottom+rb))
          .lineTo(-yy,top-rt-2)
          .threePointArc((-yy+rt-rt*.707,top-rt+rt*.707-2),(-yy+rt,top-2)).close().val())
        wires.append(wire)
    return cq.Solid.makeLoft(wires,ruled=False)


def build_body():
    length=P['body_length'];width=P['body_width'];height=P['body_height']
    outer=torso()
    inner=torso(P['body_skin']).intersect(box(P['body_length']-4,300,150))
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
    visor_cut=cq.Workplane('YZ',origin=(229,0,5)).rect(108,30).extrude(6).edges('|X').fillet(9).val()
    shell=shell.cut(visor_cut)
    nominal_shell=shell
    # The corner pockets follow the roll swept volume, including the thigh root.
    samples=[]
    for a in np.deg2rad(np.arange(-61,62)):
        for yy,zz in [(-51,-53),(-51,53),(111,-53),(111,53)]:
            samples.append([yy*np.cos(a)-zz*np.sin(a),yy*np.sin(a)+zz*np.cos(a)])
    pts=np.array(samples);hull=pts[ConvexHull(pts).vertices].tolist()
    blank=cq.Workplane(cq.Plane(origin=(-57,0,0),xDir=(0,1,0),normal=(1,0,0))).polyline(hull).close().extrude(114).val()
    for front in [-1,1]:
        for side in [-1,1]:
            cut=blank if side>0 else blank.mirror('XZ')
            shell=shell.cut(cut.translate((front*P['hip_x'],side*P['roll_y'],0)))
    for front in [-1,1]:
        for side in [-1,1]:
            shell=shell.cut(box(100,50,122,(front*205,side*135,0)))
    # The fixed sensor face narrows toward the motors behind its outer edge.
    face_region=(cq.Workplane('XY').polyline([(230,-52),(232.2,-56.8),(232.2,56.8),(230,52)])
                 .close().extrude(140).val().translate((0,0,-70)))
    for front in [-1,1]:
        region=face_region if front>0 else face_region.mirror('YZ')
        shell=shell.fuse(nominal_shell.intersect(region))
    for front in [-1,1]:
        for side in [-1,1]:
            removed=nominal_shell.cut(shell).intersect(box(116,124,120,(front*P['hip_x'],side*62,0)))
            removed=removed.cut(cyl(45.5,52,(front*P['hip_x'],side*18,0),(0,side,0)))
            removed=removed.cut(cyl(50.5,120,(front*P['hip_x'],side*67,0),(0,side,0)))
            if removed.Volume()>1:
                for label,z,h,col in [('upper',25,70,'shell'),('lower',-35,50,'dark')]:
                    patch=removed.intersect(box(120,150,h,(front*P['hip_x'],side*68,z)))
                    if patch.Volume()>1:add(f'flexible_gaiter_{label}_{front}_{side}',patch,'fabric',col,mass=.018,check=False,note='Neutral flexible gaiter envelope; not a rigid shoulder. Deformation and attachment remain to be developed.')
    for tag,x0,x1 in [('aft',-232,-132),('center',-131.6,131.6),('front',132,232)]:
        for label,z,h in [('body',25,70),('belly',-35,50)]:
            pieces=shell.intersect(box(x1-x0,240,h,((x0+x1)/2,0,z)))
            for i,solid in enumerate(pieces.Solids()):
                add(f'{label}_{tag}_{i}',solid,color='shell' if label=='body' else 'dark',prototype=f'{label}_{tag}_{i}')
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
        beam=box(264,2,54,(0,y,8),.8)
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
    add('lidar_base',cyl(31,4,(-85,0,48),(0,0,1)),'envelope','dark',mass=.04,check=False)
    add('lidar',cyl(27,18,(-85,0,52),(0,0,1)),'envelope','glass',mass=.15,check=False)
    add('lidar_lid',cyl(27,2,(-85,0,70),(0,0,1)),'aluminum','metal',check=False,prototype='lidar_lid')
    visor=cq.Workplane('YZ',origin=(230,0,5)).rect(104,26).extrude(2).edges('|X').fillet(8).val()
    add('sensor_window',visor,'envelope','rubber',mass=.09,check=False)
    for y in [-30,30]:
        add(f'camera_{y}',cyl(9.5,.8,(232,y,5),(1,0,0)),'envelope','dark',mass=.025,check=False)
        add(f'lens_{y}',cyl(6.7,.6,(232.8,y,5),(1,0,0)),'envelope','glass',check=False)
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
    cover=ring(43.5,41.5,44.4,-48.4).fuse(ring(43.5,12,2,-48.4))
    cover=cover.cut(box(20,54,46,(-front*45,-24,0),2))
    add(leg+'_shoulder_cover',cover,'petg','dark','roll',leg,prototype='shoulder_cover_'+str(front),note='Motor cup rotates with the roll output carrier; no rigid shoulder bridges the joint.')
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
    add(leg+'_thigh_outer',shell_half(True),'petg','shell','thigh',leg,prototype='thigh_outer')
    disc=cyl(40,1.1,(0,103.7,0))
    disc=disc.cut(box(.45,.4,45,(0,104.8,0)).rotate((0,0,0),(0,1,0),45))
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
    foot=cq.Solid.makeSphere(P['foot_radius'],cq.Vector(0,83,-P['shank_to_foot_center']),angleDegrees1=-90,angleDegrees2=90)
    foot=foot.fuse(cq.Solid.makeCone(14,9,14,cq.Vector(0,83,-154),cq.Vector(0,0,1)))
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
            if not name.startswith(('body_','belly_','rail_')):
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
