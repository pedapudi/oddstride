"""Check the revised motor pod against both hip carriers through a full turn."""
import hashlib,json
from functools import cache
import cadquery as cq
import trimesh
from trimesh.collision import CollisionManager
import slim_limb as design
from kinematics import ROOT,rotation

OUT=ROOT/'output/slim-limb-work';raw=(OUT/'model.json').read_bytes();rows=[]
@cache
def mesh(key):
    file=OUT/'step'/(key+'.step')
    shape=cq.importers.importStep(str(file)).val() if file.exists() else design.shifted_source(key,(0,0,0))
    vv,ff=shape.tessellate(.08,.1)
    return trimesh.Trimesh(vertices=[v.toTuple() for v in vv],faces=ff,process=False)
for front in [1,-1]:
    manager=CollisionManager();manager.add_object('carrier',mesh('motor_carrier_'+str(front)))
    for key in ['hip_hub','thigh_inner','thigh_outer',*[kind+str(a) for kind in ['pod_tie_','pod_sleeve_'] for a in [90,210,330]]]:
        hits=[];gap=float('inf')
        for angle in range(-180,181):
            matrix=rotation('y',angle)
            if manager.in_collision_single(mesh(key),transform=matrix):hits.append(angle)
            if angle%90==0:gap=min(gap,float(manager.min_distance_single(mesh(key),transform=matrix)))
        rows.append({'carrier':front,'part':key,'sample_step_deg':1,'collision_angles':hits,
            'minimum_mesh_gap_at_quadrant_samples_mm':gap,'distance_sample_step_deg':90,'passed':not hits})
        print(front,key,not hits,round(gap,3),flush=True)
report={'model_sha256':hashlib.sha256(raw).hexdigest(),'checks':rows,'passed':all(r['passed'] for r in rows),
    'scope':'Nominal rigid carrier/pod clearance over one full hip revolution at one-degree steps. Does not test torso contacts, tolerances or elastic deflection.'}
(OUT/'mount-clearance.json').write_text(json.dumps(report,indent=2));assert report['passed']
