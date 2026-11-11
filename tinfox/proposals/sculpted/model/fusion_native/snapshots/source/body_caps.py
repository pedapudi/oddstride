"""Chassis-mounted end bridges with deep shoulder sockets and no lower ribbons."""
import cadquery as cq
import numpy as np
from scipy.spatial import ConvexHull
from functools import cache
import build as b

@cache
def shoulder_sweep(front,side):
    points=[]
    for a in np.deg2rad(np.arange(-61,62)):
        for yy,zz in [(-51,-55),(-51,55),(111,-55),(111,55)]:
            points.append([yy*np.cos(a)-zz*np.sin(a), yy*np.sin(a)+zz*np.cos(a)])
    points=np.array(points);outline=points[ConvexHull(points).vertices].tolist()
    s=(cq.Workplane(cq.Plane(origin=(-58.5,0,0),xDir=(0,1,0),normal=(1,0,0)))
       .polyline(outline).close().wires().toPending().offset2D(2,kind='arc').extrude(117).val())
    if side<0:s=s.mirror('XZ')
    s=s.translate((front*b.P['hip_x'],side*b.P['roll_y'],0))
    if front>0:s=s.intersect(b.box(500,500,500,(-9,0,0)))
    return s

def end_cap(original,front=True):
    sign=1 if front else -1
    outer=b.torso()
    end_start=241 if front else 224
    end_region=b.box(70,280,150,(sign*(end_start+35),0,0))
    lap_region=b.box(26,50,20,(sign*127,0,45))
    old=original.intersect(end_region).fuse(original.intersect(lap_region))
    end=outer.cut(b.torso(4.2)).intersect(end_region)
    # A deep bridge rises locally above the shoulders. Its underside is carved
    # by the conservative roll sweep, leaving a central keel and rounded sockets.
    wires=[]
    for x,w,h,zc in [(126,48,10,44),(142,44,30,49),(165,44,38,49),(195,44,38,49),(220,44,32,47),(242 if front else 230,80,12,43)]:
        q=cq.Workplane('YZ',origin=(x,0,zc)).rect(w,h).val()
        wires.append(q.fillet2D(2,q.Vertices()))
    bridge=cq.Solid.makeLoft(wires,ruled=not front)
    if not front:bridge=bridge.mirror('YZ')
    bridge=bridge.cut(b.box(20,100,100,(sign*118,0,-7.2)))
    s=old.fuse(end,bridge)
    chin=b.box(12,220,12,(sign*(end_start+6),0,-39)).intersect(outer)
    s=s.fuse(chin)
    # Apply sockets to the bridge and end frame together, preserving hip roll.
    for side in [-1,1]:s=s.cut(shoulder_sweep(sign,side))
    if not front:
        # The rear needs no camera surround. End the bumper above the sockets
        # instead of retaining a detached lower ribbon inside the leg sweep.
        s=s.intersect(b.box(300,280,100,(-200,0,82)))
    if front:
        aperture=(cq.Workplane('YZ',origin=(226,0,4)).rect(168,44)
                  .extrude(36).edges('|X').fillet(8).val())
        s=s.cut(aperture)
    for yy in [-18,18]:
        s=s.cut(b.cyl(1.7,16,(sign*121,yy,35),(0,0,1)))
        s=s.cut(cq.Solid.makeCone(1.7,3,1.3,cq.Vector(sign*121,yy,45),cq.Vector(0,0,1)))
    if front:
        for yy in [-89,89]:
            for zz in [-27,27]:s=s.cut(b.cyl(1.25,30,(238.5,yy,zz),(1,0,0)))
    if front:
        fascia=cq.importers.importStep(str(b.OUT/'step-parts/front_fascia.step')).val()
        s=s.cut(fascia).cut(fascia.translate((-.35,0,0)))
    s=s.clean()
    if not s.isValid():s=s.fix()
    assert s.isValid() and len(s.Solids())==1,('end cap',front,len(s.Solids()))
    return s
