"""Opposed-output pitch module with a structural two-piece thigh carrier.

An architectural review candidate. The knee actuator faces the hip output,
placing the crank inside a shared housing rather than beyond the motor case.
The saved native migration target is unchanged.
"""
import math
from functools import cache
import cadquery as cq
import build as b
import cohesive_limb as cl
import integrated_candidate as ic
import service_design as sd
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections

KNEE_FACE=46.0
FLIP_Y=54.4+KNEE_FACE
CRANK_RADIUS=27.0
CAP_Y=95.4
ROD_Y=FLIP_Y-70
KNEE_CLOCK=113.8

def flip(s):return s.mirror('XZ').translate((0,FLIP_Y,0))

def loft(wires):
    maker=BRepOffsetAPI_ThruSections(True,False);maker.SetMaxDegree(3)
    for wire in wires:maker.AddWire(wire.wrapped)
    maker.Build();shape=cq.Solid(maker.Shape())
    assert shape.isValid() and len(shape.Solids())==1
    return shape

def configure():
    ic.RADIUS=CRANK_RADIUS
    ic.PIN=(CRANK_RADIUS*math.cos(ic.PHASE),-CRANK_RADIUS*math.sin(ic.PHASE))

def contour(z,cx,cy,w,d,r):
    wire=cq.Workplane('XY',origin=(cx,cy,z)).rect(w,d).val()
    return wire.fillet2D(r,wire.Vertices())

SECTIONS=[(-25,0,48,74,88,12),(-50,-8,69,68,44,12),
          (-80,-12,68,56,44,10),(-110,-12,60,56,60,10),
          (-145,-6,43,50,72,10),(-170,0,30.4,46,60,10)]

@cache
def hub():
    # A keyed metal torque plate replaces the broad flange and three tie pads.
    g=cq.Workplane(cq.Plane(origin=(0,5,0),xDir=(1,0,0),normal=(0,1,0))).polygon(6,91).extrude(3)
    flange=g.edges('|Y').fillet(2).val()
    s=b.ring(20,6,5,0).fuse(flange)
    for angle in range(0,360,60):
        a=math.radians(angle);x,z=12*math.cos(a),12*math.sin(a)
        s=s.cut(b.cyl(2.2,12,(x,-1,z))).cut(b.cyl(3.8,5,(x,3.7,z)))
    return s.clean()

@cache
def master():
    configure()
    # The two shells form the motor mount and both longitudinal load paths.
    drum=loft([cq.Wire.makeCircle(r,cq.Vector(0,y,0),cq.Vector(0,1,0)) for y,r in [(2,48),(12,48),(25,45.5),(50,44.5),(80,44.5),(CAP_Y,43.5)]])
    stem=loft([contour(*row) for row in SECTIONS])
    assert stem.isValid(), 'Invalid outer stem loft'
    outer=drum.fuse(stem).clean()
    # The root stays inside the coaxial drum's orbit beside the stationary
    # roll journal; the long neck lies outboard of the chassis rails.
    outside=b.box(200,100,150,(0,-7,-10)).cut(b.cyl(48,110,(0,-57,0)))
    outer=outer.cut(outside)
    assert outer.isValid() and len(outer.Solids())==1,'Invalid shoulder relief'
    inside_rows=[(z,cx,cy,w-8,d-8,max(3,r-4)) for z,cx,cy,w,d,r in SECTIONS]
    inside_rows[0]=(-29,*inside_rows[0][1:])
    inside_rows[-1]=(-166,*inside_rows[-1][1:])
    cavity=loft([contour(*row) for row in inside_rows])
    s=outer.cut(cavity)
    s=s.cut(b.cyl(40.5,83.4,(0,8,0)))
    # Rear opening and positive keyed pocket retain the metal hip interface.
    s=s.cut(b.cyl(25.5,5,(0,1,0)))
    pocket=cq.Workplane(cq.Plane(origin=(0,4.8,0),xDir=(1,0,0),normal=(0,1,0))).polygon(6,91.4).extrude(3.5)
    pocket=pocket.edges('|Y').fillet(2.1).val()
    s=s.cut(pocket)
    # Local annular lips hold the keyed interface; they are part of the shell.
    for y,depth,ri in [(2,2.8,25.5),(8.3,3.2,39.5)]:
        s=s.fuse(b.ring(48,ri,depth,y).intersect(outer))
    # Motor stator support is an integral bulkhead, not a separate ring/tie cage.
    bulk=b.ring(46.5,23.5,6,43.9)
    s=s.fuse(bulk.intersect(outer))
    s=s.cut(b.cyl(34,2.5,(0,43.9,0)))
    for angle in range(20,380,40):
        a=math.radians(angle-KNEE_CLOCK);x,z=36.5*math.cos(a),36.5*math.sin(a)
        s=s.cut(b.cyl(1.7,12,(x,41,z))).cut(b.cyl(3.0,3.1,(x,43.8,z)))
    # Preserve the original knee clearances, bearing backups and axle hardware.
    # Two broad inboard rails connect the shifted bearing cheek to the neck;
    # their fan-shaped roots arrive above the shin's folding cavity.
    rib_profile=[(4,-170),(9.4,-170),(9.4,-110),(94,-97),(94,-88),(4,-104)]
    for x in [12]:
        plane=cq.Plane(origin=(x,0,0),xDir=(0,1,0),normal=(1,0,0))
        rib=cq.Workplane(plane).polyline(rib_profile).close().extrude(8).val()
        s=s.fuse(rib)
    rear_profile=[(4,-118),(9.4,-118),(9.4,-110),(94,-97),(94,-88),(4,-104)]
    plane=cq.Plane(origin=(-44,0,0),xDir=(0,1,0),normal=(1,0,0))
    s=s.fuse(cq.Workplane(plane).polyline(rear_profile).close().extrude(7.5).val())
    plane=cq.Plane(origin=(0,4,0),xDir=(1,0,0),normal=(0,-1,0))
    rail=[(-44,-104),(-36.5,-104),(-12,-150),(-12,-177),(-20,-177),(-20,-150),(-44,-118)]
    wire=cq.Workplane(plane).polyline(rail).close().val()
    wire=wire.fillet2D(1.5,wire.Vertices())
    s=s.fuse(cq.Solid.extrudeLinear(wire,[],cq.Vector(0,5.4,0)))
    knee_space=cq.Workplane(obj=b.cyl(53,40.5,(0,50.5,-170))).edges().fillet(3).val()
    s=s.cut(flip(knee_space))
    for is_outer in [False,True]:
        old=cl.thigh(is_outer)
        stop=old.intersect(b.cyl(16,140,(0,0,-170)))
        s=s.fuse(flip(stop))
    s=s.cut(flip(b.cyl(6.1,140,(0,0,-170))))
    s=s.cut(flip(b.cyl(9.2,12,(0,94.3,-170))))
    s=s.cut(flip(b.cyl(7.2,12,(0,37.4,-170))))
    # The rod passes through the inboard cavity at the same crank phase.
    points=[]
    for knee in range(-156,-47,2):
        a=math.radians(knee-78)
        for dz in [0,-170]:
            x,z=CRANK_RADIUS*math.cos(a),-CRANK_RADIUS*math.sin(a)+dz
            for u in range(0,360,30):points.append((x+9*math.cos(math.radians(u)),z+9*math.sin(math.radians(u))))
    import numpy as np
    from scipy.spatial import ConvexHull
    points=np.array(points);outline=points[ConvexHull(points).vertices].tolist()
    plane=cq.Plane(origin=(0,ROD_Y-4.5,0),xDir=(1,0,0),normal=(0,-1,0))
    s=s.cut(cq.Workplane(plane).polyline(outline).close().extrude(-9).val())
    foot=cl.folded_foot_space().mirror('XZ').translate((0,FLIP_Y,0))
    s=s.cut(foot)
    for sign in [-1,1]:
        # Existing connector envelope, reoriented with the opposed actuator.
        s=s.cut(flip(sd.connector_parts(54.4,sign)[3]).rotate((0,0,0),(0,1,0),KNEE_CLOCK)).cut(flip(sd.cable_space(54.4,sign)).rotate((0,0,0),(0,1,0),KNEE_CLOCK))
    # Four transverse through-bolts join broad lands, all accessible externally.
    for y,z in [(18,43),(77,43),(7,-91),(54,-91)]:
        land=b.cyl(7,100,(-50,y,z),(1,0,0)).intersect(outer)
        land=land.cut(b.cyl(40.5,83.4,(0,8,0))) if z>0 else land
        s=s.fuse(land).cut(b.cyl(2.2,100,(-50,y,z),(1,0,0)))
        s=s.cut(b.cyl(4.1,35,(11,y,z),(1,0,0)))
        # Ordinary M4 nuts seat in pockets open to the rear half's exterior.
        nut=b.hex_nut(7.2,35,0,0,0,.01).rotate((0,0,0),(0,0,1),90).translate((-14,y,z))
        s=s.cut(nut)
    s=s.clean()
    if not s.isValid() or len(s.Solids())!=1:
        print('Integrated carrier regions',[(round(a.Volume(),3),tuple(round(v,2) for v in a.Center().toTuple())) for a in s.Solids()],flush=True)
    assert s.isValid() and len(s.Solids())==1,('opposed master',s.isValid(),len(s.Solids()))
    return s

@cache
def halves():
    whole=master()
    a=whole.intersect(b.box(120,260,360,(-60,30,-85)))
    c=whole.intersect(b.box(120,260,360,(60,30,-85)))
    for name,s in [('rear',a),('front',c)]:
        if len(s.Solids())!=1:
            print('Split regions',name,[(round(p.Volume(),2),tuple(round(v,1) for v in p.Center().toTuple())) for p in s.Solids()],flush=True)
            print('Split gap',s.Solids()[0].distance(s.Solids()[1]),flush=True)
            for i,piece in enumerate(s.Solids()):cq.exporters.export(piece,'/tmp/integrated-'+name+'-'+str(i)+'.step')
        assert s.isValid() and len(s.Solids())==1,(name,s.isValid(),len(s.Solids()))
    return a,c

def crank():
    configure()
    s=ic.input_crank()
    # Trim the near fork's redundant axial material to clear stator screw heads.
    trim=b.cyl(10.5,2.6,(CRANK_RADIUS,55.8,0))
    s=s.cut(trim).clean()
    assert s.isValid() and len(s.Solids())==1
    return flip(s)

def shin(outer):
    configure()
    return flip(cl.shin(outer))
