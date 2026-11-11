"""Sample printed body walls and verify the removable nose support interfaces."""
import json,hashlib
import numpy as np
import trimesh,cadquery as cq
from kinematics import ROOT

OUT=ROOT/'output';raw=(OUT/'model.json').read_bytes();model=json.loads(raw)
parts={p['name']:p for p in model['parts']}
def mesh(name):
    m=model['meshes'][parts[name]['mesh']]
    return trimesh.Trimesh(vertices=m['vertices'],faces=m['faces'],process=False)

shell_names=[n for n,p in parts.items() if n.startswith(('body_','belly_')) and p['material']=='petg']
shell=trimesh.util.concatenate([mesh(n) for n in shell_names])

class AxisRays:
    def __init__(self,mesh):
        self.tri=mesh.triangles;self.normals=mesh.face_normals
    def hits(self,axis,p):
        ij=[i for i in range(3) if i!=axis];a=self.tri[:,0];b=self.tri[:,1]-a;c=self.tri[:,2]-a
        det=b[:,ij[0]]*c[:,ij[1]]-b[:,ij[1]]*c[:,ij[0]];valid=np.abs(det)>1e-10
        d0=p[0]-a[:,ij[0]];d1=p[1]-a[:,ij[1]]
        u=np.divide(d0*c[:,ij[1]]-d1*c[:,ij[0]],det,out=np.zeros_like(det),where=valid)
        v=np.divide(b[:,ij[0]]*d1-b[:,ij[1]]*d0,det,out=np.zeros_like(det),where=valid)
        mask=valid&(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)
        positions=(a[:,axis]+u*b[:,axis]+v*c[:,axis])[mask];normals=self.normals[mask]
        rounded=np.round(positions,5);out=[]
        for value in np.unique(rounded):
            candidates=normals[rounded==value];normal=candidates[np.argmax(np.abs(candidates[:,axis]))]
            out.append((float(value),float(abs(normal[axis])),normal))
        return sorted(out,key=lambda v:v[0])
    def normal_wall(self,point,normal):
        direction=-normal;origin=point+direction*1e-4
        e1=self.tri[:,1]-self.tri[:,0];e2=self.tri[:,2]-self.tri[:,0]
        h=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h);valid=np.abs(det)>1e-10
        inv=np.divide(1,det,out=np.zeros_like(det),where=valid);offset=origin-self.tri[:,0]
        u=inv*np.einsum('ij,ij->i',offset,h);q=np.cross(offset,e1);v=inv*(q@direction);t=inv*np.einsum('ij,ij->i',e2,q)
        mask=valid&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)&(t>1e-4)
        return float(np.min(t[mask])+1e-4) if np.any(mask) else None

rays=AxisRays(shell);samples=[];voids=[]
def sample(label,axis,p,side,bound):
    hits=rays.hits(axis,p)
    if len(hits)<2: voids.append({'region':label,'point':p});return
    pair=hits[-2:] if side>0 else hits[:2]
    if side*pair[0 if side>0 else 1][0]<bound:
        voids.append({'region':label,'point':p});return
    length=pair[1][0]-pair[0][0]
    edge=pair[1] if side>0 else pair[0];position=np.zeros(3);position[axis]=edge[0];position[[i for i in range(3) if i!=axis]]=p
    normal=edge[2];normal=normal if normal[axis]*side>0 else -normal
    normal_wall=rays.normal_wall(position,normal)
    if label=='roof' and -4<=p[0]<=44 and abs(p[1])<=14:label='display_pocket'
    samples.append({'region':label,'axis':axis,'point':p,'axis_thickness_mm':length,'normal_ray_thickness_mm':normal_wall,
                    'normal_corrected_thickness_mm':length*min(pair[0][1],pair[1][1])})
for x in [-110,-80,-40,0,40,80,110,145,170,195,215,230]:
    for y in [-55,-30,0,30,55]:sample('roof',2,[x,y],1,30)
for x in [-110,-80,-40,0,40,80,110]:
    for z in [0,15,30]:
        sample('left_side',1,[x,z],1,80);sample('right_side',1,[x,z],-1,80)
for y in [-82,-80,-60,-30,0,30,60,80,82]:
    for z in [-40,0,40]:sample('front_rim',0,[y,z],1,233)
for y in [-50,-30,0,30,50]:
    for z in [-25,0,25]:sample('rear_cap',0,[y,z],-1,230)
summary={}
for label in ['roof','display_pocket','left_side','right_side','front_rim','rear_cap']:
    group=[s for s in samples if s['region']==label]
    summary[label]={'sample_count':len(group),'minimum_normal_ray_thickness_mm':min(s['normal_ray_thickness_mm'] for s in group if s['normal_ray_thickness_mm'] is not None),'minimum_normal_corrected_thickness_mm':min(s['normal_corrected_thickness_mm'] for s in group),'minimum_axis_thickness_mm':min(s['axis_thickness_mm'] for s in group),'maximum_axis_thickness_mm':max(s['axis_thickness_mm'] for s in group)}

panel_rays=AxisRays(mesh('nose_panel'));panel_floor=[]
for y in [-68,68]:
    for z in [-30,30]:
        hits=panel_rays.hits(0,[y+2.3,z]);panel_floor.append(hits[-1][0]-hits[-2][0])
folder=OUT/'step-parts';panel=cq.importers.importStep(str(folder/'nose_panel.step')).val()
rim=cq.Compound.makeCompound([cq.importers.importStep(str(folder/f'{n}.step')).val() for n in shell_names if n.startswith(('body_front','belly_front'))])
support=[]
for path in sorted(folder.glob('nose_standoff_*.step')):
    tab=cq.importers.importStep(str(path)).val()
    support.append({'part':path.stem,'solid_count':len(tab.Solids()),'panel_distance_mm':tab.distance(panel),'rim_distance_mm':tab.distance(rim),'panel_intersection_mm3':tab.intersect(panel).Volume(),'rim_intersection_mm3':tab.intersect(rim).Volume()})
# Counterbore/head fit and straight tool access are checked as rigid meshes.
manager=trimesh.collision.CollisionManager()
for n in shell_names+['nose_panel']:manager.add_object(n,mesh(n))
heads=[n for n in parts if n.startswith(('nose_fastener_','nose_rim_fastener_'))]
head_hits=[];tool_hits=[]
for name in heads:
    hit,names=manager.in_collision_single(mesh(name),return_names=True)
    if hit:head_hits.append({'head':name,'covers':sorted(names)})
    p=parts[name]['com_mm'];tool=trimesh.creation.cylinder(radius=2.5,height=20,sections=32)
    transform=trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]);transform[:3,3]=[253.1,p[1],p[2]]
    hit,names=manager.in_collision_single(tool,transform=transform,return_names=True)
    if hit:tool_hits.append({'head':name,'covers':sorted(names)})
report={'model_sha256':hashlib.sha256(raw).hexdigest(),'shell_regions':summary,'wall_samples':samples,'void_samples_skipped':voids,
        'nose_panel_nominal_mm':1.6,'minimum_sampled_panel_counterbore_floor_mm':min(panel_floor),'support_tabs':support,
        'head_cover_intersections':head_hits,'tool_access_intersections':tool_hits,
        'scope':'Printed rigid covers only. Wall rays start on the exported outer surface and run inward along its triangle normal. The auxiliary axis-ray correction is a conservative approximation. Neither method is a global minimum proof. Intentional openings are recorded as skipped samples. Tab contacts use exact STEP solids. Head fits and straight Ø5 mm ×20 mm access envelopes use CAD meshes. Screw envelopes remain provisional; final screw selection, tolerances and loaded retention remain unqualified.'}
(OUT/'body-fit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(summary,indent=2));print('Panel floor',min(panel_floor));print('Supports',support);print('Head hits',head_hits,'tool hits',tool_hits)
