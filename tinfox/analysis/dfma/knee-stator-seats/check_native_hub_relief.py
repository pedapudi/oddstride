"""Read-only actual native hub/case clearance and preserved tube-land audit."""
from pathlib import Path
import hashlib,json,math,sys
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
H=Path(__file__).resolve().parent;R=H.parents[2]/'proposals/sculpted/model';N=R/'fusion_native'
sys.path.insert(0,str(R));import build as b
base=cq.importers.importStep(str(H/'hub-case-input/hub.step')).val()
motor=cq.importers.importStep(str(H/'hub-case-input/motor.step')).val()
expected=base.cut(b.cyl(39.75,1,(0,8.75,0)))
def volume(shape):
 p=GProp_GProps();BRepGProp.VolumePropertiesGK_s(shape.wrapped,p,1e-11,True,True);return p.Mass()
specs={'left':('case-relieved-native-hip_hub.step','71782a60f159e538f4920f20e89bc28ecec2bb14ac35695f09882a707627f3cb'),'right':('case-relieved-native-hip_hub_right.step','e16a048bbd270b05e37c40b6fcdb63903d1612e111d5e9d64cc383550a82beb0')}
rows=[]
for hand,(name,digest) in specs.items():
 src=N/'exports'/name;raw=src.read_bytes();assert hashlib.sha256(raw).hexdigest()==digest
 dst=H/'hub-case-input'/name;dst.write_bytes(raw);hub=cq.importers.importStep(str(dst)).val()
 exp=expected if hand=='left' else expected.mirror('XZ');m=motor if hand=='left' else motor.mirror('XZ')
 gap=hub.distance(m);hit=max(0,hub.intersect(m).Volume());lands=[]
 for angle in (90,210,330):
  x,z=43.5*math.cos(math.radians(angle)),43.5*math.sin(math.radians(angle));tube=b.ring(2.5,1.7,.02,9.48,z,x)
  if hand=='right':tube=tube.mirror('XZ')
  footprint=hub.intersect(tube).Volume()/.02;target=math.pi*(2.5**2-1.7**2)
  lands.append(dict(tie_deg=angle,supported_area_mm2=footprint,expected_area_mm2=target,passed=abs(footprint-target)<1e-5))
 errors=[]
 for a,c in [(hub,exp),(exp,hub)]:
  points,_=a.tessellate(.02,.06);target=cq.Compound.makeCompound(c.Faces());step=max(1,len(points)//500)
  errors.append(max(target.distance(cq.Vertex.makeVertex(*v.toTuple())) for v in points[::step]))
 hv,ev=volume(hub),volume(exp)
 row=dict(hand=hand,input_path=str(src),frozen_path=str(dst),sha256=digest,valid=hub.isValid(),solids=len(hub.Solids()),native_volume_mm3=hv,expected_volume_mm3=ev,absolute_volume_difference_mm3=abs(hv-ev),sampled_boundary_difference_max_mm=max(errors),motor_overlap_mm3=hit,minimum_nominal_motor_gap_mm=gap,tube_lands=lands)
 row['passed']=row['valid'] and row['solids']==1 and hit<1e-6 and gap>.24999 and abs(hv-ev)<.002 and max(errors)<.05 and all(l['passed'] for l in lands);rows.append(row)
report=dict(passed=all(r['passed'] for r in rows),rows=rows,original_collision_report=str(H/'hub-case-collision.json'),scope='Actual native hub exports, both hands, compared with frozen original hub and exact shallow case relief.',limitations=['Nominal rigid geometry only. No physical printed fit, preload, deflection, fatigue or operating-strength qualification.','Sampled boundary comparison is finite. Full corrected121-solid assembly screening remains a separate gate.','Hardware vendor seeds and motor planes are unchanged.'])
(H/'native-hub-relief-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
