"""Verify the low-profile cover changes as a short native feature plan.

The baseline is the qualified rounded cover. Reference STEP loading occurs only
in this independent comparison, never inside Fusion's authoring path.
"""
import json
import sys
from pathlib import Path
import cadquery as cq

NATIVE=Path(__file__).resolve().parents[1]
MODEL=NATIVE.parent
sys.path.insert(0,str(MODEL))
from build import box,cyl
from audit_part import volume


def low_cover(base):
    s=base.cut(box(18,204,18,(122,0,44))).cut(box(24,62,70,(138,0,60)))
    # The former cradle relief detaches four lip remnants in the source.
    s=max(s.Solids(),key=lambda a:volume(a)[0])
    opening=cq.Workplane('XY',origin=(149,0,-70)).rect(150,92).val()
    opening=opening.fillet2D(8,opening.Vertices())
    tool=cq.Solid.extrudeLinear(opening,[],cq.Vector(0,0,200))
    s=s.cut(cyl(35,15,(82,0,45),(0,0,1)))
    s=s.fuse(cyl(36,3,(82,0,52.5),(0,0,1))).cut(tool)
    for side in [-1,1]:
        s=s.cut(box(264,15,100,(0,side*99.5,-14.5)))
        s=s.cut(box(14,206,100,(side*121,0,-6.7)))
    return s.clean()


def main():
    source=cq.importers.importStep(str(MODEL/'output/limb-refinement/step/body_center_0.step')).val()
    base=cq.importers.importStep(str(MODEL/'output/v0-rounded-body/step/body_center_0.step')).val()
    native_base=cq.importers.importStep(str(NATIVE/'exports/body_center_0.step')).val()
    rows=[]
    for label,shape in [('source_baseline',base),('native_baseline',native_base)]:
        candidate=low_cover(shape);sv,nv=volume(source)[0],volume(candidate)[0];errors=[]
        for a,b in [(source,candidate),(candidate,source)]:
            vertices,_=a.tessellate(.025,.05);boundary=cq.Compound.makeCompound(b.Faces());stride=max(1,len(vertices)//600)
            errors.extend(boundary.distance(cq.Vertex.makeVertex(*p.toTuple())) for p in vertices[::stride])
        row={'baseline':label,'source_volume_mm3':sv,'candidate_volume_mm3':nv,
             'relative_volume_error':abs(sv-nv)/sv,'maximum_boundary_error_mm':max(errors),
             'valid':candidate.isValid(),'solids':len(candidate.Solids()),
             'passed':abs(sv-nv)/sv<.001 and max(errors)<.05}
        rows.append(row);print(json.dumps(row),flush=True)
    (NATIVE/'audits/current-low-cover-delta-replay.json').write_text(json.dumps(rows,indent=2))


if __name__=='__main__':main()
