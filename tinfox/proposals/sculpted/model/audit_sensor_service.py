"""Sample sensor-module removal against the assembled standing robot."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
import trimesh
from kinematics import ROOT,P,matrix,uniform
folder=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'output/sensor-saddle-work'
raw=(folder/'model.json').read_bytes();model=json.loads(raw)
P.update(model['parameters'])
parts={p['name']:p for p in model['parts'] if p.get('service_role') not in ['keepout','withdrawal']}
q=uniform([0,30,-60]);meshes={}
for name,p in parts.items():
    m=model['meshes'][p['mesh']];mesh=trimesh.Trimesh(m['vertices'],m['faces'],process=False)
    mesh.apply_transform(matrix(p,q));meshes[name]=mesh
hood={n for n in parts if n=='front_fascia' or n.startswith(('lidar','camera_','lens_','lens_ring_','iris_','sensor_window','depth_sensor'))}
cradle={'body_nose_surround'}|{n for n in parts if n.startswith('sensor_hood_nut_')}
rows=[]
cases=[('hood with sensors',hood,{n for n in parts if n.startswith('sensor_hood_screw_')}),
 ('main body cover with display and switch',{'body_center_0','status_display','status_display_dial','power_button','body_wordmark','body_serial','body_status_dot'} & set(parts),{n for n in parts if n.startswith(('body_service_screw_','body_clamp_screw_'))}),
 ('cradle, hood removed',cradle,hood|{n for n in parts if n.startswith(('sensor_hood_screw_','sensor_root_screw_','sensor_root_washer_'))})]
for label,moving,removed in cases:
    manager=trimesh.collision.CollisionManager()
    for name,mesh in meshes.items():
        if name not in moving|removed:manager.add_object(name,mesh)
    for dz in [.2,1,3,5,10,20,40,80]:
        transform=np.eye(4);transform[2,3]=dz;hits=[]
        for name in moving:
            hit,names=manager.in_collision_single(meshes[name],transform=transform,return_names=True)
            if hit:hits.extend([[name,n] for n in sorted(names)])
        rows.append({'assembly':label,'upward_travel_mm':dz,'pairs':hits})
report={'model_sha256':hashlib.sha256(raw).hexdigest(),'samples':rows,'passed':not any(r['pairs'] for r in rows),
 'scope':'Standing robot. Fasteners listed for the operation are removed, electrical connections disconnected. Rigid meshes at eight heights per operation; no hand/handle, flexible-cable or tolerance validation.'}
(folder/'sensor-service.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'passed':report['passed'],'samples':len(rows),'failures':[r for r in rows if r['pairs']]},indent=2))
