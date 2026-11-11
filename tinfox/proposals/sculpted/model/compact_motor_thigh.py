"""Review candidate: a structural motor cup within the two thigh shells.

The qualified generated limb remains the migration reference. This candidate
keeps the motor, bearing and linkage datums and needs its own fit qualification.
"""
from functools import cache
import math
import cadquery as cq
import cohesive_limb as baseline
import integrated_candidate as ic
import service_design as sd
import build as b

CAP_Y=94.0
ROOT_STATIONS=[(9,45.5),(18,45.5),(30,46),(40,47.7),(47,49),(51,49)]

@cache
def master():
    blank=baseline.thigh_outline(9).extrude(-(CAP_Y-9)).val()
    blank=cq.Workplane(obj=blank).faces('>Y').edges().fillet(5).val()
    original_underside=b.box(220,94,300,(0,0,-90))
    root=cq.Solid.makeLoft([cq.Wire.makeCircle(r,cq.Vector(0,y,0),cq.Vector(0,1,0)) for y,r in ROOT_STATIONS],False)
    # Preserve the motor cup inside the old blanket inboard truncation.
    blank=blank.cut(original_underside.cut(root)).clean()
    blank=cq.Workplane(obj=blank).faces('<Y').edges().fillet(1.2).val()
    inner_wire=baseline.thigh_outline(13).wires().val().offset2D(-4)[0].toNURBS()
    cavity=cq.Solid.extrudeLinear(inner_wire,[],cq.Vector(0,CAP_Y-4-13,0))
    cavity=cavity.cut(original_underside.translate((0,4,0)))
    shell=blank.cut(cavity)
    for x,z,y,h,r in [(-38,-70,44,56,12),(26,-48,30,70,8)]:
        shell=shell.fuse(b.cyl(r,h,(x,y,z)).intersect(blank))
    for angle in b.POD_TIE_ANGLES:
        a=math.radians(angle);x,z=b.POD_TIE_RADIUS*math.cos(a),b.POD_TIE_RADIUS*math.sin(a)
        shell=shell.fuse(b.cyl(5.2,51,(x,9,z)).intersect(blank))
    shell=shell.cut(b.cyl(41.25,41.5,(0,9,0)))
    shell=shell.cut(b.cyl(48.3,3.4,(0,50.3,0)))
    shell=shell.cut(b.cyl(40.2,36.5,(0,53.5,0)))
    for angle in b.POD_TIE_ANGLES:
        a=math.radians(angle);x,z=b.POD_TIE_RADIUS*math.cos(a),b.POD_TIE_RADIUS*math.sin(a)
        shell=shell.cut(b.cyl(2.8,53,(x,8,z))).cut(b.cyl(3.1,8,(x,60,z)))
    knee_space=cq.Workplane(obj=b.cyl(53,40.5,(0,50.5,-170))).edges().fillet(3).val()
    shell=shell.cut(knee_space)
    # Preserve exactly the existing all-angle rod corridor and folded foot cut.
    # Reuse the qualified analytic linkage corridor; no old cosmetic skin is
    # unioned into the new shell.
    points=[]
    for knee in range(-156,-47,2):
        a=math.radians(knee-78)
        for dz in [0,-170]:
            x,z=28*math.cos(a),-28*math.sin(a)+dz
            for u in range(0,360,30):points.append((x+9*math.cos(math.radians(u)),z+9*math.sin(math.radians(u))))
    import numpy as np
    from scipy.spatial import ConvexHull
    points=np.array(points);outline=points[ConvexHull(points).vertices].tolist()
    plane=cq.Plane(origin=(0,65.5,0),xDir=(1,0,0),normal=(0,-1,0))
    shell=shell.cut(cq.Workplane(plane).polyline(outline).close().extrude(-9).val())
    shell=shell.cut(baseline.folded_foot_space())
    for sign in [-1,1]:
        shell=shell.cut(sd.connector_parts(54.4,sign)[3]).cut(sd.cable_space(54.4,sign))
        # Rounded axial windows let the bare motor's sockets travel through
        # the cup during insertion; plugs are installed after the motor seats.
        center,tangent,_,radial=sd.port_frame(69.1,sign)
        plane=cq.Plane(origin=tuple(center-radial*5.5),xDir=tuple(tangent),normal=tuple(radial))
        wire=cq.Workplane(plane).rect(18,50).val()
        wire=wire.fillet2D(3,wire.Vertices())
        shell=shell.cut(cq.Solid.extrudeLinear(wire,[],cq.Vector(*(radial*21))))
    shell=shell.clean()
    assert shell.isValid(), 'Invalid compact thigh master'
    return shell,blank


@cache
def inner_half_mask():
    # A stepped split opens the stator-plate seat when the outer shell comes
    # off. It returns to the established knee split without moving bearings.
    plane=cq.Plane(origin=(-100,0,0),xDir=(0,1,0),normal=(1,0,0))
    profile=(cq.Workplane(plane).moveTo(-50,80).lineTo(50.3,80)
        .lineTo(50.3,-38).spline([(50.3,-45),(52,-52),(60,-64),(66,-74),(67,-82)],includeCurrent=True,tangents=[(0,-1),(0,-1)])
        .lineTo(67,-230).lineTo(-50,-230).close())
    return profile.extrude(200).val()

def finish_thigh(shape,outer,mask=None):
    mask=inner_half_mask() if mask is None else mask
    shape=shape.cut(mask) if outer else shape.intersect(mask)
    old=ic.source('thigh_outer' if outer else 'thigh_inner')
    stop=old.intersect(b.cyl(16,140,(0,0,-170))).translate((0,3 if outer else -1,0))
    if outer:
        stop=stop.fuse(b.cyl(16,6,(0,91,-170)))
        crown=cq.Solid.makeLoft([cq.Wire.makeCircle(r,cq.Vector(0,y,-170),cq.Vector(0,1,0)) for y,r in [(92,21),(94,20),(97,16)]],False)
        stop=stop.fuse(crown)
    else:stop=stop.cut(b.box(180,94,300,(0,0,-90)))
    shape=shape.fuse(stop).cut(b.cyl(6.1,140,(0,0,-170)))
    shape=shape.cut(b.cyl(9.2,12,(0,94.3,-170)) if outer else b.cyl(7.2,12,(0,37.4,-170)))
    for x,z in [(-38,-70),(26,-48)]:shape=shape.cut(b.cyl(2.2,70,(x,40,z)))
    shape=shape.cut(b.cyl(4.1,18,(-38,58,-70)))
    if outer:shape=shape.cut(b.hex_nut(7.2,26,-38,76,-70,.01))
    else:shape=shape.cut(b.cyl(4.1,15,(-38,43,-70)))
    shape=shape.cut(b.cyl(4.1,42,(26,48,-48)))
    shape=shape.cut(b.cyl(4.4,8,(26,42 if not outer else 90,-48)))
    shape=shape.clean()
    assert shape.isValid() and len(shape.Solids())==1,('compact thigh',outer,shape.isValid(),len(shape.Solids()))
    return shape

@cache
def thigh(outer):
    return finish_thigh(master()[0],outer)
