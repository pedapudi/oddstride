"""Shared clamshell envelope, with separate motor and bearing interfaces."""
from functools import cache
import math
import cadquery as cq
import build as b
import integrated_candidate as ic
import service_design as sd
from integrated_candidate import box, cyl, ring

CROWN_RADIUS=21.0
BEARING_INNER_Y=53.0
BEARING_OUTER_Y=77.0
BEARING_WIDTH=8.0
SHAFT_CHANNEL_Y=(66.5,73.5)


@cache
def shin_linkage_space():
    """Sweep the rod's narrow stem and tapered eye, not an oversized capsule."""
    import numpy as np
    from scipy.spatial import ConvexHull
    x,z=ic.PIN
    # Rod outline from the output eye toward the input eye, in knee coordinates.
    # The 6 mm stem widens to a 15 mm eye over its first 12 mm of length.
    def sweep(outline):
        points=[]
        for knee in range(-156,-47):
            a=math.radians(-knee);co,si=math.cos(a),math.sin(a)
            for dx,dz in outline:
                xx=x+co*dx+si*dz;zz=z-si*dx+co*dz
                for u in range(0,360,30):points.append((xx+math.cos(math.radians(u)),zz+math.sin(math.radians(u))))
        points=np.array(points);poly=points[ConvexHull(points).vertices].tolist()
        plane=cq.Plane(origin=(0,SHAFT_CHANNEL_Y[0],0),xDir=(1,0,0),normal=(0,-1,0))
        return cq.Workplane(plane).polyline(poly).close().extrude(-(SHAFT_CHANNEL_Y[1]-SHAFT_CHANNEL_Y[0])).val()
    stem=sweep([(-3,12),(3,12),(3,158),(-3,158)])
    taper=sweep([(-7.5,0),(7.5,0),(3,12),(-3,12)])
    # Only the bushing flanges need the wider axial slot at the fixed output pin.
    return stem.fuse(taper,cyl(8.5,7,(x,66.5,z)),cyl(6.3,8.4,(x,65.8,z))).clean()


def thigh_outline(y):
    plane = cq.Plane(origin=(0,y,0), xDir=(1,0,0), normal=(0,-1,0))
    return (cq.Workplane(plane).moveTo(-49,0)
        .threePointArc((0,49),(49,0))
        .spline([(44,-30),(34,-50),(15,-77),(-5,-105),(-3,-122),(12,-147),(23,-170)], includeCurrent=True, tangents=[(0,-1),(0,-1)])
        .threePointArc((0,-193),(-23,-170))
        .spline([(-29,-146),(-40,-115),(-46,-75),(-43,-52),(-41,-36),(-46,-18),(-49,0)], includeCurrent=True, tangents=[(0,1),(0,1)])
        .close())


@cache
def folded_foot_space():
    def center(q):
        a=math.radians(q)
        return cq.Vector(-148*math.sin(a),67,-170-148*math.cos(a))
    start,middle,end=[center(q) for q in [-156,-102,-48]]
    path=cq.Wire.assembleEdges([cq.Edge.makeThreePointArc(start,middle,end)])
    a=math.radians(-156);tangent=(-math.cos(a),0,math.sin(a))
    plane=cq.Plane(origin=start,normal=tangent)
    swept=cq.Workplane(plane).circle(23.5).sweep(path).val()
    return swept.fuse(*[cq.Solid.makeSphere(23.5,p,angleDegrees1=-90,angleDegrees2=90) for p in [start,end]])


@cache
def thigh_master():
    # One continuous exterior supplies both halves. There is no union between
    # an inherited motor-cover skin and a separate replacement leg skin.
    blank = thigh_outline(9).extrude(-91).val()
    blank = cq.Workplane(obj=blank).faces('>Y').edges().fillet(7).val()
    # The inboard shell begins beyond the perpendicular roll carrier. The
    # three metal ties carry the stator plate; a redundant deep skirt would
    # sweep through the roll carrier and chassis when the hip rotates.
    underside=box(220,94,300,(0,0,-90))
    blank=blank.cut(underside).clean()
    blank=cq.Workplane(obj=blank).faces('<Y').edges().fillet(4).val()
    # A four-millimetre shell, open at the split, with a common side outline.
    # STEP cannot retain all offset-curve side faces without converting the
    # offset wire before extrusion. Keep the manufactured shell watertight.
    inner_wire=thigh_outline(13).wires().val().offset2D(-4)[0].toNURBS()
    cavity=cq.Solid.extrudeLinear(inner_wire,[],cq.Vector(0,83,0))
    cavity=cavity.cut(underside.translate((0,4,0)))
    shell=blank.cut(cavity)
    # Hardware is supported on broad lands tied into the common shell.
    for x,z,y,h,r in [(-38,-70,44,56,12),(26,-48,30,70,8)]:
        shell=shell.fuse(cyl(r,h,(x,y,z)).intersect(blank))
    for a in b.POD_TIE_ANGLES:
        x,z=b.POD_TIE_RADIUS*math.cos(math.radians(a)),b.POD_TIE_RADIUS*math.sin(math.radians(a))
        shell=shell.fuse(cyl(5.2,51,(x,9,z)).intersect(blank))
    # Actuator, flange and crank space. The cap is the structural outer face.
    shell=shell.cut(cyl(41.25,41.5,(0,9,0)))
    shell=shell.cut(cyl(48.3,3.4,(0,50.3,0)))
    shell=shell.cut(cyl(40.2,38,(0,53.5,0)))
    for a in b.POD_TIE_ANGLES:
        x,z=b.POD_TIE_RADIUS*math.cos(math.radians(a)),b.POD_TIE_RADIUS*math.sin(math.radians(a))
        shell=shell.cut(cyl(2.8,53,(x,8,z)))
        shell=shell.cut(cyl(3.1,8,(x,60,z)))
    # The same rounded knee opening passes through the two cheeks. It leaves
    # complete bearing backup lands, which are restored independently below.
    knee_space=cq.Workplane(obj=cyl(53,40.5,(0,50.5,-170))).edges().fillet(3).val()
    shell=shell.cut(knee_space)
    # Equal-crank pushrod corridor: convex envelope of eye centers with a 9 mm
    # radius, covering the entire stated knee range, not one display pose.
    points=[]
    for knee in range(-156,-47,2):
        a=math.radians(knee-78)
        for dz in [0,-170]:
            x=28*math.cos(a);z=-28*math.sin(a)+dz
            for u in range(0,360,30):
                points.append((x+9*math.cos(math.radians(u)),z+9*math.sin(math.radians(u))))
    import numpy as np
    from scipy.spatial import ConvexHull
    points=np.array(points);outline=points[ConvexHull(points).vertices].tolist()
    plane=cq.Plane(origin=(0,65.5,0),xDir=(1,0,0),normal=(0,-1,0))
    corridor=cq.Workplane(plane).polyline(outline).close().extrude(-9).val()
    shell=shell.cut(corridor)
    shell=shell.cut(folded_foot_space())
    for sign in [-1,1]:
        shell=shell.cut(sd.connector_parts(54.4,sign)[3]).cut(sd.cable_space(54.4,sign))
    return shell.clean(),blank


def thigh(outer):
    master,blank=thigh_master()
    split=box(180,90,300,(0,112 if outer else 22,-100))
    s=master.intersect(split)
    # Precision axial stops belong to the structural cheek, not an extra insert.
    old=ic.source('thigh_outer' if outer else 'thigh_inner')
    stop=old.intersect(cyl(16,140,(0,0,-170)))
    stop=stop.translate((0,3 if outer else -1,0))
    if outer:stop=stop.fuse(cyl(16,6,(0,91,-170)))
    else:stop=stop.cut(box(180,94,300,(0,0,-90)))
    s=s.fuse(stop).cut(cyl(6.1,140,(0,0,-170)))
    s=s.cut(cyl(9.2,12,(0,94.3,-170)) if outer else cyl(7.2,12,(0,37.4,-170)))
    for x,z in [(-38,-70),(26,-48)]:
        s=s.cut(cyl(2.2,70,(x,40,z)))
    s=s.cut(cyl(4.1,18,(-38,58,-70)))
    if outer:s=s.cut(b.hex_nut(7.2,26,-38,76,-70,.01))
    else:s=s.cut(cyl(4.1,15,(-38,43,-70)))
    s=s.cut(cyl(4.1,42,(26,48,-48)))
    s=s.cut(cyl(4.4,8,(26,42 if not outer else 90,-48)))
    cleaned=s.clean()
    s=cleaned if cleaned.isValid() else s
    if len(s.Solids())!=1:
        print('Disconnected regions',outer,[(a.Volume(),a.Center().toTuple()) for a in s.Solids()],flush=True)
    assert s.isValid() and len(s.Solids())==1,('thigh',outer,len(s.Solids()))
    return s


def carrier(front):
    source=ic.source('motor_carrier_'+str(front))
    # The screw tip sweeps an annulus at radius 43.5. A shallow rounded
    # bridge pocket provides 2 mm axial clearance without touching the journal.
    relief=box(12,6,44,(-front*45,4,0),1)
    s=source.cut(relief).clean()
    assert s.isValid() and len(s.Solids())==1
    return s


def shin_outline(y):
    """Retain the approved cam crown; continue its sides into one tapered stem."""
    x,z=ic.PIN;direction=math.atan2(z,x)
    alpha=math.acos((CROWN_RADIUS-10.5)/math.hypot(x,z))
    def p(cx,cz,r,a):return cq.Vector(cx+r*math.cos(a),y,cz+r*math.sin(a))
    left=cq.Vector(-CROWN_RADIUS,y,0);right=cq.Vector(CROWN_RADIUS,y,0)
    a=p(0,0,CROWN_RADIUS,direction+alpha);bb=p(x,z,10.5,direction+alpha)
    c=p(x,z,10.5,direction-alpha);d=p(0,0,CROWN_RADIUS,direction-alpha)
    end_x=b.shin_center(-136)
    lo=cq.Vector(end_x-11,y,-136);hi=cq.Vector(end_x+11,y,-136)
    edges=[cq.Edge.makeThreePointArc(left,p(0,0,CROWN_RADIUS,(math.pi+direction+alpha)/2),a),
        cq.Edge.makeLine(a,bb),cq.Edge.makeThreePointArc(bb,p(x,z,10.5,direction),c),
        cq.Edge.makeLine(c,d),cq.Edge.makeThreePointArc(d,p(0,0,CROWN_RADIUS,(direction-alpha)/2),right),
        cq.Edge.makeSpline([right,cq.Vector(18,y,-40),cq.Vector(16,y,-85),hi],tangents=[cq.Vector(0,0,-1),cq.Vector(-.08,0,-1)]),
        cq.Edge.makeLine(hi,lo),
        cq.Edge.makeSpline([lo,cq.Vector(-10,y,-85),cq.Vector(-15,y,-40),left],tangents=[cq.Vector(-.08,0,1),cq.Vector(0,0,1)])]
    return cq.Wire.assembleEdges(edges)


@cache
def shin_master():
    blank=cq.Solid.extrudeLinear(shin_outline(51),[],cq.Vector(0,34,0))
    # Soft exterior edges; the bearing bore and shoulder datums are machined
    # after this feature and therefore keep their circular locating surfaces.
    blank=cq.Workplane(obj=blank).faces('>Y or <Y').edges().fillet(1.2).val()
    assert blank.isValid(),'Shin exterior fillet must remain a valid solid'
    plane=cq.Plane(origin=(0,55,0),xDir=(1,0,0),normal=(0,-1,0))
    pocket=(cq.Workplane(plane).moveTo(-11,-25).lineTo(11,-25)
        .lineTo(8,-128).lineTo(-6,-128).close().extrude(-26).val())
    pocket=cq.Workplane(obj=pocket).edges('|Y').fillet(4).val()
    s=blank.cut(pocket)
    for zz in [-30,-105]:s=s.fuse(cyl(8.6,34,(2,51,zz)).intersect(blank))
    # Opposed, complete press seats with open extraction paths after splitting.
    s=s.cut(cyl(14,11,(0,50,0))).cut(cyl(14,9,(0,BEARING_OUTER_Y,0)))
    s=s.cut(cyl(8.2,48,(0,44,0))).cut(shin_linkage_space())
    x,z=ic.PIN
    s=s.cut(cyl(5.3,10,(x,50,z))).cut(cyl(3.05,20,(x,60,z)))
    s=s.cut(cyl(6.3,8.4,(x,65.8,z))).cut(b.hex_nut(8.2,12,x,80,z,.01)).cut(cyl(2.7,12,(x,79.9,z)))
    for zz in [-30,-105]:
        s=s.cut(cyl(4.05,18,(2,58,zz))).cut(cyl(2.2,42,(2,46,zz)))
        s=s.cut(cyl(4.1,8,(2,50,zz))).cut(b.hex_nut(7.2,12,2,76,zz,.01))
    for xx in [-12.7,12.7]:s=s.cut(cyl(1.3,16,(xx,61,0)))
    cleaned=s.clean()
    return cleaned if cleaned.isValid() else s


def shin(outer):
    s=shin_master().intersect(box(120,60,240,(0,97 if outer else 37,-70)))
    cleaned=s.clean()
    s=cleaned if cleaned.isValid() else s
    assert s.isValid() and len(s.Solids())==1,('shin',outer,len(s.Solids()))
    return s


def custom_parts():
    """The complete coordinated revision, including its relocated hardware."""
    shapes={kind+('_outer' if outer else '_inner'):fn(outer)
            for kind,fn in [('thigh',thigh),('shin',shin)] for outer in [False,True]}
    shapes.update({'motor_carrier_'+str(front):carrier(front) for front in [1,-1]})
    for key in ['sleeve_0','bolt_0','thigh_clamp_nut_0']:
        shapes[key]=cq.importers.importStep(str(ic.OUT/'step'/(key+'.step'))).val().translate((2,0,0))
    shapes.update(bearing_revisions())
    return shapes


def bearing_revisions():
    return {'bearing_inner':ic.source('bearing_inner').translate((0,-1,0)),
            'bearing_outer':ic.source('bearing_outer').translate((0,3,0)),
            'knee_inner_spacer':ring(7.75,6.1,16,61,-170)}


def geometry_parameters():
    return dict(knee_bearing_inner_y=BEARING_INNER_Y,knee_bearing_outer_y=BEARING_OUTER_Y,
                knee_bearing_width=BEARING_WIDTH,knee_crown_radius=CROWN_RADIUS,
                knee_shaft_channel_y=list(SHAFT_CHANNEL_Y))
