"""Low frame-mounted sensor cradle and independently removable smooth hood."""
from functools import cache
import cadquery as cq
from build import box,cyl,hex_nut
from low_lidar_neck import reference

LIDAR_X=121.0
SEAT_Z=80.0
SCREWS=[(92,-25),(92,25),(164,-18),(164,18)]
STATIONS=[(76,32,58,66),(92,78,58,77),(121,80,58,80),
          (150,70,58,78),(185,54,56,72),(216,38,40,59),
          (240,150,31,44),(248,178,32,43)]

def wire(x,w,lo,hi,r):
    q=cq.Workplane('YZ',origin=(x,0,(lo+hi)/2)).rect(w,hi-lo).val()
    return q.fillet2D(min(r,(hi-lo)/2-.2),q.Vertices())

def smooth_loft(wires):
    s=cq.Solid.makeLoft(wires,ruled=False)
    assert s.isValid(),'Loft must be valid before any booleans'
    return s

@cache
def envelope():
    return smooth_loft([wire(x,w,lo,hi,4) for x,w,lo,hi in STATIONS])

@cache
def hood():
    outer=envelope()
    inside=smooth_loft([wire(x,w-8,lo-3,hi-4,2) for x,w,lo,hi in STATIONS])
    assert len(inside.Solids())==1
    face=reference('front_fascia').intersect(box(45,240,200,(268.5,0,0)))
    s=outer.cut(inside).fuse(face)
    s=s.fuse(cyl(32,5,(LIDAR_X,0,75),(0,0,1))).cut(box(400,300,100,(160,0,130)))
    s=s.cut(cyl(9,60,(LIDAR_X,0,40),(0,0,1)))
    for x,y in SCREWS:
        s=s.fuse(cyl(6,20,(x,y,60),(0,0,1)).intersect(outer))
        s=s.cut(cyl(1.7,40,(x,y,50),(0,0,1))).cut(cyl(3.25,30,(x,y,73),(0,0,1)))
    if not s.isValid():s=s.fix()
    assert s.isValid() and len(s.Solids())==1,('hood',s.isValid(),len(s.Solids()))
    return s

@cache
def cradle():
    # Two feet bear directly on the metal crossmember. No cantilevered
    # printed crossbar, wrapped socket or front face retaining lip is needed.
    s=box(22,16,17.2,(121,-24,51.4),1)
    s=s.fuse(box(22,16,17.2,(121,24,51.4),1))
    profile=[(86,60),(174,60),(174,53),(86,53)]
    for side in [-1,1]:
        plane=cq.Plane(origin=(0,side*16,0),xDir=(1,0,0),normal=(0,-1,0))
        wall=cq.Workplane(plane).polyline(profile).close().extrude(-side*6).val()
        s=s.fuse(wall)
    # Transverse web below the cable path connects the two fore/aft rails.
    s=s.fuse(box(16,44,5,(121,0,55.5)))
    for x,y in SCREWS:
        s=s.fuse(cyl(7,10,(x,y,50),(0,0,1)))
        s=s.cut(cyl(1.7,20,(x,y,48),(0,0,1)))
        pocket=hex_nut(5.8,8.4,0,0,0,.01).rotate((0,0,0),(1,0,0),90).translate((x,y,48))
        s=s.cut(pocket)
    for y in [-24,24]:
        s=s.cut(cyl(2.2,35,(121,y,30),(0,0,1))).cut(cyl(5,20,(121,y,53.2),(0,0,1)))
    s=s.clean()
    assert s.isValid() and len(s.Solids())==1,('cradle',s.isValid(),len(s.Solids()))
    return s

def body_cover():
    opening=cq.Workplane('XY',origin=(149,0,-70)).rect(150,92).val()
    opening=opening.fillet2D(8,opening.Vertices())
    cut=cq.Solid.extrudeLinear(opening,[],cq.Vector(0,0,200))
    # Remove the obsolete roof-mounted lidar seat and close its opening at
    # the main roof height before cutting the independent service opening.
    s=reference('body_center_0').cut(cyl(35,15,(82,0,45),(0,0,1)))
    s=s.fuse(cyl(36,3,(82,0,52.5),(0,0,1))).cut(cut).clean()
    # Open the former blind frame pockets downwards so the cover can lift
    # over the rails and crossmembers without removing the chassis hardware.
    for side in [-1,1]:
        s=s.cut(box(264,15,100,(0,side*99.5,-14.5)))
        s=s.cut(box(14,206,100,(side*121,0,-6.7)))
    s=s.clean()
    assert s.isValid() and len(s.Solids())==1
    return s

def hardware():
    result={}
    for i,(x,y) in enumerate(SCREWS):
        result[f'sensor_hood_screw_{i}']=cyl(1.5,20,(x,y,53),(0,0,1)).fuse(cyl(2.75,3,(x,y,73),(0,0,1)))
        result[f'sensor_hood_nut_{i}']=hex_nut(5.5,2.4,0,0,0,1.5).rotate((0,0,0),(1,0,0),90).translate((x,y,54))
    for side,y in enumerate([-24,24]):
        result[f'sensor_root_screw_{side}']=cyl(2,20,(121,y,34),(0,0,1)).fuse(cyl(3.5,4,(121,y,54),(0,0,1)))
        result[f'sensor_root_washer_{side}']=cyl(4.5,.8,(121,y,53.2),(0,0,1)).cut(cyl(2.15,2,(121,y,53),(0,0,1)))
        result[f'sensor_root_nut_{side}']=hex_nut(7,3.2,0,0,0,2).rotate((0,0,0),(1,0,0),90).translate((121,y,37.6))
    return result

def parts():
    shapes={'front_fascia':hood(),'body_nose_surround':cradle(),'body_center_0':body_cover()}
    beam=reference('chassis_crossmember_121')
    for y in [-24,24]:beam=beam.cut(cyl(2.2,25,(121,y,25),(0,0,1)))
    shapes['chassis_crossmember_121']=beam
    for key,z in [('lidar_base',SEAT_Z),('lidar',SEAT_Z+4),('lidar_lid',SEAT_Z+22)]:
        s=reference(key);bb=s.BoundingBox()
        shapes[key]=s.translate((LIDAR_X-(bb.xmin+bb.xmax)/2,0,z-bb.zmin))
    shapes.update(hardware())
    return shapes

def parameters():
    return {'low_lidar_center_x_mm':LIDAR_X,'low_lidar_seat_z_mm':SEAT_Z,
        'low_lidar_scan_band_z_mm':[SEAT_Z+4,SEAT_Z+22],
        'low_lidar_cable_bore_mm':18,'sensor_hood_screw_centers_xy_mm':SCREWS,
        'sensor_saddle_split_z_mm':60}
