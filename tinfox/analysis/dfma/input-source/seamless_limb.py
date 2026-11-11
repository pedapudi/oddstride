"""Rounded structural limb retaining the established actuator/linkage planes.

One master per limb segment supplies both manufactured halves. Complete bearing
seats and service features remain independent of the sculpted exterior.
"""
import math
from functools import cache
import cadquery as cq
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
import build as b
import cohesive_limb as cl
import compact_motor_thigh as compact
import integrated_candidate as ic
import service_design as sd

CAP_Y=94.0
FACE_RADIUS=500.0
WALL=4.0

def smooth_loft(wires):
    builder=BRepOffsetAPI_ThruSections(True,False);builder.SetMaxDegree(3)
    for wire in wires:builder.AddWire(wire.wrapped)
    builder.Build();s=cq.Solid(builder.Shape())
    assert s.isValid() and len(s.Solids())==1
    return s

def cap_mask(radius):return b.cyl(radius,400,(0,CAP_Y-FACE_RADIUS,-250),(0,0,1))

def build_thigh_master(root=None):
    blank=cl.thigh_outline(9).extrude(-(CAP_Y-9)).val()
    blank=cq.Workplane(obj=blank).faces('>Y').edges().fillet(8).val()
    underside=b.box(220,94,300,(0,0,-90))
    if root is None:
        root=smooth_loft([cq.Wire.makeCircle(r,cq.Vector(0,y,0),cq.Vector(0,1,0)) for y,r in compact.ROOT_STATIONS])
    blank=blank.cut(underside.cut(root)).intersect(cap_mask(FACE_RADIUS)).clean()
    blank=cq.Workplane(obj=blank).faces('<Y').edges().fillet(1.2).val()
    wire=cl.thigh_outline(13).wires().val().offset2D(-WALL)[0].toNURBS()
    cavity=cq.Solid.extrudeLinear(wire,[],cq.Vector(0,CAP_Y-WALL-13,0))
    cavity=cavity.cut(underside.translate((0,4,0))).intersect(cap_mask(FACE_RADIUS-WALL))
    s=blank.cut(cavity)
    for x,z,y,h,r in [(-38,-70,44,56,12),(26,-48,30,70,8)]:s=s.fuse(b.cyl(r,h,(x,y,z)).intersect(blank))
    for angle in b.POD_TIE_ANGLES:
        a=math.radians(angle);x,z=b.POD_TIE_RADIUS*math.cos(a),b.POD_TIE_RADIUS*math.sin(a)
        s=s.fuse(b.cyl(5.2,51,(x,9,z)).intersect(blank))
    for r,h,origin in [(41.25,41.5,(0,9,0)),(48.3,3.4,(0,50.3,0)),(40.2,36.5,(0,53.5,0))]:s=s.cut(b.cyl(r,h,origin))
    for angle in b.POD_TIE_ANGLES:
        a=math.radians(angle);x,z=b.POD_TIE_RADIUS*math.cos(a),b.POD_TIE_RADIUS*math.sin(a)
        s=s.cut(b.cyl(2.8,53,(x,8,z))).cut(b.cyl(3.1,8,(x,60,z)))
    knee=cq.Workplane(obj=b.cyl(53,40.5,(0,50.5,-170))).edges().fillet(3).val();s=s.cut(knee)
    points=[]
    for knee in range(-156,-47,2):
        a=math.radians(knee-78)
        for dz in [0,-170]:
            x,z=28*math.cos(a),-28*math.sin(a)+dz
            for angle in range(0,360,30):points.append((x+9*math.cos(math.radians(angle)),z+9*math.sin(math.radians(angle))))
    import numpy as np
    from scipy.spatial import ConvexHull
    points=np.array(points);outline=points[ConvexHull(points).vertices].tolist()
    plane=cq.Plane(origin=(0,65.5,0),xDir=(1,0,0),normal=(0,-1,0))
    s=s.cut(cq.Workplane(plane).polyline(outline).close().extrude(-9).val()).cut(cl.folded_foot_space())
    for sign in [-1,1]:
        s=s.cut(sd.connector_parts(54.4,sign)[3]).cut(sd.cable_space(54.4,sign))
        center,tangent,_,radial=sd.port_frame(69.1,sign)
        plane=cq.Plane(origin=tuple(center-radial*5.5),xDir=tuple(tangent),normal=tuple(radial))
        wire=cq.Workplane(plane).rect(18,50).val();wire=wire.fillet2D(3,wire.Vertices())
        s=s.cut(cq.Solid.extrudeLinear(wire,[],cq.Vector(*(radial*21))))
    s=s.clean();assert s.isValid() and len(s.Solids())==1
    return s

@cache
def thigh_master():return build_thigh_master()

@cache
def thigh(outer):return compact.finish_thigh(thigh_master(),outer)

SHIN_ROWS=[(-18,44,34,1.2),(-40,35,34,9),(-75,32,34,11),(-105,29,34,11),(-136,25,34,10)]

def shin_wire(z,width,depth,radius,inset=0):
    wire=cq.Workplane('XY',origin=(b.shin_center(z),68,z)).rect(width-2*inset,depth-2*inset).val()
    return wire.fillet2D(max(.8,radius-inset),wire.Vertices())

@cache
def shin_master():
    blank=cq.Solid.extrudeLinear(cl.shin_outline(51),[],cq.Vector(0,34,0))
    blank=cq.Workplane(obj=blank).faces('>Y or <Y').edges().fillet(1.2).val()
    # The cam crown remains complete. Below it, rounded transverse sections
    # replace the slab crosssection while preserving the single side curve.
    rounding=smooth_loft([shin_wire(*row) for row in SHIN_ROWS])
    rounding=rounding.fuse(b.box(180,120,120,(0,68,42)))
    original_blank=blank
    blank=blank.intersect(rounding)
    # Broad local clamp lands keep screw-head and nut seats flat and supported.
    for z in [-30,-105]:blank=blank.fuse(b.cyl(8.6,34,(2,51,z)).intersect(original_blank))
    inner_rows=[(-26,40,34,4),(-40,35,34,9),(-75,32,34,11),(-105,29,34,11),(-128,26,34,10)]
    pocket=smooth_loft([shin_wire(*row,inset=4) for row in inner_rows])
    s=blank.cut(pocket)
    for z in [-30,-105]:s=s.fuse(b.cyl(8.6,34,(2,51,z)).intersect(blank))
    s=s.cut(b.cyl(14,11,(0,50,0))).cut(b.cyl(14,9,(0,77,0)))
    s=s.cut(b.cyl(8.2,48,(0,44,0))).cut(cl.shin_linkage_space())
    x,z=ic.PIN
    s=s.cut(b.cyl(5.3,10,(x,50,z))).cut(b.cyl(3.05,20,(x,60,z)))
    s=s.cut(b.cyl(6.3,8.4,(x,65.8,z))).cut(b.hex_nut(8.2,12,x,80,z,.01)).cut(b.cyl(2.7,12,(x,79.9,z)))
    for z in [-30,-105]:
        s=s.cut(b.cyl(4.05,18,(2,58,z))).cut(b.cyl(2.2,42,(2,46,z)))
        s=s.cut(b.cyl(4.1,8,(2,50,z))).cut(b.hex_nut(7.2,12,2,76,z,.01))
    for x in [-12.7,12.7]:s=s.cut(b.cyl(1.3,16,(x,61,0)))
    s=s.clean();assert s.isValid() and len(s.Solids())==1,('shin master',s.isValid(),len(s.Solids()))
    return s

@cache
def shin(outer):
    s=shin_master().intersect(b.box(120,60,240,(0,97 if outer else 37,-70))).clean()
    assert s.isValid() and len(s.Solids())==1
    return s
