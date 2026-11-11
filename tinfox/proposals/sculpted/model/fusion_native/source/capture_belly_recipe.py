"""Capture the lower center shell without constructing discarded end sections."""
import json
from pathlib import Path
import cadquery as cq
import capture as cap
import build as b
import service_design as sd
from capture_cover_delta import center,compare
ROOT=Path(__file__).resolve().parents[1]
def belly():
 outer=center();s=outer.cut(center(b.P['body_skin']))
 for front in [-1,1]:
  for side in [-1,1]:
   s=s.cut(b.cyl(41.25,49.4,(front*70.3,side*68,0),(front,0,0)))
   s=s.cut(b.cyl(42,7,(front*111.7,side*68,0),(front,0,0)))
   s=s.cut(b.cyl(38,20,(front*113.5,side*68,0),(front,0,0)))
   for z in [-12,24]:s=s.cut(b.box(14,16,14,(front*125.5,side*94.5,z)))
 for y in [-102,102]:s=s.cut(b.box(268,3,55,(0,y,8),.8))
 s=s.cut(b.box(148,202,70,(0,0,-55),8))
 # Shoulder sweeps start at |X|=126.5 mm, beyond this ±125.4 mm part.
 # Window, lid ribs and return patches are outside the lower shell's Z range.
 s=s.intersect(b.box(250.8,240,140,(0,0,0))).intersect(b.box(270,250,38,(0,0,-29.3)))
 for front,side in sd.LEGS.values():
  for sign in [-1,1]:
   cut=sd.connector_parts(0,sign)[3].rotate((0,0,0),(0,0,1),-90).translate((-67.3,0,0))
   if front<0:cut=cut.mirror('YZ')
   if side<0:cut=cut.mirror('XZ')
   s=s.cut(cut.translate((front*b.P['hip_x'],side*b.P['roll_y'],0)))
 return s.clean()
shape=belly();reference=cq.importers.importStep(str(ROOT/'snapshots/step/belly_center_0.step')).val();evidence=compare(reference,shape)
root=cap.ref(shape);bb=shape.BoundingBox();record={'root':root,'volume_mm3':shape.Volume(),'bounds_mm':{k:getattr(bb,k) for k in ['xmin','xmax','ymin','ymax','zmin','zmax']}}
folder=ROOT/'snapshots/reconstructed/belly_center_0';folder.mkdir(parents=True,exist_ok=True)
(folder/'recipe.json').write_text(json.dumps({'schema':1,'nodes':cap.NODES,'parts':{'belly_center_0':record}},indent=2));(folder/'reconstruction-audit.json').write_text(json.dumps(evidence,indent=2));print(evidence,flush=True)
