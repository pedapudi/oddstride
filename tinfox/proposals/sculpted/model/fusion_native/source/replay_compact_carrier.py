"""Verify compact analytic carrier stock against the frozen current design.

This local construction is a native recipe planning aid, never an imported
Fusion body. Preserve operation order where bridge unions can fill prior holes.
"""
import json
import math
import sys
from pathlib import Path

import cadquery as cq

NATIVE = Path(__file__).resolve().parents[1]
MODEL = NATIVE.parent
sys.path[:0] = [str(MODEL)]
from build import box, cyl, ring
import service_design as sd
from audit_part import volume


def shroud():
    profile = [(12,-48.4),(43.5,-48.4),(43.5,-4.4),(44,-4.4),
               (44,-.9),(41.5,-.9),(41.5,-46.4),(12,-46.4)]
    return cq.Workplane('XY').polyline(profile).close().revolve(360,(0,0),(0,1)).val()


def journal():
    # build_leg.handed translates the journal ten millimeters before union.
    # The shifted flange and unshifted bridge disc are contiguous at X=-51.
    profile = [(-67.3,0),(-67.3,24.95),(-54,24.95),(-54,29),
               (-49.5,29),(-49.5,0)]
    return cq.Workplane('XY').polyline(profile).close().revolve(360,(0,0),(1,0)).val()


def carrier(front):
    flange = ring(44,27,3,-3.9)
    for angle in range(0,360,40):
        a=math.radians(angle)
        flange=flange.cut(cyl(1.7,5,(36.5*math.cos(a),-4.9,36.5*math.sin(a))))
    bridge=box(18,28,40,(-49,-11,0),2).cut(box(22,15,23,(-49,-13,0),4))
    # The stepped journal combines the pilot, thrust flange and bridge disc.
    hub=journal()
    if front<0:
        bridge=bridge.mirror('YZ');hub=hub.mirror('YZ')
    result=flange.fuse(bridge,hub)
    for angle in range(0,360,60):
        a=math.radians(angle)
        result=result.cut(cyl(2.2,23,(-front*68,12*math.cos(a),12*math.sin(a)),(front,0,0)))
    result=result.cut(cyl(7,23,(-front*68,0,0),(front,0,0)))
    enclosure=shroud().cut(box(20,54,46,(-front*45,-24,0),2))
    result=result.fuse(enclosure,tol=1e-5).clean()
    result=sd.hip_port_cut(result)
    result=result.cut(box(12,6,44,(-front*45,4,0),1)).clean()
    return result


def main():
    rows=[]
    for front in [1,-1]:
        key='motor_carrier_'+str(front)
        src=NATIVE/'snapshots/cohesive-limb/step'/f'{key}.step'
        source=cq.importers.importStep(str(src)).val();candidate=carrier(front)
        sv,nv=volume(source)[0],volume(candidate)[0]
        differences=[]
        for a,b in [(source,candidate),(candidate,source)]:
            vertices,_=a.tessellate(.025,.05)
            boundary=cq.Compound.makeCompound(b.Faces())
            # Uniform deterministic coverage, including all BRep vertices.
            stride=max(1,len(vertices)//600)
            points=[v.toTuple() for v in vertices[::stride]]+[v.toTuple() for v in a.Vertices()]
            differences.extend(boundary.distance(cq.Vertex.makeVertex(*p)) for p in points)
        record={'key':key,'source_volume_mm3':sv,'candidate_volume_mm3':nv,
                'relative_volume_error':abs(sv-nv)/sv,'boundary_samples':len(differences),
                'maximum_boundary_error_mm':max(differences),'valid':candidate.isValid(),
                'solid_count':len(candidate.Solids()),'passed':abs(sv-nv)/sv<1e-6 and max(differences)<.001}
        rows.append(record);print(json.dumps(record),flush=True)
    (NATIVE/'audits/compact-carrier-local-replay.json').write_text(json.dumps(rows,indent=2))


if __name__=='__main__':main()
