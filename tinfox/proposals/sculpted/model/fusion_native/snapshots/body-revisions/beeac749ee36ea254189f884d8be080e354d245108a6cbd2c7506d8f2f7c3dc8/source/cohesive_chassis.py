"""Intentional shoulder openings and accessible frame joints for the CAD review.

The metal frame carries the actuators. The removable polymer cover locates on
four lateral screw lands; it does not complete a motor bearing or frame joint.
"""
from functools import cache
import cadquery as cq
import build as b
from kinematics import ROOT

BASE=ROOT/'output/slim-limb-work'
COVER_SCREW_X=64.0
COVER_SCREW_Z=18.0
FRAME_TIE_Y=104.0
FRAME_PAD_X=115.0

@cache
def source(key):
    for folder in [BASE/'step',ROOT/'output/limb-refinement/step',ROOT/'output/integrated-candidate/step',
        ROOT/'output/service-design/step',ROOT/'output/step-parts']:
        file=folder/(key+'.step')
        if file.exists():return cq.importers.importStep(str(file)).val()
    raise FileNotFoundError(key)

def edge_mask():
    # One tangent bottom edge replaces the overlapping box/socket notches.
    # The top of the central roof remains the original torso surface.
    def p(x,z):return cq.Vector(x,-150,z)
    edges=[cq.Edge.makeLine(p(-126,80),p(-126,45)),
        cq.Edge.makeBezier([p(-126,45),p(-105,45),p(-96,-10),p(-64,-10)]),
        cq.Edge.makeLine(p(-64,-10),p(64,-10)),
        cq.Edge.makeBezier([p(64,-10),p(96,-10),p(105,45),p(126,45)]),
        cq.Edge.makeLine(p(126,45),p(126,80)),cq.Edge.makeLine(p(126,80),p(-126,80))]
    return cq.Solid.extrudeLinear(cq.Wire.assembleEdges(edges),[],cq.Vector(0,300,0))

@cache
def cover():
    # Rebuild the enclosure envelope rather than adding material over old cuts.
    outer=b.torso();s=outer.cut(b.torso(2.8)).intersect(b.box(250.8,260,120,(0,0,35)))
    s=s.intersect(edge_mask())
    # A vertical rounded plan boundary ends the roof above the rail/tie
    # hardware. It avoids blind interior reliefs and feathered corner tabs.
    plan=cq.Workplane('XY',origin=(0,0,-40)).rect(250.8,222.4).extrude(140).edges('|Z').fillet(52).val()
    s=s.intersect(plan)
    for x in [-28,28]:s=s.fuse(b.box(2.4,170,6,(x,0,47)).intersect(outer))
    window=cq.Workplane('XY',origin=(20,0,38)).rect(48.6,28.6).extrude(30).edges('|Z').fillet(4).val()
    s=s.cut(window)
    s=s.cut(b.cyl(4.8,15,(55,-27,42),(0,0,1)))
    opening=cq.Workplane('XY',origin=(149,0,-70)).rect(150,92).val()
    opening=opening.fillet2D(8,opening.Vertices())
    s=s.cut(cq.Solid.extrudeLinear(opening,[],cq.Vector(0,0,200)))
    # Keep an outward-open fixed-motor relief, then trim its intersections with
    # the designed lower edge. No separate rectangular ear windows survive.
    for front in [-1,1]:
        for side in [-1,1]:
            s=s.cut(b.cyl(41.25,49.4,(front*70.3,side*68,0),(front,0,0)))
            s=s.cut(b.cyl(42,7,(front*111.7,side*68,0),(front,0,0)))
    for x in [-COVER_SCREW_X,COVER_SCREW_X]:
        for side in [-1,1]:
            # Broad wall lands support the screw head without a separate tab.
            s=s.cut(b.cyl(1.7,10,(x,side*105,COVER_SCREW_Z),(0,side,0)))
    s=s.clean();assert s.isValid() and len(s.Solids())==1
    return s

@cache
def belly():
    s=source('belly_center_0')
    # Remove the thin end crescents. The remaining lower shell wraps only the
    # battery cassette; its motor-facing edge has a deliberate rounded plan.
    mask=cq.Workplane('XY',origin=(0,0,-110)).rect(174,220).extrude(150).edges('|Z').fillet(14).val()
    s=s.intersect(mask).clean();assert s.isValid() and len(s.Solids())==1
    return s

@cache
def rail(side):
    s=source('chassis_beam_'+str(side*102))
    # Remove the retired cover screw lands outside the original rail web.
    for x in [-112,112]:s=s.cut(b.box(12,5,13,(x,side*105.5,22)))
    for x in [-COVER_SCREW_X,COVER_SCREW_X]:
        boss=b.box(12,5,12,(x,side*105.5,COVER_SCREW_Z),1.5)
        s=s.fuse(boss)
        # A wide triangular rib bears on the web and the top flange.
        plane=cq.Plane(origin=(x-4,0,0),xDir=(0,1,0),normal=(1,0,0))
        rib=cq.Workplane(plane).polyline([(side*102,18),(side*108,22),(side*102,32)]).close().extrude(8).val()
        s=s.fuse(rib).cut(b.cyl(1.25,10,(x,side*100,COVER_SCREW_Z),(0,side,0)))
    for x in [-FRAME_PAD_X,FRAME_PAD_X]:
        # Integral aluminum pad replaces two loose nuts. Screws sit in the
        # transverse tie at Z36; there is no head-to-seat stand-off.
        pad=b.box(16,9,8,(x,side*FRAME_TIE_Y,30),1)
        s=s.fuse(pad)
        for dx in [-3,3]:s=s.cut(b.cyl(1.25,10,(x+dx,side*FRAME_TIE_Y,25),(0,0,1)))
    for front in [-1,1]:s=s.cut(crossmember(front))
    s=s.clean();assert s.isValid() and len(s.Solids())==1
    return s

def crossmember(front):
    x=121*front
    profile=[(-98,34),(-90,40.8),(90,40.8),(98,34),
        (98,36),(90,42.8),(-90,42.8),(-98,36)]
    w=cq.Workplane('YZ',origin=(x-6,0,0)).polyline(profile).close().val()
    s=cq.Solid.extrudeLinear(w,[],cq.Vector(12,0,0))
    for side in [-1,1]:
        foot=cq.Workplane('XY',origin=(front*FRAME_PAD_X,side*103.5,34)).rect(18,12).extrude(2).edges('|Z').fillet(1).val()
        s=s.fuse(foot)
        for dx in [-3,3]:
            sx=front*FRAME_PAD_X+dx
            s=s.cut(b.cyl(1.7,6,(sx,side*FRAME_TIE_Y,32),(0,0,1)))
            s=s.cut(cq.Solid.makeCone(1.7,3,1.3,cq.Vector(sx,side*FRAME_TIE_Y,34.7),cq.Vector(0,0,1)))
    for y in [-18,18]:s=s.cut(b.cyl(1.7,6,(x,y,38),(0,0,1)))
    if front>0:
        for y in [-24,24]:
            s=s.fuse(b.cyl(5,6.8,(x,y,34),(0,0,1)))
            s=s.cut(b.cyl(1.65,9,(x,y,33),(0,0,1)))
            s=s.cut(b.cyl(2.2,4,(x,y,40.8),(0,0,1)))
    assert s.isValid() and len(s.Solids())==1
    return s

def tie_screw(front,side,dx):
    x=FRAME_PAD_X*front+dx;y=side*FRAME_TIE_Y
    return b.cyl(1.5,6.7,(x,y,28),(0,0,1)).fuse(cq.Solid.makeCone(1.5,2.9,1.3,cq.Vector(x,y,34.7),cq.Vector(0,0,1)))

def cover_screw(x,side):
    return b.cyl(1.5,10,(x,side*111.2,COVER_SCREW_Z),(0,-side,0)).fuse(b.cyl(2.75,3,(x,side*111.2,COVER_SCREW_Z),(0,side,0)))

def smooth_thigh(outer,foot_clearance=True):
    import slim_limb as limb
    base=source('thigh_outer' if outer else 'thigh_inner') if foot_clearance else limb.thigh(outer,False)
    if not outer:return base
    import seamless_limb as rounded
    # Replace only the exterior depression. The existing internal cavity and
    # reinforced joint material remain; added material overlaps the old face.
    blank=limb.extrusion(limb.outline(9),85)
    blank=cq.Workplane(obj=blank).faces('>Y').edges().fillet(6).val()
    blank=blank.intersect(rounded.cap_mask(500))
    fill=blank.cut(limb.roof(2)).intersect(b.box(150,40,74,(0,90,-81)))
    s=base.fuse(fill)
    for x,z in [limb.REAR_CLAMP,limb.FRONT_CLAMP]:
        s=s.cut(b.cyl(2.2,70,(x,40,z))).cut(b.cyl(5.3,30,(x,79.4,z)))
    s=s.clean();assert s.isValid() and len(s.Solids())==1
    return s
