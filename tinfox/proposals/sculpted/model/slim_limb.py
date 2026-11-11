"""Slender structural thigh and rounded motor mounts around fixed joint datums.

The knee actuator remains proximal. Only the custom tie circle and one shell
clamp move; motor bolt circles, crank geometry and bearing datums stay fixed.
"""
from functools import cache
import math
import cadquery as cq
import build as b
import cohesive_limb as cl
import integrated_candidate as ic
import seamless_limb as rounded
import manufacturing_thigh as manufacturing
import service_design as sd
from kinematics import ROOT

BASE=ROOT/'output/manufacturing-thigh-work'
TIE_RADIUS=43.5
CASE_BORE_RADIUS=40.25
CASE_OUTER_RADIUS=45.4
TIE_BOSS_RADIUS=7.5
PLATE_OUTER_RADIUS=40.5
PLATE_BOSS_RADIUS=4.5
PLATE_ASSEMBLY_CLEARANCE=0.3
WALL=8.0
REAR_CLAMP=(-36.0,-66.0)
FRONT_CLAMP=(5.0,-70.0)
ROOF_BEZIER=[[(-117,94),(-108,94),(-105,86),(-90,86)],
    [(-90,86),(-76,86),(-61,94),(-45,94)]]

def point(x,y,z):return cq.Vector(x,y,z)

def circle_point(center,r,angle,y):
    a=math.radians(angle)
    return point(center[0]+r*math.cos(a),y,center[1]+r*math.sin(a))

def arc(center,r,start,end,y):
    return cq.Edge.makeThreePointArc(circle_point(center,r,start,y),
        circle_point(center,r,(start+end)/2,y),circle_point(center,r,end,y))

def lobed_wire(radius,boss,y,tie_radius=TIE_RADIUS):
    """Convex envelope of a central circle and three boss circles, using arcs."""
    delta=math.degrees(math.acos((radius-boss)/tie_radius));edges=[]
    assert delta<60
    for theta in b.POD_TIE_ANGLES:
        center=(tie_radius*math.cos(math.radians(theta)),tie_radius*math.sin(math.radians(theta)))
        start,end=theta-delta,theta+delta
        edges.extend([cq.Edge.makeLine(circle_point((0,0),radius,start,y),circle_point(center,boss,start,y)),
            arc(center,boss,start,end,y),
            cq.Edge.makeLine(circle_point(center,boss,end,y),circle_point((0,0),radius,end,y)),
            arc((0,0),radius,end,theta+120-delta,y)])
    return cq.Wire.assembleEdges(edges)

def rounded_triangle(y,boss=5.5):
    """Three lines and three tangent arcs around the tie centers."""
    edges=[]
    for theta in b.POD_TIE_ANGLES:
        center=(TIE_RADIUS*math.cos(math.radians(theta)),TIE_RADIUS*math.sin(math.radians(theta)))
        next_center=(TIE_RADIUS*math.cos(math.radians(theta+120)),TIE_RADIUS*math.sin(math.radians(theta+120)))
        edges.extend([arc(center,boss,theta-60,theta+60,y),cq.Edge.makeLine(
            circle_point(center,boss,theta+60,y),circle_point(next_center,boss,theta+60,y))])
    return cq.Wire.assembleEdges(edges)

def extrusion(wire,depth):return cq.Solid.extrudeLinear(wire,[],point(0,depth,0))

def output_pin_tail_space():
    # True swept annular sector, rather than its convex hull: the inner
    # radius preserves the complete shaft/bearing backup lands.
    y=85.5;r=4.25;center=(0,-170)
    upper=(28*math.cos(math.radians(126)),-170+28*math.sin(math.radians(126)))
    lower=(28*math.cos(math.radians(234)),-170+28*math.sin(math.radians(234)))
    wire=cq.Wire.assembleEdges([arc(center,28+r,126,234,y),arc(lower,r,234,414,y),
        arc(center,28-r,234,126,y),arc(upper,r,306,486,y)])
    return extrusion(wire,3.5)

@cache
def plate():
    s=extrusion(lobed_wire(PLATE_OUTER_RADIUS,PLATE_BOSS_RADIUS,50.5),3)
    for theta in b.POD_TIE_ANGLES:
        a=math.radians(theta)
        s=s.fuse(b.cyl(PLATE_BOSS_RADIUS,1.5,(TIE_RADIUS*math.cos(a),53.5,TIE_RADIUS*math.sin(a))))
    s=s.cut(b.cyl(30,5,(0,49.5,0)))
    for theta in range(20,380,40):
        a=math.radians(theta);s=s.cut(b.cyl(1.7,5,(36.5*math.cos(a),49.5,36.5*math.sin(a))))
    for theta in b.POD_TIE_ANGLES:
        a=math.radians(theta);s=s.cut(b.cyl(1.7,7,(TIE_RADIUS*math.cos(a),49.5,TIE_RADIUS*math.sin(a))))
    s=s.clean();assert s.isValid() and len(s.Solids())==1
    return s

@cache
def hub():
    s=extrusion(rounded_triangle(5),3).fuse(b.ring(20,6,5,0)).cut(b.cyl(6,12,(0,-1,0)))
    # Broad integral ribs shorten the unsupported plate span under motor
    # overturning loads. They stay inside the motor-face radial envelope.
    for theta in b.POD_TIE_ANGLES:
        rib=b.box(12,4.5,20,(0,2.75,27),1.2).rotate((0,0,0),(0,1,0),90-theta)
        s=s.fuse(rib)
        a=math.radians(theta)
        s=s.fuse(b.cyl(6,1.5,(TIE_RADIUS*math.cos(a),8,TIE_RADIUS*math.sin(a))))
    for theta in range(0,360,60):
        a=math.radians(theta);x,z=12*math.cos(a),12*math.sin(a)
        s=s.cut(b.cyl(2.2,13,(x,0,z))).cut(b.cyl(3.8,4.5,(x,3.7,z)))
    for theta in b.POD_TIE_ANGLES:
        a=math.radians(theta);s=s.cut(b.cyl(1.7,11,(TIE_RADIUS*math.cos(a),0,TIE_RADIUS*math.sin(a))))
    # Retain the original 48 mm rotating radial envelope at the hip carrier.
    # Local thickening stays within that envelope and preserves the original
    # 2.8 mm minimum outer ligament around each tie hole.
    s=s.intersect(b.cyl(48,12,(0,-1,0)))
    s=s.clean();assert s.isValid() and len(s.Solids())==1
    return s

def shifted_source(key,offset):
    for folder in [BASE/'step',ROOT/'output/limb-refinement/step',ROOT/'output/integrated-candidate/step',
        ROOT/'output/v0-rounded-body/step',ROOT/'output/service-design/step',ROOT/'output/step-parts']:
        path=folder/(key+'.step')
        if path.exists():return cq.importers.importStep(str(path)).val().translate(offset)
    raise FileNotFoundError(key)

def tie_part(key,theta):
    a=math.radians(theta);dr=TIE_RADIUS-b.POD_TIE_RADIUS
    if key.startswith('pod_sleeve_'):
        x,z=TIE_RADIUS*math.cos(a),TIE_RADIUS*math.sin(a)
        return b.ring(2.5,1.7,41,9.5,z,x).fuse(b.ring(2.5,1.7,6,55,z,x))
    return shifted_source(key,(dr*math.cos(a),0,dr*math.sin(a)))

def clamp_part(key):return shifted_source(key,(REAR_CLAMP[0]+38,0,REAR_CLAMP[1]+70))

def front_clamp_part(key):
    source={'sleeve_1':'sleeve_0','bolt_1':'bolt_0','thigh_clamp_nut_1':'thigh_clamp_nut_0'}[key]
    return shifted_source(source,(FRONT_CLAMP[0]+38,0,FRONT_CLAMP[1]+70))

def pin_part(key):
    # Preserve the loaded 6 x 20 mm shoulder and full M5 nut engagement.
    # Only excess thread beyond Y=87 is shortened; the standard stock screw
    # needs deburring after this cut. No special low-profile head is required.
    return shifted_source(key,(0,0,0)).intersect(b.box(150,200,500,(0,-13,0))).clean()

def outline(y,rear_flare_mm=0):
    # Keep the shoulder trim clear of the cup's crown. Exact tangency here
    # creates touching face wires that some STL/STEP meshers cannot triangulate.
    upper=cq.Edge.makeEllipse(44.5,51,point(0,y,0),(0,-1,0),(1,0,0),0,180)
    left=[(-44.5,0),(-44.5,-24),(-44.8-.22*rear_flare_mm,-48),(-40-rear_flare_mm,-75),(-36.5-.27*rear_flare_mm,-100),(-32,-123),(-26,-146),(-21.5,-170)]
    right=[(21.5,-170),(10,-145),(-1,-116),(-1,-96),(14,-73),(34,-48),(43.8,-25),(44.5,0)]
    down=point(0,0,-1);up=point(0,0,1)
    return cq.Wire.assembleEdges([upper,
        cq.Edge.makeSpline([point(x,y,z) for x,z in left],tangents=[down,down]),
        cq.Edge.makeThreePointArc(point(-21.5,y,-170),point(0,y,-191.5),point(21.5,y,-170)),
        cq.Edge.makeSpline([point(x,y,z) for x,z in right],tangents=[up,up])])

@cache
def inner_mask():
    # Split the proximal cup through the two connector openings. Its upper
    # forward half belongs to the removable outer shell and connects directly
    # to that shell's crown, eliminating a disconnected inboard casing sector.
    _,tangent,_,_=sd.port_frame(54.4,1)
    plane=cq.Plane(origin=(0,0,0),xDir=(0,1,0),normal=tuple(tangent))
    front=cq.Workplane(plane).rect(500,700).extrude(300).val()
    return manufacturing.inner_mask().cut(front)

@cache
def roof(offset=0,reinforce=False):
    def p(z,y):return point(-100,y-offset,z)
    edges=[cq.Edge.makeLine(p(-250,-40),p(-250,94)),cq.Edge.makeLine(p(-250,94),p(-117,94))]
    for controls in ROOF_BEZIER:
        edges.append(cq.Edge.makeBezier([p(z,y-(2*(94-y)/8 if reinforce else 0)) for z,y in controls]))
    edges.extend([cq.Edge.makeLine(p(-45,94),p(100,94)),cq.Edge.makeLine(p(100,94),p(100,-40)),
        cq.Edge.makeLine(p(100,-40),p(-250,-40))])
    return cq.Solid.extrudeLinear(cq.Wire.assembleEdges(edges),[],point(200,0,0))

@cache
def master(foot_clearance=True,rear_flare_mm=0):
    blank=extrusion(outline(9,rear_flare_mm),85)
    blank=cq.Workplane(obj=blank).faces('>Y').edges().fillet(6).val()
    underside=b.box(220,94,300,(0,0,-90))
    root=b.cyl(CASE_OUTER_RADIUS,42,(0,9,0))
    # Rounded flange guards begin beyond the carrier's Y=29 mm envelope.
    # Cylindrical stock and three patterned rounded bosses avoid the unstable
    # cone/profile tangencies of the earlier intersection construction.
    for theta in b.POD_TIE_ANGLES:
        guard=b.box(12,19,10,(0,41.5,45),2).rotate((0,0,0),(0,1,0),90-theta)
        root=root.fuse(guard)
    root=root.clean()
    blank=blank.cut(underside.cut(root)).intersect(rounded.cap_mask(500)).intersect(roof()).clean()
    # Round the newly exposed waist-to-side transitions after the roof cut.
    waist_edges=[e for e in blank.Edges() if -150<e.Center().z<-55 and e.Center().y>80 and e.Length()>15]
    if waist_edges:
        blank=blank.fillet(2,waist_edges).clean()
    cavity=extrusion(outline(13,rear_flare_mm).offset2D(-WALL)[0].toNURBS(),77)
    cavity=cavity.cut(underside.translate((0,6,0))).intersect(rounded.cap_mask(496)).intersect(roof(4,True))
    s=blank.cut(cavity)
    # The inner knee cheek grows inward only as far as the existing screw
    # head. Its rounded integral pad overlaps the original wall by 2 mm.
    knee_pad=cq.Workplane(obj=b.cyl(45,4,(0,45,-170))).edges().fillet(1).val()
    s=s.fuse(knee_pad.intersect(extrusion(outline(45,rear_flare_mm),5)))
    for (x,z),r in [(REAR_CLAMP,8.8),(FRONT_CLAMP,8.8)]:
        s=s.fuse(b.cyl(r,56,(x,44,z)).intersect(blank))
    # The inner face is six millimetres thick. The outer skin thickens
    # smoothly to six millimetres at the waist through the roof controls.
    for theta in b.POD_TIE_ANGLES:
        a=math.radians(theta);x,z=TIE_RADIUS*math.cos(a),TIE_RADIUS*math.sin(a)
        s=s.fuse(b.cyl(5.2,51,(x,9,z)).intersect(blank))
        s=s.cut(b.cyl(2.8,53,(x,8,z))).cut(b.cyl(3.1,8,(x,60,z)))
        s=s.cut(b.cyl(6.3,1.2,(x,8.8,z)))
        s=s.cut(b.cyl(4.8,1.6,(x,53.5,z)))
    s=s.cut(b.cyl(CASE_BORE_RADIUS,41.5,(0,9,0)))
    s=s.cut(extrusion(lobed_wire(PLATE_OUTER_RADIUS+.3,PLATE_BOSS_RADIUS+.3,50.3),3.4))
    s=s.cut(b.cyl(40.2,36.5,(0,53.5,0)))
    knee=cq.Workplane(obj=b.cyl(53,36,(0,50.5,-170))).edges().fillet(3).val()
    s=s.cut(knee).cut(output_pin_tail_space())
    # Equal cranks keep the pushrod vertical in thigh coordinates. The broad
    # end eyes fit inside the crank and knee cavities; this slot fits its stem.
    xmin=-28-4.5;xmax=28*math.cos(math.radians(126))+4.5
    zmin=-28*math.sin(math.radians(126))-158;zmax=28*math.sin(math.radians(126))-12
    s=s.cut(b.box(xmax-xmin,9,zmax-zmin,((xmin+xmax)/2,70,(zmin+zmax)/2)))
    if foot_clearance:s=s.cut(cl.folded_foot_space())
    for sign in [-1,1]:
        s=s.cut(sd.connector_parts(54.4,sign)[3]).cut(sd.cable_space(54.4,sign))
        center,tangent,_,radial=sd.port_frame(69.1,sign)
        plane=cq.Plane(origin=tuple(center-radial*5.5),xDir=tuple(tangent),normal=tuple(radial))
        wire=cq.Workplane(plane).rect(18,50).val();wire=wire.fillet2D(3,wire.Vertices())
        s=s.cut(cq.Solid.extrudeLinear(wire,[],cq.Vector(*(radial*21))))
    # Open the lower cable recess as one accessible window, eliminating
    # disconnected lips outside the cable path rather than retaining scraps.
    center,tangent,_,radial=sd.port_frame(77.2,-1)
    plane=cq.Plane(origin=tuple(center-radial*6),xDir=tuple(tangent),normal=tuple(radial))
    window=cq.Workplane(plane).rect(30,36).val();window=window.fillet2D(4,window.Vertices())
    s=s.cut(cq.Solid.extrudeLinear(window,[],cq.Vector(*(radial*45))))
    s=s.clean();assert s.isValid() and len(s.Solids())==1,('master',s.isValid(),[(t.Volume(),t.Center().toTuple()) for t in s.Solids()])
    return s

@cache
def thigh(outer,foot_clearance=True,rear_flare_mm=0):
    shape=master(foot_clearance,rear_flare_mm).cut(inner_mask()) if outer else master(foot_clearance,rear_flare_mm).intersect(inner_mask())
    old=ic.source('thigh_outer' if outer else 'thigh_inner')
    stop=old.intersect(b.cyl(16,140,(0,0,-170))).translate((0,3 if outer else -1,0))
    if outer:
        stop=stop.fuse(b.cyl(16,6,(0,91,-170)))
        # Remove the inherited end stub beyond the intended crown face. Leaving
        # it above Y97 closes the entry chamfer into a reverse-facing lip.
        stop=stop.cut(b.box(80,20,80,(0,107,-170)))
        crown=cq.Solid.makeLoft([cq.Wire.makeCircle(r,point(0,y,-170),point(0,1,0)) for y,r in [(92,21),(94,20),(97,16)]],False)
        stop=stop.fuse(crown)
    else:stop=stop.cut(b.box(180,94,300,(0,0,-90)))
    shape=shape.fuse(stop).cut(b.cyl(6.1,140,(0,0,-170)))
    shape=shape.cut(b.cyl(9.2,12,(0,94.3,-170)) if outer else b.cyl(7.2,12,(0,37.4,-170)))
    for x,z in [REAR_CLAMP,FRONT_CLAMP]:shape=shape.cut(b.cyl(2.2,70,(x,40,z)))
    for x,z in [REAR_CLAMP,FRONT_CLAMP]:
        shape=shape.cut(b.cyl(4.1,18,(x,58,z))).cut(b.cyl(4.1,15,(x,43,z)))
        if outer:
            shape=shape.cut(b.hex_nut(7.2,3.4,x,76,z,.01)).cut(b.cyl(5.3,30,(x,79.4,z)))
            for theta in range(0,360,60):
                a=math.radians(theta);r=7.2/math.sqrt(3)-.5
                shape=shape.cut(b.cyl(1.5,3.4,(x+r*math.cos(a),76,z+r*math.sin(a))))
    if outer:
        shape=shape.cut(cq.Solid.makeCone(9.2,9.7,.5,point(0,96.5,-170),point(0,1,0)))
        # The closed half slides over the preassembled motor and stator plate
        # from the inboard side. Open the complete plate silhouette, including
        # its tangent webs, while retaining the outboard stop beyond Y55.2.
        shape=shape.cut(extrusion(lobed_wire(PLATE_OUTER_RADIUS+PLATE_ASSEMBLY_CLEARANCE,
            PLATE_BOSS_RADIUS+PLATE_ASSEMBLY_CLEARANCE,-5),60.2))
        # Open the socket-head insertion and driver routes through the crown.
        # The short tube ends at Y61; its end supports the head independently
        # of the surrounding polymer. Preserve that seating plane.
        for theta in b.POD_TIE_ANGLES:
            angle=math.radians(theta)
            shape=shape.cut(b.cyl(3.2,49,(TIE_RADIUS*math.cos(angle),61,TIE_RADIUS*math.sin(angle))))
    else:
        shape=shape.cut(cq.Solid.makeCone(CASE_BORE_RADIUS+.6,CASE_BORE_RADIUS,1,point(0,9,0),point(0,1,0)))
        # A shallow rounded clearance for the fixed shoulder screw restores
        # the coupled roll/pitch poses. The six-millimetre inner face retains
        # at least 4.3 mm nominal material beneath this 1.7 mm edge recess.
        shape=shape.cut(b.cyl(5.5,5.7,(-45,43,-38)))
    shape=shape.clean();assert shape.isValid() and len(shape.Solids())==1,('thigh',outer,shape.isValid(),[(s.Volume(),s.Center().toTuple()) for s in shape.Solids()])
    return shape
