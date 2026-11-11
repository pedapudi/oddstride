"""Two printable orthogonal motor supports joined at a broad keyed face."""
import math
import cadquery as cq
from build import box,cyl,ring,hex_nut

def split_carrier(source,front):
    shroud=ring(43.5,41.5,44.4,-48.4).fuse(ring(43.5,12,2,-48.4),ring(44,41.5,3.5,-4.4))
    shroud=shroud.cut(box(20,54,46,(-front*45,-24,0),2))
    old_flange=ring(44,27,3,-3.9)
    flange=ring(44,27,5,-3.9)
    for a in range(0,360,40):
        x,z=36.5*math.cos(math.radians(a)),36.5*math.sin(math.radians(a))
        flange=flange.cut(cyl(1.7,8,(x,-5,z)))
        old_flange=old_flange.cut(cyl(1.7,8,(x,-5,z)))
    tab=box(10,5,44,(-front*44,-1.4,0),1.5)
    tongue=box(8,3.2,16,(-front*44,-5.4,0),.8)
    flange=flange.fuse(shroud,tab,tongue,tol=1e-5).clean().fix()
    support=box(10,8,44,(-front*44,-8.1,0),1.5)
    support=support.cut(cyl(40.75,12,(0,-15,0)))
    trunnion=source.cut(shroud).cut(old_flange)
    # Clear the mating face without thinning the roll-output journal or end plate.
    trunnion=trunnion.cut(box(11,16,52,(-front*43.5,3.9,0)))
    trunnion=trunnion.fuse(support,tol=1e-5)
    trunnion=trunnion.cut(box(8.4,3.6,16.4,(-front*44,-5.4,0),.8))
    hardware=[]
    for z in [-14,14]:
        x=-front*44
        flange=flange.cut(cyl(2.2,18,(x,-14,z)))
        trunnion=trunnion.cut(cyl(2.2,24,(x,-20,z)))
        trunnion=trunnion.cut(hex_nut(7.2,3.4,x,-12.2,z,.01))
        screw=cyl(2,16,(x,-14.9,z)).fuse(cyl(3.8,2.2,(x,1.1,z)))
        nut=hex_nut(7,3.2,x,-12.1,z,2)
        hardware.extend([(f'carrier_screw_{z}',screw),(f'carrier_nut_{z}',nut)])
    trunnion=trunnion.clean().fix();flange=flange.clean().fix()
    for name,s in [('trunnion',trunnion),('flange',flange)]:
        assert s.isValid() and len(s.Solids())==1,(front,name,s.isValid(),len(s.Solids()))
    overlap=max(0,trunnion.intersect(flange).Volume());assert overlap<1e-4,(front,overlap)
    for name,part in hardware:
        for label,support in [('trunnion',trunnion),('flange',flange)]:
            volume=max(0,part.intersect(support).Volume())
            assert volume<1e-4,(front,name,label,volume)
    return {'trunnion':trunnion,'flange':flange},hardware
