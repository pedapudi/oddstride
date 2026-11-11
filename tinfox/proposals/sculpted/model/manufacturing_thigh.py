"""Two structural thigh halves with accessible machining and printing features.

The established motor, axle and linkage datums remain fixed. Manufacturing
supports are separate exports and never enter the assembled robot model.
"""
from functools import cache
import math
import cadquery as cq
import build as b
import seamless_limb as rounded
import compact_motor_thigh as compact

TOOL_RADIUS=1.5
SEAM_BLEND_RADIUS=3.0
LAND_RADIUS=4.0
LAND_Y=93.4

@cache
def inner_mask():
    plane=cq.Plane(origin=(-100,0,0),xDir=(0,1,0),normal=(1,0,0))
    wire=(cq.Workplane(plane).polyline([(-50,80),(50.3,80),(50.3,-38),
        (67,-82),(67,-230),(-50,-230)]).close().val())
    wire=wire.fillet2D(SEAM_BLEND_RADIUS,wire.Vertices())
    return cq.Solid.extrudeLinear(wire,[],cq.Vector(200,0,0))

def nut_corner_reliefs(shape,x,z,y,depth,af=7.2):
    # Six axial drill reliefs preserve the center of each nut-contact flat.
    # Toolpath and holder qualification remain a CAM task.
    radius=af/math.sqrt(3)
    for angle in range(0,360,60):
        a=math.radians(angle)
        shape=shape.cut(b.cyl(TOOL_RADIUS,depth,(x+radius*math.cos(a),y,z+radius*math.sin(a))))
    return shape

@cache
def thigh(outer):
    # A cylinder and a cone replace the six-section curved motor-cup loft.
    root=b.cyl(45.5,15,(0,9,0)).fuse(cq.Solid.makeCone(
        45.5,49,27,cq.Vector(0,24,0),cq.Vector(0,1,0))).clean()
    shape=compact.finish_thigh(rounded.build_thigh_master(root),outer,inner_mask())
    if outer:
        shape=nut_corner_reliefs(shape,-38,-70,76,26)
        # Two shallow exterior flats provide repeatable fixture contacts.
        # These remove less than 0.35 mm from the nominal 4 mm face skin.
        for x in [-20,20]:shape=shape.cut(b.cyl(LAND_RADIUS,8,(x,LAND_Y,0)))
        shape=shape.cut(cq.Solid.makeCone(9.2,9.7,.5,
            cq.Vector(0,96.5,-170),cq.Vector(0,1,0)))
    else:
        # An accessible motor-bore entry; cylindrical registration stays intact.
        shape=shape.cut(cq.Solid.makeCone(41.85,41.25,1,
            cq.Vector(0,9,0),cq.Vector(0,1,0)))
    shape=shape.clean()
    assert shape.isValid() and len(shape.Solids())==1
    return shape
