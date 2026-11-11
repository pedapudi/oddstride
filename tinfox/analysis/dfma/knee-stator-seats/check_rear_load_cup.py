"""Read-only packaging screen of a rear-loaded, integral-front-flange cup."""
from pathlib import Path
import hashlib,json,math,sys
import cadquery as cq
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
H=Path(__file__).resolve().parent;R=H.parents[2]/'proposals/sculpted/model';N=R/'fusion_native'
sys.path.insert(0,str(R));import build as b
authority=json.loads((N/'manifests/motor-complex-native-exports.json').read_text())
def read_part(name):
 rec=authority['parts'][name];p=N/rec['native_step'];assert hashlib.sha256(p.read_bytes()).hexdigest()==rec['native_step_sha256']
 s=cq.importers.importStep(str(p)).val()
 return s.translate(tuple(rec.get('assembly_translation_mm',[0,0,0])))
def common(a,c):
 s=a._bool_op((a,),(c,),BRepAlgoAPI_Common(),parallel=False)
 return dict(valid=s.isValid(),overlap_mm3=max(0,sum(x.Volume()for x in s.Solids())))
cup=read_part('motor_carrier_1');closure=read_part('hip_stator_closure_1')
rear_open=cup.cut(b.cyl(40.75,40,(0,-80,0)))
fixed={'rear-open cup':rear_open,'integral-front-flange reference':closure}
for name in ['roll_cartridge_1','roll_stator_backplate_1','roll_outer_retainer_1','roll_inner_backplate_1','roll_inner_spacer_1','roll_outer_spacer_1']:fixed[name]=read_part(name)
manifest=json.loads((N/'manifests/motor-complex-hardware.json').read_text());path=N/manifest['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==manifest['sha256']
shapes=cq.importers.importStep(str(path)).val().Solids()
def bounds(s):
 q=s.BoundingBox();return[q.xmin,q.ymin,q.zmin,q.xmax,q.ymax,q.zmax]
def ref(name):
 rec=next(p for p in manifest['parts']if p['name']==name);found=[s for s in shapes if max(abs(a-c)for a,c in zip(bounds(s),rec['bounds_mm']))<1e-6];assert len(found)==1;return found[0]
motor=cq.Compound.makeCompound([ref('Hip pitch motor'),ref('FL_hip_port_-1_socket'),ref('FL_hip_port_1_socket')])
fixed['roll motor']=ref('Roll motor')
for a in range(0,360,60):fixed['coupling screw'+str(a)]=ref('FL_roll_output_bolt_'+str(a)).translate((-.2,0,0))
checks=[]
for travel in [-100,-80,-60,-50,-40,-30,-20,-10,-5,-1,0]:
 for name,s in fixed.items():
  result=common(motor.translate((0,travel,0)),s);checks.append(dict(kind='rear_motor_insertion',travel_mm=travel,against=name,**result,passed=result['valid']and result['overlap_mm3']<1e-5))
for a in range(0,360,60):
 y,z=12*math.cos(math.radians(a)),12*math.sin(math.radians(a));tool=b.cyl(1.6,150,(-57.5,y,z),(1,0,0))
 for name,s in {'rear-open cup':rear_open,'integral-front-flange reference':closure}.items():
  result=common(tool,s);checks.append(dict(kind='coupling_straight_driver',angle_deg=a,against=name,tool_diameter_mm=3.2,**result,passed=result['valid']and result['overlap_mm3']<1e-5))
out=dict(passed=all(c['passed']for c in checks),status='analysis_packaging_proposal_not_native_revision',current_authority_sha256=hashlib.sha256((N/'manifests/motor-complex-native-exports.json').read_bytes()).hexdigest(),hardware_reference_sha256=manifest['sha256'],proposal='Replace the rear cup wall with a coaxial81.5mm open mouth. Make the existing stator-face geometry integral; omit its separate fastening lugs/closure screws in the future native revision.',checks=checks,scope='Detached module packaging; unconnected hip motor plus its two fixed socket references, existing roll support and six seated roll-output screws. No plug/boot/cable attached to the insertion body.',limits=['Eleven sampled axial positions do not establish a complete continuous swept-solid proof.','Chassis, equipment and body shell are absent. Rearward service likely requires removing the complete module from the chassis first.','Future one-piece structural continuity, contact stresses, stiffness, CNC access, printed strength and exact new feature topology require native authoring and review.','Two current source solids represent the future integral cup for this clearance screen; no custom geometry export or source-authority change was made.'])
(H/'rear-loaded-cup-packaging-proposal.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(passed=out['passed'],checks=len(checks),failures=[c for c in checks if not c['passed']]),indent=2))
