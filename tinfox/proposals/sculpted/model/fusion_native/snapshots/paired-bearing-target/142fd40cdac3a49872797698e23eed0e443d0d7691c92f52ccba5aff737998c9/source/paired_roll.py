"""Paired 6810 support and an axially serviceable perpendicular motor cup.

All dimensions are millimetres. These are fit-prototype geometries; polymer
strength, bearing fits and preload require measured qualification.
"""
from functools import cache
import math
import cadquery as cq
import build as b
import service_design as sd

PARAMETERS = dict(
    roll_bearing_id_mm=50.0, roll_bearing_od_mm=65.0,
    roll_bearing_width_mm=7.0, roll_bearing_center_spacing_mm=14.0,
    roll_bearing_seat_diameter_mm=65.15, roll_journal_diameter_mm=49.90,
    roll_motor_shift_x_mm=-6.2, roll_motor_output_face_x_mm=-73.5,
    roll_bearing_rear_x_mm=-71.5, roll_bearing_front_x_mm=-57.5,
    roll_housing_rear_x_mm=-77.5, roll_housing_front_x_mm=-50.5,
    roll_housing_outer_radius_mm=36.0, roll_retainer_thickness_mm=2.0,
    roll_outer_shoulder_opening_mm=63.0,
    roll_inner_shoulder_diameter_mm=52.5,
    roll_inner_backplate_thickness_mm=2.0,
    carrier_motor_bore_mm=81.5, carrier_front_split_y_mm=-4.0,
    carrier_closure_bolt_radius_mm=47.0,
    pitch_x_offset=5.0,
    prototype_structural_load_qualified=False,
)
LUG_ANGLES = (20,140,260)
CUP_ANGLES = (90,215,325)

def layout():
    p=PARAMETERS
    face=-67.3+p['roll_motor_shift_x_mm']
    rear=face+p['roll_inner_backplate_thickness_mm']
    width=p['roll_bearing_width_mm'];span=p['roll_bearing_center_spacing_mm']
    return dict(face=face,rear=rear,front=rear+span,end=rear+span+width,
                housing_rear=face-4,seat=p['roll_bearing_seat_diameter_mm']/2,
                journal=p['roll_journal_diameter_mm']/2,
                outer_open=p['roll_outer_shoulder_opening_mm']/2,
                inner_land=p['roll_inner_shoulder_diameter_mm']/2,
                width=width,spacer=span-width,
                retainer=p['roll_retainer_thickness_mm'])

def annulus_x(ro,ri,x0,x1):
    return b.cyl(ro,x1-x0,(x0,0,0),(1,0,0)).cut(
        b.cyl(ri,x1-x0+2,(x0-1,0,0),(1,0,0)))

def polar(radius,angle):
    a=math.radians(angle);return radius*math.cos(a),radius*math.sin(a)

def valid(s):
    s=s.clean()
    assert s.isValid() and len(s.Solids())==1,(s.isValid(),len(s.Solids()))
    return s

@cache
def housing():
    p=PARAMETERS;l=layout();back,end=l['housing_rear'],l['end']
    s=annulus_x(36,l['seat'],back,end)
    # Bore and rear outer-race abutment are reached from the open front.
    s=s.fuse(annulus_x(36,l['outer_open'],l['rear']-1.8,l['rear']))
    stator=annulus_x(41,27,back,back+3)
    for a in range(0,360,40):
        y,z=polar(36.5,a)
        stator=stator.cut(b.cyl(1.7,5,(back-1,y,z),(1,0,0)))
    s=s.fuse(stator)
    # Long standard stator screws are driven from the open front face. Their
    # heads clamp the housing, independently of the bearing-retainer screws.
    for a in range(0,360,40):
        y,z=polar(36.5,a)
        s=s.fuse(b.cyl(3.5,end-back,(back,y,z),(1,0,0)))
        s=s.cut(b.cyl(1.7,end-back+2,(back-1,y,z),(1,0,0)))
    # Chassis ear datums remain at their established coordinates.
    for z in [-12,24]:
        ear=b.box(11,13,11,(-59.5,26.5,z),2)
        ear=ear.cut(b.cyl(1.7,30,(-59.5,7,z),(0,1,0)))
        s=s.fuse(ear)
    for a in LUG_ANGLES:
        y,z=polar(37,a)
        s=s.fuse(b.cyl(4.5,end-back,(back,y,z),(1,0,0)))
        s=s.cut(b.cyl(1.7,end-back+2,(back-1,y,z),(1,0,0)))
        # An open rear hex pocket gives ordinary nuts a straight insertion path.
        depth=end+l['retainer']-25+.5+2.4-back
        nut=b.hex_nut(5.8,depth,0,0,0,.01)
        nut=nut.rotate((0,0,0),(0,0,1),-90).translate((back,y,z))
        s=s.cut(nut)
    s=s.cut(b.cyl(l['seat'],end-l['rear'],(l['rear'],0,0),(1,0,0)))
    # Ear and lug unions must not refill any motor-stator through bore.
    for a in range(0,360,40):
        y,z=polar(36.5,a)
        s=s.cut(b.cyl(1.7,end-back+2,(back-1,y,z),(1,0,0)))
    return valid(s)

@cache
def retainer():
    l=layout();end=l['end'];h=l['retainer']
    s=annulus_x(36,l['outer_open'],end,end+h)
    for a in LUG_ANGLES:
        y,z=polar(37,a)
        s=s.fuse(b.cyl(4.5,h,(end,y,z),(1,0,0)))
        s=s.cut(b.cyl(1.7,h+2,(end-1,y,z),(1,0,0)))
    for a in range(0,360,40):
        y,z=polar(36.5,a)
        s=s.cut(b.cyl(3.15,h+2,(end-1,y,z),(1,0,0)))
    return valid(s)

def bearing(index):
    l=layout();x=l['rear']+PARAMETERS['roll_bearing_center_spacing_mm']*index
    return annulus_x(PARAMETERS['roll_bearing_od_mm']/2,PARAMETERS['roll_bearing_id_mm']/2,x,x+l['width'])

def spacer(outer):
    l=layout();x=l['rear']+l['width'];end=l['front']
    return annulus_x(PARAMETERS['roll_bearing_od_mm']/2-.05,l['outer_open'],x,end) if outer else annulus_x(l['inner_land'],PARAMETERS['roll_bearing_id_mm']/2+.05,x,end)

def inner_backplate():
    l=layout();s=annulus_x(l['inner_land'],7,l['face'],l['rear'])
    for a in range(0,360,60):
        y,z=polar(12,a);s=s.cut(b.cyl(2.2,l['rear']-l['face']+2,(l['face']-1,y,z),(1,0,0)))
    return valid(s)

def bolt_x(diameter,length,face,y,z,head_diameter,head_height):
    return b.cyl(diameter/2,length,(face-length,y,z),(1,0,0)).fuse(
        b.cyl(head_diameter/2,head_height,(face,y,z),(1,0,0)))

@cache
def cup(front=1):
    l=layout();end=l['end'];split=PARAMETERS['carrier_front_split_y_mm']
    # Open toward the output side so the motor can be inserted along -Y.
    s=b.ring(44,PARAMETERS['carrier_motor_bore_mm']/2,split+48.4,-48.4)
    s=s.fuse(b.ring(44,12,2.5,-48.4))
    # Socket channels are open to the front, not trapped radial apertures.
    for sign in [-1,1]:
        slot=sd.port_box(18,40,21,0,sign,-5.5).translate((0,13.4,0))
        s=s.cut(slot)
    for sign in [-1,1]:s=s.cut(sd.cable_space(0,sign))
    for a in CUP_ANGLES:
        x,z=polar(47,a)
        s=s.fuse(b.cyl(6,split+11.9,(x,-11.9,z)))
        s=s.fuse(b.cyl(4.8,1,(x,split,z)))
        s=s.cut(b.cyl(2.2,11,(x,-13,z)))
        # Nut and open-ended wrench enter radially from outside the cup.
        # The open slot is reachable with a radial straight-tool setup.
        slot=b.box(50,5.5,22,(62,-14.65,0))
        slot=slot.rotate((0,0,0),(0,1,0),-a)
        s=s.cut(slot)
    s=s.translate((front*PARAMETERS['pitch_x_offset'],0,0))
    # New journal is supported between both bearing centers.
    journal=annulus_x(l['journal'],7,l['rear'],end)
    journal=journal.fuse(annulus_x(l['inner_land'],7,end,end+.8),
                         annulus_x(29,7,end+.8,end+1.7))
    # A broad web stays inside the retainer opening while behind its face.
    web_end=-40.8+PARAMETERS['pitch_x_offset']
    web_width=web_end-(end+1)
    web=b.box(web_width,split+25,40,((end+1+web_end)/2,(split-25)/2,0),2)
    web=web.intersect(b.cyl(30,web_end+51,(-51,0,0),(1,0,0)))
    if front<0: web=web.mirror('YZ');journal=journal.mirror('YZ')
    s=s.fuse(web,journal)
    # Recessed ordinary M4 x 25 flat-head output screws clear the rotating
    # thigh. Their total length includes the head; nominal engagement is4mm.
    for a in range(0,360,60):
        y,z=polar(12,a)
        bore=b.cyl(2.2,end-l['face']+5,(l['face']-.5,y,z),(1,0,0))
        face=end-2
        head=b.cyl(4.65,130,(face,y,z),(1,0,0))
        seat=cq.Solid.makeCone(2.2,4.5,2.3,cq.Vector(face-2.3,y,z),cq.Vector(1,0,0))
        if front<0:bore=bore.mirror('YZ');head=head.mirror('YZ');seat=seat.mirror('YZ')
        s=s.cut(bore).cut(head).cut(seat)
    # Open front-side window makes the roll screws reachable through the empty
    # motor cup, before fitting the perpendicular motor and its closure.
    s=s.cut(b.box(90,22,32,((50+PARAMETERS['pitch_x_offset'])*front,-8,0),3))
    return valid(s)

@cache
def closure(front=1):
    split=PARAMETERS['carrier_front_split_y_mm']
    s=b.ring(44,27,-.9-split,split)
    for a in CUP_ANGLES:
        x,z=polar(47,a)
        s=s.fuse(b.cyl(6,-.9-split,(x,split,z)))
        s=s.cut(b.cyl(2.2,6,(x,-5.5,z)))
        s=s.cut(b.cyl(4.95,1.1,(x,split,z)))
    for a in range(0,360,40):
        x,z=polar(36.5,a)
        s=s.cut(b.cyl(1.7,6,(x,-5.5,z)))
        # Flat-head recess accessible directly from the output side.
        s=s.cut(cq.Solid.makeCone(1.7,3.15,1.45,cq.Vector(x,-2.35,z),cq.Vector(0,1,0)))
    return valid(s.translate((front*PARAMETERS['pitch_x_offset'],0,0)))

def hardware():
    result={};l=layout();end=l['end']
    for a in range(0,360,40):
        y,z=polar(36.5,a)
        result[f'roll_stator_bolt_{a}']=bolt_x(3,30,end,y,z,5.6,1.65)
    for a in LUG_ANGLES:
        y,z=polar(37,a)
        result[f'roll_retainer_bolt_{a}']=bolt_x(3,25,end+l['retainer'],y,z,5.6,1.65)
        nut=b.hex_nut(5.5,2.4,0,0,0,1.5).rotate((0,0,0),(0,0,1),-90)
        result[f'roll_retainer_nut_{a}']=nut.translate((end+l['retainer']-25+.5,y,z))
    for a in CUP_ANGLES:
        x,z=polar(47,a)
        result[f'carrier_closure_bolt_{a}']=b.cyl(2,16,(x,-16.1,z)).fuse(b.cyl(3.8,2.2,(x,-.1,z)))
        result[f'carrier_closure_washer_{a}']=b.ring(4.5,2.15,.8,-.9,z,x)
        result[f'carrier_closure_nut_{a}']=b.hex_nut(7,3.2,0,-15.1,0,2).rotate(
            (0,0,0),(0,1,0),-a).translate((x,0,z))
    for a in range(0,360,40):
        x,z=polar(36.5,a)
        result[f'hip_stator_bolt_{a}']=b.cyl(1.5,6.55,(x,-8.9,z)).fuse(
            cq.Solid.makeCone(1.5,2.95,1.45,cq.Vector(x,-2.35,z),cq.Vector(0,1,0)))
    for a in range(0,360,60):
        y,z=polar(12,a)
        face=end-2
        result[f'roll_output_bolt_{a}']=b.cyl(2,22.7,(face-25,y,z),(1,0,0)).fuse(
            cq.Solid.makeCone(2,4.3,2.3,cq.Vector(face-2.3,y,z),cq.Vector(1,0,0)))
    return result

def custom_parts(front=1):
    flip=lambda s:s if front>0 else s.mirror('YZ')
    return {f'roll_cartridge_{front}':flip(housing()),
            f'roll_outer_retainer_{front}':flip(retainer()),
            f'motor_carrier_{front}':cup(front),f'hip_stator_closure_{front}':closure(front),
            f'roll_inner_backplate_{front}':flip(inner_backplate()),
            f'roll_inner_spacer_{front}':flip(spacer(False)),
            f'roll_outer_spacer_{front}':flip(spacer(True))}
