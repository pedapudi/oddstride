"""Open washer seats give shell clamps a defined plastic bearing footprint."""
from functools import cache
import cadquery as cq
import build as b
import cohesive_chassis as chassis
import slim_limb as limb
from kinematics import ROOT

BASE=ROOT/'output/closed-thigh-work'
REAR_FLARE_MM=3.5
WASHER_OD=12.0
WASHER_ID=4.3
WASHER_THICKNESS=1.0
ACCESS_RADIUS=6.2

@cache
def source(key):
    for folder in [BASE/'step',ROOT/'output/limb-refinement/step',ROOT/'output/integrated-candidate/step',ROOT/'output/service-design/step',ROOT/'output/step-parts']:
        file=folder/(key+'.step')
        if file.exists():return cq.importers.importStep(str(file)).val()
    raise FileNotFoundError(key)

def seats(s,outer,centers):
    for x,z in centers:
        # Both counterbores are open to their accessible outer face. There
        # is no narrower entry trapping a washer beneath a nut pocket.
        s=s.cut(b.cyl(ACCESS_RADIUS,40 if outer else 15,(x,76 if outer else 43,z)))
    s=s.clean();assert s.isValid() and len(s.Solids())==1
    return s

@cache
def thigh(outer):
    s=chassis.smooth_thigh(outer,foot_clearance=False,rear_flare_mm=REAR_FLARE_MM)
    return seats(s,outer,[limb.REAR_CLAMP,limb.FRONT_CLAMP])

@cache
def shin(outer):
    return seats(source('shin_outer' if outer else 'shin_inner'),outer,[(2,-30),(2,-105)])

def washer(center,outer):
    x,z=center
    return b.ring(WASHER_OD/2,WASHER_ID/2,WASHER_THICKNESS,76 if outer else 57,z,x)

def shifted_hardware(key):
    delta=-1 if key.startswith('bolt_') or 'clamp_bolt_' in key else 1
    return source(key).translate((0,delta,0))
