"""Capture the authorized rounded V0 cover without importing its source solid.

The old cover is reconstructed from the original native construction operations.
Only the torso's central extrusion is needed inside the cover's ±125.4 mm split.
The source STEP files are read solely to validate the reconstruction.
"""
import json,math,gzip,hashlib,shutil
from pathlib import Path
import numpy as np
import cadquery as cq
from scipy.spatial import ConvexHull
import capture as cap
import build as b
import service_design as sd
ROOT=Path(__file__).resolve().parents[1];MODEL=ROOT.parent

def center(inset=0):return cq.Solid.extrudeLinear(b.body_section(-132,inset),[],cq.Vector(264,0,0))
def original_cover():
 outer=center();inner=center(b.P['body_skin']);shell=outer.cut(inner)
 mask=cq.Workplane(obj=b.box(48,28,20,(20,0,48))).edges('|Z').fillet(4).val()
 shell=shell.cut(outer.cut(center(.6)).intersect(mask))
 for x in [-28,28]:shell=shell.fuse(b.box(2.4,170,6,(x,0,47)).intersect(outer))
 for front in [-1,1]:
  for side in [-1,1]:
   shell=shell.cut(b.cyl(41.25,49.4,(front*70.3,side*68,0),(front,0,0)))
   shell=shell.cut(b.cyl(42,7,(front*111.7,side*68,0),(front,0,0)))
   shell=shell.cut(b.cyl(38,20,(front*113.5,side*68,0),(front,0,0)))
   for z in [-12,24]:shell=shell.cut(b.box(14,16,14,(front*125.5,side*94.5,z)))
 for y in [-102,102]:shell=shell.cut(b.box(268,3,55,(0,y,8),.8))
 shell=shell.cut(b.box(148,202,70,(0,0,-55),8))
 samples=[]
 for angle in np.deg2rad(np.arange(-61,62)):
  for yy,zz in [(-51,-55),(-51,55),(111,-55),(111,55)]:samples.append([yy*np.cos(angle)-zz*np.sin(angle),yy*np.sin(angle)+zz*np.cos(angle)])
 points=np.array(samples);hull=points[ConvexHull(points).vertices].tolist()
 blank=cq.Workplane(cq.Plane(origin=(-58.5,0,0),xDir=(0,1,0),normal=(1,0,0))).polyline(hull).close().wires().toPending().offset2D(2,kind='arc').extrude(117).val()
 for front in [-1,1]:
  for side in [-1,1]:
   cut=blank if side>0 else blank.mirror('XZ');cut=cut.translate((front*b.P['hip_x'],side*b.P['roll_y'],0))
   if front>0:cut=cut.intersect(b.box(500,500,500,(-9,0,0)))
   shell=shell.cut(cut)
 # All end-cap cuts and return patches are outside this central split.
 lid=shell.intersect(b.box(250.8,240,140,(0,0,0))).intersect(b.box(270,250,80,(0,0,30)))
 for side in [-1,1]:
  for x in [-112,112]:
   boss=b.box(9,7.5,14,(x,side*106.25,22),.5).intersect(outer)
   lid=lid.fuse(boss).cut(b.box(9.4,5.4,80,(x,side*103.5,-13.3),.3)).cut(b.box(10,4,100,(x,side*101.5,-5))).cut(b.cyl(1.7,12,(x,side*101,22),(0,side,0)))
 for front in [-1,1]:
  for side in [-1,1]:lid=lid.cut(b.cyl(42,7,(front*111.7,side*68,0),(front,0,0)))
 for front in [-1,1]:lid=lid.cut(b.box(32,260,100,(front*125.4,0,-35.8),2))
 for front,side in sd.LEGS.values():
  for sign in [-1,1]:
   cut=sd.connector_parts(0,sign)[3].rotate((0,0,0),(0,0,1),-90).translate((-67.3,0,0))
   if front<0:cut=cut.mirror('YZ')
   if side<0:cut=cut.mirror('XZ')
   lid=lid.cut(cut.translate((front*b.P['hip_x'],side*b.P['roll_y'],0)))
 return lid.clean()

def compare(source,reconstructed):
 from OCP.BRepGProp import BRepGProp
 from OCP.GProp import GProp_GProps
 def volume(s):
  props=GProp_GProps();BRepGProp.VolumeProperties_s(s.wrapped,props,1e-9,True,False);return props.Mass()
 volumes=[volume(s) for s in [source,reconstructed]];errors=[]
 for a,bshape in [(source,reconstructed),(reconstructed,source)]:
  vertices,_=a.tessellate(.04,.08);indices=np.random.default_rng(7).choice(len(vertices),min(600,len(vertices)),replace=False)
  errors.extend(bshape.distance(cq.Vertex.makeVertex(*vertices[i].toTuple())) for i in indices)
 result={'source_volume_mm3':volumes[0],'reconstructed_volume_mm3':volumes[1],'relative_volume_error':abs(volumes[0]-volumes[1])/volumes[0],'sampled_surface_max_mm':max(errors)}
 assert result['relative_volume_error']<.0001 and result['sampled_surface_max_mm']<.001,result
 return result

def main():
 source_dir=MODEL/'output/v0-rounded-body';model_bytes=(source_dir/'model.json').read_bytes();stamp=hashlib.sha256(model_bytes).hexdigest()
 assert stamp=='3f384f8cace91b1b5154eea61771b4c69d207e6d3fdab714ed475639b0cd8ce5'
 delta=ROOT/'snapshots/deltas'/stamp;delta.mkdir(parents=True,exist_ok=True)
 old=original_cover();baseline=cq.importers.importStep(str(ROOT/'snapshots/step/body_center_0.step')).val();old_check=compare(baseline,old)
 import rounded_design as rounded
 rounded.source=lambda key:old if key=='body_center_0' else (_ for _ in ()).throw(ValueError('Unexpected source solid '+key))
 new=rounded.body_shell();reference=cq.importers.importStep(str(source_dir/'step/body_center_0.step')).val();new_check=compare(reference,new)
 root=cap.ref(new);bb=new.BoundingBox();record={'root':root,'volume_mm3':new.Volume(),'bounds_mm':{k:getattr(bb,k) for k in ['xmin','xmax','ymin','ymax','zmin','zmax']}}
 (delta/'recipe.json').write_text(json.dumps({'schema':1,'nodes':cap.NODES,'parts':{'body_center_0':record}},indent=2))
 shutil.copyfile(source_dir/'step/body_center_0.step',delta/'body_center_0.step');shutil.copyfile(MODEL/'rounded_design.py',delta/'rounded_design.py')
 (delta/'model.json.gz').write_bytes(gzip.compress(model_bytes,compresslevel=6))
 report={'model_sha256':stamp,'changed_custom_parts':['body_center_0'],'baseline_cover_reconstruction':old_check,'rounded_cover_reconstruction':new_check,'source_limitations':['Fixed frame/hardware contacts remain unresolved in the authorized source cover. Seven named limb poses passed the source screen; this does not qualify assembly fit.'],'native_recipe':'snapshots/deltas/'+stamp+'/recipe.json'}
 (delta/'capture-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
