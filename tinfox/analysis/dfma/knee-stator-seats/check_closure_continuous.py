"""Continuous axial clearance proof and independent local web measurements."""
from pathlib import Path
import contextlib,hashlib,io,json,math,sys
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
with contextlib.redirect_stdout(io.StringIO()):import check_closure_recess as p
b=p.b;R=p.R;N=p.N
def read(name):return cq.importers.importStep(str(N/'exports'/name)).val().translate((-5,0,0))
def vol(s):return max(0,sum(v.Volume() for v in s.Solids()))
hardware_manifest_path=N/'manifests/motor-complex-hardware.json'
hardware_manifest=json.loads(hardware_manifest_path.read_text())
hardware_path=N/hardware_manifest['path']
assert hashlib.sha256(hardware_path.read_bytes()).hexdigest()==hardware_manifest['sha256']
hardware_solids=cq.importers.importStep(str(hardware_path)).val().Solids()
assert len(hardware_solids)==103
def bounds(s):
 q=s.BoundingBox();return[q.xmin,q.ymin,q.zmin,q.xmax,q.ymax,q.zmax]
def hardware(name):
 record=next(r for r in hardware_manifest['parts'] if r['name']==name)
 matches=[s for s in hardware_solids if max(abs(x-y) for x,y in zip(bounds(s),record['bounds_mm']))<1e-6]
 assert len(matches)==1,(name,len(matches))
 return matches[0]
heads={};ties={};fullscrews={};nuts={};oldbolts={}
for a in (90,215,325):
 x,z=p.polar(47,a)
 oldbolts[a]=hardware(f'FL_carrier_closure_bolt_{a}')
 fullscrews[a]=oldbolts[a].translate((0,-2.1,0));heads[a]=fullscrews[a]
 nuts[a]=hardware(f'FL_carrier_closure_nut_{a}')
for a in (90,210,330):
 ties[a]=hardware(f'Pod M3x60 screw {a}')
original_cases=[]
for hip in (0,-5,-10,30):
 pairs=[]
 for ta,tie in ties.items():
  for ha,screw in oldbolts.items():
   overlap=vol(tie.rotate((0,0,0),(0,1,0),hip).intersect(screw))
   if overlap>1e-5:pairs.append(dict(tie_deg=ta,closure_deg=ha,overlap_mm3=overlap))
 original_cases.append(dict(hip_deg=hip,interfering_pairs=pairs))
samples=[]
for hip in (-180,-90,-60,-30,-10,-5,0,30,60,90,180):
 for ta,tie in ties.items():
  moved=tie.rotate((0,0,0),(0,1,0),hip)
  for ha,head in heads.items():
   gap=moved.distance(head)
   samples.append(dict(hip_deg=hip,tie_deg=ta,head_deg=ha,gap_mm=gap,passed=gap>=1-1e-7))
continuous=[dict(tie_deg=ta,head_deg=ha,tie_y_min_mm=tie.BoundingBox().ymin,head_y_max_mm=head.BoundingBox().ymax,axial_gap_mm=tie.BoundingBox().ymin-head.BoundingBox().ymax,all_real_hip_angles_proved=True) for ta,tie in ties.items() for ha,head in heads.items()]
fixed={'cup':p.newcup,'closure':p.newclosure,'hip motor':b.motor_envelope()}
input_hashes=dict(p.inputs,hardware=dict(path=str(hardware_path),sha256=hardware_manifest['sha256'],solid_count=103),hardware_manifest=dict(path=str(hardware_manifest_path),sha256=hashlib.sha256(hardware_manifest_path.read_bytes()).hexdigest()))
for key,name in [('housing','paired-native-roll_cartridge_1.step'),('retainer','paired-native-roll_outer_retainer_1.step'),('rear plate','paired-native-roll_stator_backplate_1.step')]:
 path=N/'exports'/name
 fixed[key]=read(name);input_hashes[key]=dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
tips=[]
for a in (90,215,325):
 x,z=p.polar(47,a);tip=b.cyl(2,3.1,(x,-18.2,z))
 for name,solid in fixed.items():
  gap=tip.distance(solid);overlap=vol(tip.intersect(solid))
  tips.append(dict(closure_angle_deg=a,against=name,gap_mm=gap,overlap_mm3=overlap,passed=overlap<1e-5))
 # A conventional holding wrench can still pass its open jaw over the
 # longer protruding tip; all geometry and handle dimensions are explicit.
 head=b.cyl(8,3.8,(0,-16,0));handle=b.box(100,3.8,8,(55,-14.1,0)).rotate((0,0,0),(0,1,0),-15)
 mouth=b.box(20,6,7.1,(-5.8,-14.1,0))
 tool=head.fuse(handle).cut(mouth).rotate((0,0,0),(0,1,0),-a).translate((x,0,z))
 tool=tool.translate((math.cos(math.radians(a)),0,math.sin(math.radians(a))))
 for name,solid in dict(fixed,**{'screw':fullscrews[a]}).items():
  overlap=vol(tool.intersect(solid));tips.append(dict(closure_angle_deg=a,check='ordinary7mm wrench at1mm radial stand-off',against=name,overlap_mm3=overlap,passed=overlap<1e-5))
 # The documented radial entry is8mm outward followed by7mm seating.
 for stand in (8,6,4,2):
  moved=tool.translate(((stand-1)*math.cos(math.radians(a)),0,(stand-1)*math.sin(math.radians(a))))
  overlap=vol(moved.intersect(fullscrews[a]));tips.append(dict(closure_angle_deg=a,check='wrench radial approach over longer screw',radial_standoff_mm=stand,overlap_mm3=overlap,passed=overlap<1e-5))
sections=[]
def section_inertia(shape):
 props=GProp_GProps();BRepGProp.SurfaceProperties_s(shape.wrapped,props,1e-10,True)
 matrix=props.MatrixOfInertia()
 return dict(area_mm2=props.Mass(),centroid_mm=list(props.CentreOfMass().Coord()),Iyy_mm4=matrix.Value(2,2),Izz_mm4=matrix.Value(3,3))
# Pitch-local X cuts isolate the cup-to-journal transition in its common
# Y=-25..-4 and Z=-30..30 support region. The central shaft hole and the
# existing cable/window cuts remain represented by the native source.
region=b.box(120,21,60,(-55,-14.5,0))
old_web=p.cup.intersect(region);new_web=p.newcup.intersect(region)
for x in (-54,-52,-50,-48,-46,-45,-44.5,-44,-43.5,-43,-42.5,-42,-41.5,-41,-40.9):
 plane=cq.Face.makePlane(basePnt=(x,0,0),dir=(1,0,0))
 old=old_web.intersect(plane);new=new_web.intersect(plane)
 oa=sum(f.Area() for f in old.Faces());na=sum(f.Area() for f in new.Faces())
 oi,ni=section_inertia(old),section_inertia(new)
 sections.append(dict(pitch_local_x_mm=x,source_area_mm2=oa,proposed_area_mm2=na,area_removed_mm2=oa-na,retained_fraction=na/oa if oa else None,source_centroidal_inertia=oi,proposed_centroidal_inertia=ni,Iyy_retained_fraction=ni['Iyy_mm4']/oi['Iyy_mm4'],Izz_retained_fraction=ni['Izz_mm4']/oi['Izz_mm4']))
out=dict(passed=p.out['passed'] and all(s['passed'] for s in samples) and all(r['passed'] for r in tips),status='analysis_geometry_only_not_native_release',inputs=input_hashes,preserved_original_actual_hardware_cases=original_cases,
 analytic_proof=dict(statement='Every rigid rotation about the hip Y axis preserves theYcoordinate of every point. All three ties occupyY>=1 and all three closure heads occupyY<=0. Therefore each of the nine pairings has at least1mm Euclidean separation for every real hip angle.',nominal_only=True,nine_pair_bounds=continuous),sampled_exact_distances=samples,rear_tip_and_tool_checks=tips,
 web_sections=dict(method='Exact intersection with X-normal planes after clipping toY[-25,-4],Z[-30,30]; pitch-axis local coordinates. Areas and centroidal second moments use exact section faces. These are sampled geometric properties, not strength calculations.',rows=sections,minimum_sampled_proposed_area_mm2=min(r['proposed_area_mm2'] for r in sections),maximum_fraction_removed=max((1-r['retained_fraction']) for r in sections if r['retained_fraction'] is not None),minimum_Iyy_retained_fraction=min(r['Iyy_retained_fraction'] for r in sections),minimum_Izz_retained_fraction=min(r['Izz_retained_fraction'] for r in sections)),
 limitations=['The analytic proof assumes exact nominal coordinates and rigidY-axis rotation; screw length, printed floors, tube lengths, deflection and manufacturing errors remain outside it.','Cup/journal cross-sections are finite samples of one support region. Area retention does not establish bending stiffness, stress, impact, fatigue or printed layer strength.','The holding-wrench envelope is generic; a particular purchased wrench, hand clearance and full robot environment remain unverified.','Native authoring, both handed exports and downstream full assembly must be checked separately.'])
(H/'closure-continuous-review.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(passed=out['passed'],exact_pairs=len(samples),tip_tool_checks=len(tips),failed=[r for r in tips if not r['passed']],web_sections=out['web_sections']),indent=2))
