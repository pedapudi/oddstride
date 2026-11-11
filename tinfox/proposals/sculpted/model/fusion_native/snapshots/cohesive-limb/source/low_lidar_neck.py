"""Raised lidar seat integrated into the removable low-profile camera hood."""
import cadquery as cq
from kinematics import ROOT
from build import box, cyl

LIDAR_X=82.0
SEAT_Z=94.0
RISE=42.0

def reference(key):
    for folder in ['integrated-candidate/step','v0-rounded-body/step','service-design/step','step-parts']:
        path=ROOT/'output'/folder/(key+'.step')
        if path.exists():return cq.importers.importStep(str(path)).val()
    raise FileNotFoundError(key)

def ellipse(x,z,rx,ry):
    return cq.Workplane('XY',origin=(x,0,z)).ellipse(rx,ry).val()

def bridge_wire(x,width,bottom,top,radius):
    wire=cq.Workplane('YZ',origin=(x,0,(top+bottom)/2)).rect(width,top-bottom).val()
    return wire.fillet2D(radius,wire.Vertices())

def hood():
    # Broad aft root and shrinking crown form a low, hollow fairing. A loft
    # supplies the outer shape without a separate platform, stalk or bracket.
    outer=cq.Solid.makeLoft([ellipse(95,57,54,36),ellipse(93,65,51,36),
        ellipse(85,85,39,35),ellipse(LIDAR_X,SEAT_Z,34,34)],ruled=False)
    cavity=cq.Solid.makeLoft([ellipse(95,56,49,31),ellipse(93,65,46,31),
        ellipse(85,85,34,30),ellipse(LIDAR_X,89,29,29)],ruled=False)
    # A broad roof and two side walls carry the seat into the existing neck.
    # This also removes the visual pinch between a circular pedestal and hood.
    stations=[(98,60,58,93),(122,62,58,91),(148,64,66,89),(176,64,72,88)]
    bridge=cq.Solid.makeLoft([bridge_wire(x,w,lo,hi,4) for x,w,lo,hi in stations],ruled=False)
    bridge_cavity=cq.Solid.makeLoft([bridge_wire(x,w-10,lo-2,hi-5,2) for x,w,lo,hi in stations],ruled=False)
    fairing=outer.fuse(bridge).cut(cavity).cut(bridge_cavity)
    # The existing cradle owns the lower structural neck; retain its split.
    import integrated_candidate as ic
    lower=ic.neck_lower_region()
    fairing=fairing.cut(lower)
    result=reference('front_fascia').fuse(fairing).cut(bridge_cavity)
    # Open cable path from the sensor into the shared neck cavity. No new
    # cable connector specification or mounting bolt pattern is assumed.
    result=result.cut(cyl(9,42,(LIDAR_X,0,55),(0,0,1)))
    result=result.cut(box(55,28,12,(113,0,70),4))
    for y in [-16,16]:
        result=result.cut(cyl(3.1,80,(136,y,55),(0,0,1)))
    result=result.clean()
    assert result.isValid() and len(result.Solids())==1
    return result

def parts():
    result={'front_fascia':hood()}
    for key in ['lidar_base','lidar','lidar_lid']:
        # Use current low-profile datums; the oldest source has X=112.
        shape=reference(key);bb=shape.BoundingBox()
        shape=shape.translate((LIDAR_X-(bb.xmin+bb.xmax)/2,0,RISE))
        result[key]=shape
    return result

def parameters():
    return {'low_lidar_center_x_mm':LIDAR_X,'low_lidar_seat_z_mm':SEAT_Z,
        'low_lidar_raise_mm':RISE,'low_lidar_scan_band_z_mm':[98,116],
        'low_lidar_cable_bore_mm':18}
