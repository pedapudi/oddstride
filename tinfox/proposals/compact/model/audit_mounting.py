"""Check installed fasteners against the moving rod and measure CAD shin sections."""
import json,hashlib
import numpy as np
import cadquery as cq
import trimesh
from kinematics import ROOT,P,POSES,LEGS,matrix

data=json.loads((ROOT/'output/model.json').read_text())
parts=[p for p in data['parts'] if p['leg']=='FL' and (p['name'].endswith('_pushrod') or any(t in p['name'] for t in ['_bolt_','_sleeve_','_pod_tie_','_knee_axle','_knee_inner_spacer']))]
cm=trimesh.collision.CollisionManager()
for p in parts:
 m=data['meshes'][p['mesh']];cm.add_object(p['name'],trimesh.Trimesh(vertices=m['vertices'],faces=m['faces'],process=False))
hits=[]
for k in range(*[int(x) for x in [P['joint_limits_deg']['knee'][0],P['joint_limits_deg']['knee'][1]+1]]):
 poses={l:list(q) for l,q in POSES['stand'].items()};poses['FL'][2]=k
 for p in parts:cm.set_transform(p['name'],matrix(p,poses))
 _,pairs=cm.in_collision_internal(return_names=True)
 bad=[sorted(pair) for pair in pairs if 'FL_pushrod' in pair]
 if bad:hits.append({'knee_deg':k,'pairs':bad})
sections=[]
s=cq.importers.importStep(str(ROOT/'output/step-parts/shin_inner.step')).val().fuse(cq.importers.importStep(str(ROOT/'output/step-parts/shin_outer.step')).val())
for z in range(-35,-146,-5):
 slab=cq.Workplane('XY').box(200,200,.2).val().translate((0,60,z));cut=s.intersect(slab)
 if cut.Volume()<1:raise RuntimeError('Missing shin section')
 inertia=cq.Shape.matrixOfInertia(cut);b=cut.BoundingBox();c=cut.Center()
 iy=inertia[1][1]/.2-cut.Volume()/.2*.2**2/12
 section_modulus=iy/max(abs(b.xmin-c.x),abs(b.xmax-c.x))
 sections.append({'z_mm':z,'area_mm2':cut.Volume()/.2,'Iy_mm4':iy,'Ix_mm4':inertia[0][0]/.2-cut.Volume()/.2*.2**2/12,'section_modulus_y_mm3':section_modulus})
# Measure exported transverse skin beneath the curved groove. Projecting each
# triangle into XZ gives exact ray intersections for this tessellated surface.
from build import shin_station
mesh=trimesh.load_mesh(ROOT/'output/stl/shin_inner.stl')
tri=mesh.triangles;a=tri[:,0];b=tri[:,1]-a;c=tri[:,2]-a
det=b[:,0]*c[:,2]-b[:,2]*c[:,0];valid=np.abs(det)>1e-10

def ray_y(x,z):
    dx=x-a[:,0];dz=z-a[:,2]
    u=np.divide(dx*c[:,2]-dz*c[:,0],det,out=np.zeros_like(det),where=valid)
    v=np.divide(b[:,0]*dz-b[:,2]*dx,det,out=np.zeros_like(det),where=valid)
    mask=valid&(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)
    return np.unique(np.round((a[:,1]+u*b[:,1]+v*c[:,1])[mask],5))
wall=[];holes_skipped=0
for z in range(-78,-145,-1):
    center,_,_=shin_station(z)
    for offset in [-1.5,0,1.5]:
        x=center+offset
        hole_distance=min(np.hypot(x-shin_station(h)[0],z-h) for h in [-91,-132])
        if hole_distance<1.8:
            holes_skipped+=1;continue
        yy=ray_y(x,z)
        if len(yy)<2:raise RuntimeError(f'Missing shin skin at x={x}, z={z}')
        wall.append({'x_mm':x,'z_mm':z,'skin_mm':float(yy[1]-yy[0])})
bolt_ligaments=[]
for z in [-91,-132]:
    x,_,_=shin_station(z)
    cut=s.intersect(cq.Workplane('XY').box(200,200,.02).val().translate((0,60,z)))
    bb=cut.BoundingBox()
    bolt_ligaments.append({'z_mm':z,'hole_center_x_mm':x,'sagittal_edge_ligament_mm':min(x-1.7-bb.xmin,bb.xmax-x-1.7)})
outline=[]
for z in range(-35,-146,-10):
    bounds=mesh.section(plane_origin=[0,0,z],plane_normal=[0,0,1]).bounds
    outline.append({'z_mm':z,'center_x_mm':float(bounds[:,0].mean()),'width_mm':float(bounds[1,0]-bounds[0,0])})
centers=np.array([v['center_x_mm'] for v in outline]);widths=np.array([v['width_mm'] for v in outline])
outline_report={'samples':outline,'center_second_differences_mm':np.diff(centers,2).tolist(),
 'single_curvature_sign':bool(np.all(np.diff(centers,2)<0)),
 'monotonic_taper':bool(np.all(np.diff(widths)<0)),
 'scope':'Center and width of the exported shin silhouette sections at 10 mm spacing across the exposed shaft; fixed bearing ring and boot interface excluded.'}
wall_report={'sample_count':len(wall),'intentional_hole_rays_skipped':holes_skipped,
 'minimum_sampled_skin_mm':min(v['skin_mm'] for v in wall),'minimum_location':min(wall,key=lambda v:v['skin_mm']),
 'bolt_sagittal_edge_ligaments':bolt_ligaments,
 'scope':'Transverse ray thickness through the exported inner-shin groove at 1 mm longitudinal spacing and three offsets across its center; mirrored outer half shares this geometry. Intentional drill openings excluded. Bolt edge ligaments use exact CAD sections. This is a nominal geometry check, not a stress or print-strength qualification.'}
report={'model_sha256':hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest(),'rod_hardware_sweep':{'knee_range_deg':P['joint_limits_deg']['knee'],'step_deg':1,'collisions':hits},'shin_sections':sections,'shin_skin_audit':wall_report,'shin_outline_audit':outline_report,'minimum_shin_section_modulus_y_mm3':min(s['section_modulus_y_mm3'] for s in sections),'scope':'Nominal rod versus modeled fastening hardware at one-degree increments. Shin sections are 0.2 mm CAD slices at 5 mm intervals, measured about their centroids; no local stress, anisotropy, fatigue or torsion qualification.'}
(ROOT/'output/mounting-audit.json').write_text(json.dumps(report,indent=2))
print('Rod/hardware collision samples:',len(hits),'minimum section modulus:',report['minimum_shin_section_modulus_y_mm3'],flush=True)
if hits:print(hits[:3])
