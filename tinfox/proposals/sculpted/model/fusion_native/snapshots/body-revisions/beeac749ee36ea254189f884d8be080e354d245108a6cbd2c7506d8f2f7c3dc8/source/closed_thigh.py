"""Continuous thigh wall checked against the modeled boot instead of a sphere."""
from functools import cache
import cadquery as cq
import build as b
import cohesive_chassis as chassis
from kinematics import ROOT

BASE=ROOT/'output/cohesive-chassis-work'

@cache
def thigh(outer):return chassis.smooth_thigh(outer,foot_clearance=False)

@cache
def rail(side):
    s=chassis.rail(side)
    # Restore the original open motor window after removing its retired
    # cover-boss roots; no pilot holes or downward tabs survive in the web.
    for x in [-91,91]:
        window=cq.Workplane(obj=b.box(56,6,52,(x,side*102,0))).edges('|Y').fillet(4).val()
        s=s.cut(window)
    for front in [-1,1]:
        for dx in [-3,3]:
            old_hole=b.cyl(1.701,2,(front*121+dx,side*99,32),(0,0,1))
            s=s.fuse(old_hole.intersect(b.torso(3.4)))
        s=s.cut(chassis.crossmember(front))
    s=s.clean();assert s.isValid() and len(s.Solids())==1
    return s
