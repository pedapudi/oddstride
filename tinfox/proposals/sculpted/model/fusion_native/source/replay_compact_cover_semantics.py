"""Check compact cover construction and identify empty boolean operations."""
import sys,json,math
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
import build as b,rounded_design as rd
from replay_current_body_deltas import low_cover
from audit_part import volume
ops=[]
def four(s):return [s,s.mirror('XZ'),s.mirror('YZ'),s.mirror('XZ').mirror('YZ')]
def cut(s,tools,name):
 out=s.cut(*tools).clean();change=abs(volume(s)[0]-volume(out)[0]);ops.append({'name':name,'change_mm3':change});return out
def join(s,tools,name):
 out=s.fuse(*tools).clean();ops.append({'name':name,'change_mm3':abs(volume(s)[0]-volume(out)[0])});return out
outer=cq.Solid.extrudeLinear(b.body_section(-125.4),[],cq.Vector(250.8,0,0));inner=cq.Solid.extrudeLinear(b.body_section(-126.4,2.8),[],cq.Vector(252.8,0,0));body=outer.cut(inner).intersect(b.box(270,250,200,(0,0,90)))
rib=b.box(2.4,170,5.5,(28,0,46.75));body=join(body,[rib,rib.mirror('YZ')],'Integral roof ribs')
tool=b.cyl(41.25,49.4,(70.3,68,0),(1,0,0)).fuse(b.cyl(42,7,(111.7,68,0),(1,0,0)),b.cyl(38,20,(113.5,68,0),(1,0,0)))
body=cut(body,four(tool),'Four fixed motor clearances')
for z,label in [(-12,'Lower'),(24,'Upper')]:body=cut(body,four(b.box(14,16,14,(125.5,94.5,z))),'Four '+label.lower()+' mounting ear clearances')
tool=b.box(268,3,55,(0,102,8),.8);body=cut(body,[tool,tool.mirror('XZ')],'Separate shell from frame rails')
body=join(body,four(b.box(9,7.5,14,(112,106.25,22),.5)),'Four integral mounting bosses')
body=cut(body,four(b.box(9.4,5.4,80,(112,103.5,-13.3),.3)),'Four downward-open boss channels')
body=cut(body,four(b.box(10,4,100,(112,101.5,-5))),'Open inner mounting channels')
body=cut(body,four(b.cyl(1.7,12,(112,101,22),(0,1,0))),'Four accessible M3 cover holes')
body=cut(body,four(b.cyl(42,7,(111.7,68,0),(1,0,0))),'Keep mounting bosses clear of cartridges')
tool=b.box(32,260,100,(125.4,0,-35.8),2);body=cut(body,[tool,tool.mirror('YZ')],'Open lower end service paths')
sections=[(46.8,249.5,201,19),(50,246,195,23),(54,230,174,32),(55.5,212,145,36)];outerw=[];innerw=[]
for z,w,d,r in sections:
 q=cq.Workplane('XY',origin=(0,0,z)).rect(w,d).val();outerw.append(q.fillet2D(r,q.Vertices()));q=cq.Workplane('XY',origin=(0,0,z-3)).rect(w-6,d-6).val();innerw.append(q.fillet2D(r-3,q.Vertices()))
dome=cq.Solid.makeLoft(outerw).cut(cq.Solid.makeLoft(innerw));body=join(body,[dome],'Continuous raised roof')
core=cq.Workplane('XY',origin=(0,0,45.8)).rect(207,139).extrude(4).edges('|Z').fillet(32).val();body=cut(body,[core],'Single roof wall');body=cut(body,[b.box(50,30,20,(20,0,55),4)],'Rounded display opening')
profile=[(118.8,48),(128,48),(132,43),(135,40.5),(135,37.5),(132,37.5),(128,42.5),(118.8,42.5)]
cuff=cq.Workplane('XY').polyline([(x,68+r) for x,r in profile]).close().revolve(180,(0,68),(1,68)).val();root=b.box(9,32,5,(121,68,46.5),1);body=join(body,four(cuff)+four(root),'Four integral upper shoulder cuffs')
tool=b.box(14,184,4.6,(121,0,41.8));body=cut(body,[tool,tool.mirror('YZ')],'Crossmember to cuff clearance')
for z,label in [(-12,'Lower'),(24,'Upper')]:body=cut(body,four(b.box(14,16,14,(125.5,94.5,z),.8)),'Rounded '+label.lower()+' cuff mounting clearances')
tool=b.cyl(67,400,(185,-200,0),(0,1,0));body=cut(body,[tool,tool.mirror('YZ')],'Pitch freedom below the shoulders');body=low_cover(body)
reference=cq.importers.importStep(str(ROOT.parent/'output/limb-refinement/step/body_center_0.step')).val();a,bv=volume(body)[0],volume(reference)[0];errors=[]
for left,right in [(body,reference),(reference,body)]:
 pts,_=left.tessellate(.025,.05);boundary=cq.Compound.makeCompound(right.Faces());errors +=[boundary.distance(cq.Vertex.makeVertex(*p.toTuple())) for p in pts[::max(1,len(pts)//500)]]
record={'valid':body.isValid(),'solids':len(body.Solids()),'volume_mm3':a,'source_volume_mm3':bv,'relative_volume_error':abs(a-bv)/bv,'maximum_boundary_error_mm':max(errors),'operations':ops};record['passed']=record['valid'] and record['solids']==1 and record['relative_volume_error']<.001 and max(errors)<.05
(ROOT/'audits/compact-current-cover-semantic-replay.json').write_text(json.dumps(record,indent=2));print(json.dumps(record));cq.exporters.export(body,str(ROOT/'snapshots/current-targets/compact-current-cover-semantic.step'))
