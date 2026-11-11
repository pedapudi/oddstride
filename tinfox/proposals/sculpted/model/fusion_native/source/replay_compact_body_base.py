"""Prove the cover's transverse envelope needs no nose or tail lofts."""
import gzip,json,sys
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1];MODEL=ROOT.parent;sys.path.insert(0,str(MODEL))
import build as b,service_design as sd,rounded_design as rd
from replay_current_body_deltas import low_cover
from audit_part import volume
model=json.loads(gzip.decompress((ROOT/'snapshots/cohesive-limb/model.json.gz').read_bytes()));b.P.update(model['parameters'])
class CapturedCover(Exception):pass
captured={}
original_torso=b.torso;original_add=b.add

def transverse_torso(inset=0):return cq.Solid.extrudeLinear(b.body_section(-132,inset),[],cq.Vector(264,0,0))
def capture(name,shape,*args,**kwargs):
 if name=='body_center_0':captured[name]=shape;raise CapturedCover()
b.torso=transverse_torso;b.add=capture
try:
 try:b.build_body()
 except CapturedCover:pass
finally:b.torso=original_torso;b.add=original_add
assert 'body_center_0' in captured
s=captured['body_center_0']
for front,side in [(1,1),(1,-1),(-1,1),(-1,-1)]:
 for sign in [-1,1]:
  tool=sd.connector_parts(0,sign)[3].rotate((0,0,0),(0,0,1),-90).translate((-67.3,0,0))
  if front<0:tool=tool.mirror('YZ')
  if side<0:tool=tool.mirror('XZ')
  s=s.cut(tool.translate((front*b.P['hip_x'],side*b.P['roll_y'],0)))
s=s.clean();oldsource=rd.source;rd.source=lambda key:s if key=='body_center_0' else oldsource(key)
try:rd.body_shell.cache_clear();rounded=rd.body_shell()
finally:rd.source=oldsource;rd.body_shell.cache_clear()
current=low_cover(rounded);sources=[('constant_section_service_cover',s,MODEL/'output/step-parts/body_center_0.step'),('constant_section_rounded_cover',rounded,MODEL/'output/v0-rounded-body/step/body_center_0.step'),('constant_section_current_cover',current,MODEL/'output/limb-refinement/step/body_center_0.step')];rows=[]
for name,candidate,path in sources:
 reference=cq.importers.importStep(str(path)).val();sv,cv=volume(reference)[0],volume(candidate)[0];errors=[]
 for a,z in [(reference,candidate),(candidate,reference)]:
  vertices,_=a.tessellate(.025,.05);boundary=cq.Compound.makeCompound(z.Faces());errors.extend(boundary.distance(cq.Vertex.makeVertex(*p.toTuple())) for p in vertices[::max(1,len(vertices)//600)])
 row={'stage':name,'valid':candidate.isValid(),'solids':len(candidate.Solids()),'source_volume_mm3':sv,'candidate_volume_mm3':cv,'relative_volume_error':abs(sv-cv)/sv,'maximum_boundary_error_mm':max(errors),'passed':candidate.isValid() and len(candidate.Solids())==1 and abs(sv-cv)/sv<.001 and max(errors)<.05};rows.append(row);print(json.dumps(row),flush=True)
(ROOT/'audits/compact-body-transverse-envelope.json').write_text(json.dumps(rows,indent=2));cq.exporters.export(current,str(ROOT/'snapshots/current-targets/compact-current-cover.step'))
