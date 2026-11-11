"""Prove a constant-section native rail recipe against the frozen frame."""
import json,sys
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT.parent)]
from build import box,cyl,body_section
from audit_part import volume

def rail():
 y=102
 body=box(260,2,54,(0,y,8),.7)
 windows=[cq.Workplane(obj=box(56,6,52,(x,y,0))).edges('|Y').fillet(4).val() for x in [-91,91]]
 windows.append(cq.Workplane(obj=box(80,6,28,(0,y,5))).edges('|Y').fillet(6).val())
 for tool in windows:body=body.cut(tool)
 flange=box(260,8,2,(0,99,33),.5).cut(box(138,20,6,(0,99,33)))
 flange=flange.fuse(box(138,6,2,(0,105,33),.5));body=body.fuse(flange)
 pads=[cyl(5.5,5,(x,101,z),(0,1,0)) for x in [-125.5,125.5] for z in [-12,24]]
 body=body.fuse(*pads)
 for x in [-125.5,125.5]:
  for z in [-12,24]:body=body.cut(cyl(1.7,9,(x,99,z),(0,1,0)))
 bosses=[box(9,5,9,(x,103.5,22),.5) for x in [-112,112]];body=body.fuse(*bosses)
 for x in [-112,112]:body=body.cut(cyl(1.25,9,(x,100,22),(0,1,0)))
 for x in [-52,52]:body=body.cut(cyl(1.7,8,(x,99,-6),(0,1,0)))
 for x in [-124,-118,118,124]:body=body.cut(cyl(1.7,8,(x,99,29),(0,0,1)))
 for front in [-1,1]:body=body.cut(cyl(40.75,49.4,(front*70.3,68,0),(front,0,0)))
 ledges=[box(12,10,4,(x,98,-1.5),.4).cut(box(13,11.3,17,(52 if x>0 else -52,94.15,-8))) for x in [-63,63]];body=body.fuse(*ledges)
 for x in [-63,63]:body=body.cut(cyl(1.25,7,(x,97,-4),(0,0,1)))
 # The shared transverse section is the constant central section, not the raised shoulder.
 envelope=cq.Solid.extrudeLinear(body_section(0,3.4).translate((-185,0,0)),[],cq.Vector(370,0,0))
 return body.intersect(envelope).clean()

def main():
 target=json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low'];targets={p['key']:p for p in target['custom_parts']};base=rail();rows=[]
 for side in [1,-1]:
  key='chassis_beam_'+str(side*102);source=cq.importers.importStep(str(ROOT/targets[key]['files']['step']['path'])).val();candidate=base if side==1 else base.mirror('XZ');sv=volume(source)[0];nv=volume(candidate)[0];errors=[]
  for a,b in [(source,candidate),(candidate,source)]:
   vertices,_=a.tessellate(.025,.05);boundary=cq.Compound.makeCompound(b.Faces());points=[v.toTuple() for v in vertices[::max(1,len(vertices)//500)]]+[v.toTuple() for v in a.Vertices()];errors.extend(boundary.distance(cq.Vertex.makeVertex(*p)) for p in points)
  row={'key':key,'source_volume_mm3':sv,'candidate_volume_mm3':nv,'relative_volume_error':abs(sv-nv)/sv,'maximum_boundary_error_mm':max(errors),'boundary_samples':len(errors),'valid':candidate.isValid(),'solid_count':len(candidate.Solids()),'passed':abs(sv-nv)/sv<1e-6 and max(errors)<.001};rows.append(row);print(row,flush=True)
 (ROOT/'audits/frame-rail-intent-local-replay.json').write_text(json.dumps({'parts':rows,'passed':all(row['passed'] for row in rows)},indent=2))
if __name__=='__main__':main()
