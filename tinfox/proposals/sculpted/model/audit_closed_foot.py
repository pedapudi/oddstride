"""Bound continuous rigid boot clearance using exact sampled surface distances."""
import hashlib,json,math,time,sys
from pathlib import Path
import cadquery as cq
import numpy as np
from kinematics import ROOT

OUT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'output/closed-thigh-work'
raw=(OUT/'model.json').read_bytes();model=json.loads(raw)
paths=[OUT/'step'/(key+'.step') for key in ['thigh_inner','thigh_outer']]
halves=[cq.importers.importStep(str(path)).val() for path in paths]
thigh=cq.Compound.makeCompound(halves)
foot_path=ROOT/'output/step-parts/foot.step'
foot=cq.importers.importStep(str(foot_path)).val()
p=next(p for p in model['parts'] if p['name']=='FL_foot')
vertices=np.array(model['meshes'][p['mesh']]['vertices'])
bounds=np.array([vertices.min(axis=0),vertices.max(axis=0)])
bb=foot.BoundingBox();dy=bounds[:,1].mean()-(bb.ymin+bb.ymax)/2
foot=foot.translate((0,float(dy),0));bb=foot.BoundingBox()
exact_bounds=np.array([[bb.xmin,bb.ymin,bb.zmin],[bb.xmax,bb.ymax,bb.zmax]])
assert np.max(np.abs(bounds-exact_bounds))<.3,'Foot reference does not match the modeled boot envelope'
radius=math.hypot(max(abs(bb.xmin),abs(bb.xmax)),max(abs(bb.zmin),abs(bb.zmax)))
low,high=model['parameters']['joint_limits_deg']['knee'];step=.5
count=round((high-low)/step)+1;rows=[];t=time.time()
for i in range(count):
    q=low+i*step
    moved=foot.rotate((0,0,0),(0,1,0),q).translate((0,0,-model['parameters']['thigh']))
    gap=thigh.distance(moved);rows.append({'knee_deg':q,'distance_mm':gap})
    if i%36==0:print(q,round(gap,4),'seconds',round(time.time()-t,1),flush=True)
minimum=min(rows,key=lambda r:r['distance_mm'])
motion_bound=2*radius*math.sin(math.radians(step/2)/2)
required=model['parameters']['thigh_foot_clearance_required_mm']
report={'model_sha256':hashlib.sha256(raw).hexdigest(),
    'input_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*paths,foot_path]},
    'checker':'OpenCascade BRepExtrema surface distance; nominal rigid boot versus both structural thigh halves',
    'samples':rows,'minimum':minimum,'step_deg':step,'foot_reference_y_translation_mm':dy,
    'foot_radius_about_knee_bound_mm':radius,'nearest_sample_rotation_deg':step/2,
    'maximum_inter_sample_point_motion_mm':motion_bound,
    'continuous_nominal_distance_lower_bound_mm':minimum['distance_mm']-motion_bound,
    'required_nominal_gap_mm':required,'passed':minimum['distance_mm']-motion_bound>=required,
    'scope':'Full modeled knee range. Subtracting maximum foot-point motion to the nearest sample bounds rigid clearance between samples. Common hip rotations preserve this relative distance. Actual boot deformation, manufacturing tolerances and loaded deflection remain unqualified.'}
(OUT/'foot-clearance.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='samples'}),flush=True)
assert report['passed']
