"""Screen a conventional shoulder screw as a substitution, without approving it."""
import hashlib,json,math
import cadquery as cq
import trimesh
from integrated_candidate import OUT,PIN,RADIUS,cyl
from kinematics import P,POSES,matrix
raw=(OUT/'model.json').read_bytes();d=json.loads(raw);P.update(d['parameters'])
review=OUT/'hardware-review';review.mkdir(exist_ok=True)
meshes={k:trimesh.Trimesh(vertices=v['vertices'],faces=v['faces'],process=False) for k,v in d['meshes'].items()}
parts={p['name']:p for p in d['parts'] if p.get('service_role') not in ['keepout','withdrawal']}
results=[]
for name,x,z in [('input_pin',RADIUS,0),('output_pin',*PIN)]:
    # Bolt Depot 14232: 6 x 20 shoulder, M5 x 9.75 thread, 10 x 4.5 head.
    # Keep shoulder-to-thread transition at Y62, as in the existing fork.
    s=cyl(2.5,9.75,(x,52.25,z)).fuse(cyl(3,20,(x,62,z)),cyl(5,4.5,(x,82,z)))
    cq.exporters.export(s,str(review/(name+'-standard-envelope.step')))
    vv,ff=s.tessellate(.08,.1);mesh=trimesh.Trimesh(vertices=[v.toTuple() for v in vv],faces=ff,process=False)
    part=parts['FL_'+name]
    for label,q in POSES.items():
        manager=trimesh.collision.CollisionManager()
        for n,p in parts.items():
            if n==part['name']:continue
            manager.add_object(n,meshes[p['mesh']],transform=matrix(p,q))
        _,hits=manager.in_collision_single(mesh,transform=matrix(part,q),return_names=True)
        results.append({'pin':name,'pose':label,'reported_contacts':sorted(hits)})
report={'source_model_sha256':hashlib.sha256(raw).hexdigest(),'specification':{'supplier_reference':'Bolt Depot 14232','shoulder_diameter_mm':6,'shoulder_length_mm':20,'thread_length_mm':9.75,'head_diameter_mm':10,'head_height_mm':4.5},'change_from_modeled_pin_mm':{'inboard_extension':3.75,'outboard_extension':3.5},'samples':results,'status':'Dimensional substitution study only. Mating contacts included. Not a drop-in replacement or procurement approval.'}
(review/'standard-pivot-audit.json').write_text(json.dumps(report,indent=2))
for row in results:
 if row['pose']=='stand':print(row)
