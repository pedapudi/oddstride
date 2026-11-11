"""Measure nominal CAD body skin and the separate nose attachment interfaces."""
from pathlib import Path
import json,math,hashlib
import numpy as np
import trimesh
import cadquery as cq
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
from OCP.gp import gp_Lin,gp_Pnt,gp_Dir
import build
from kinematics import ROOT,P
outer=build.torso();inner=build.torso(P['body_skin']);skin=outer.cut(inner)
mesh_cache={}
def surface_mesh(shape):
    key=id(shape)
    if key not in mesh_cache:
        vertices,faces=shape.tessellate(.15,.1)
        mesh_cache[key]=trimesh.Trimesh(vertices=[v.toTuple() for v in vertices],faces=faces,process=False)
    return mesh_cache[key]
samples=[]
def probe(label,shape,point,normal):
    point=np.array(point,float);normal=np.array(normal,float);normal/=np.linalg.norm(normal)
    seed=point.copy();mesh=surface_mesh(outer if shape is skin else shape)
    candidates=np.flatnonzero(mesh.face_normals@normal>.95)
    nearest=candidates[np.argmin(np.linalg.norm(mesh.triangles_center[candidates]-point,axis=1))]
    point=mesh.triangles_center[nearest];normal=mesh.face_normals[nearest]
    start=point+normal*2
    intersections=IntCurvesFace_ShapeIntersector();intersections.Load(shape.wrapped,1e-7)
    intersections.Perform(gp_Lin(gp_Pnt(*start),gp_Dir(*(-normal))),0,8)
    positions=sorted(set([0,8]+[round(intersections.WParameter(i),8) for i in range(1,intersections.NbPnt()+1)]))
    thickness=0
    for a,b in zip(positions,positions[1:]):
        midpoint=start-normal*((a+b)/2)
        if any(s.isInside(tuple(midpoint),1e-6) for s in shape.Solids()):thickness+=b-a
    samples.append({'location':label,'seed_point_mm':seed.tolist(),'point_mm':point.tolist(),'seed_to_surface_mm':float(np.linalg.norm(point-seed)),'normal':normal.tolist(),'material_path_mm':thickness})
    return thickness
for x in [-228,-212,-192,-172,-148,0,148,172,192,214,226,236]:
    width,top,bottom=build.body_dimensions(x);yy=width/2
    dw,dt,db=(build.body_dimensions(x+.001)-build.body_dimensions(x-.001))/.002;dy=dw/2
    bt,bb,_=build.body_corner(x);dbt,dbb,_=(build.body_corner(x+.001)-build.body_corner(x-.001))/.002
    probe(f'roof_x{x}',skin,[x,0,top],[-dt,0,1])
    probe(f'side_x{x}',skin,[x,yy,(top+bottom)/2],[-dy,1,0])
    probe(f'upper_bevel_x{x}',skin,[x,yy-bt/2,top-bt/2],[-(dy+dt-dbt),1,1])
    probe(f'lower_bevel_x{x}',skin,[x,yy-bb/2,bottom+bb/2],[-(dy-db-dbb),1,-1])
    probe(f'bottom_x{x}',skin,[x,0,bottom],[db,0,-1])
for degree in [20,35,50,65]:
    a=math.radians(degree)
    probe(f'leading_roof_blend_{degree}',skin,[240.4+5*math.cos(a),0,40.5+5*math.sin(a)],[math.cos(a),0,math.sin(a)])
nominal=list(samples);samples=[]
fascia=cq.importers.importStep(str(ROOT/'output/step-parts/front_fascia.step')).val()
nose=cq.importers.importStep(str(ROOT/'output/step-parts/body_nose_surround.step')).val()
for y,z in [(0,-27),(0,35),(90,0),(-90,0),(85,-30),(-85,-30)]:probe(f'fascia_y{y}_z{z}',fascia,[245.4,y,z],[1,0,0])
for y in [-75,-50,-25,0,25,50,75]:
    z=30;u=y/98;v=(z-2)/42;crown=P['front_face_crown_mm']
    xx=build.face_x(y,z)
    dxdy=-2*crown*y/98**2
    dxdz=-2*P['front_face_vertical_crown_mm']*(z-2)/42**2
    probe(f'fascia_bow_y{y}',fascia,[xx,y,z],[1,-dxdy,-dxdz])
for z in [-33,36,39]:
    v=(z-2)/42;xx=build.face_x(0,z)
    dxdz=-2*P['front_face_vertical_crown_mm']*(z-2)/42**2
    probe(f'fascia_vertical_return_z{z}',fascia,[xx,0,z],[1,0,-dxdz])
finished=list(samples);samples=[]
for x in [218,224,228]:
    w,top,b=build.body_dimensions(x);dt=(build.body_dimensions(x+.001)[1]-build.body_dimensions(x-.001)[1])/.002
    probe(f'return_tongue_x{x}',nose,[x,3.5,top],[-dt,0,1])
sections=[]
for x in [216,220,224,228,232,236]:
    slab=cq.Workplane('XY').box(.2,12,30).val().translate((x,0,45));cut=nose.intersect(slab)
    sections.append({'x_mm':x,'area_mm2':cut.Volume()/.2})
report={'model_sha256':hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest(),
 'nominal_skin_samples':nominal,'nominal_skin_min_mm':min(v['material_path_mm'] for v in nominal),
 'finished_fascia_samples':finished,'finished_fascia_min_mm':min(v['material_path_mm'] for v in finished),
 'return_tongue_samples':samples,'return_tongue_sections':sections,
 'minimum_return_tongue_section_mm2':min(v['area_mm2'] for v in sections),
 'scope':'Exact CAD line intersections along actual tessellated surface normals; analytic targets select nearby outer surface samples. Material intervals are classified inside the solid and summed. Nominal envelope samples exclude openings and mounting ribs. Finished fascia and attachment tongue are checked separately; samples do not establish every local minimum, print strength, sealing or load capacity.'}
(ROOT/'output/body-skin-audit.json').write_text(json.dumps(report,indent=2))
print('Nominal minimum',report['nominal_skin_min_mm'],'finished fascia minimum',report['finished_fascia_min_mm'],'tongue section',report['minimum_return_tongue_section_mm2'],flush=True)
