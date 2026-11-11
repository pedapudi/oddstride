"""Prepare unsliced thigh orientations, removable exterior supports and tool checks."""
import hashlib,json,math,zipfile,sys
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
import trimesh
import cadquery as cq
from kinematics import ROOT
from cad_authority import require_generated_authority
require_generated_authority(ROOT)
import build as b
import manufacturing_thigh as design
from mesh_cleanup import clean_mesh

OUT=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'output/manufacturing-thigh-work'
BASE=Path(sys.argv[2]) if len(sys.argv)>2 else ROOT/'output/seamless-limb-work'
raw=(OUT/'model.json').read_bytes();model=json.loads(raw);stamp=hashlib.sha256(raw).hexdigest()
for sub in ['print-stl','print-preparation']:(OUT/sub).mkdir(exist_ok=True)
def rotation(angle):return trimesh.transformations.rotation_matrix(math.radians(angle),[1,0,0])
def orient(mesh,angle):
    s=mesh.copy();matrix=rotation(angle);s.apply_transform(matrix)
    shift=np.array([-s.bounds[0,0],-s.bounds[0,1],-s.bounds[0,2]])
    s.apply_translation(shift);matrix[:3,3]+=shift
    return s,matrix
def metric(mesh):
    n=mesh.face_normals;c=mesh.triangles_center;a=mesh.area_faces
    down=(n[:,2]<-math.cos(math.radians(45)))&(c[:,2]>.5)
    projected=a[down]*(-n[down,2]);area=float(projected.sum())
    height=float((projected*c[down,2]).sum()/max(area,1e-9))
    return {'projected_downward_area_mm2':area,'weighted_height_mm':height,'score':area*(1+height/35)}

NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',NS)
def plate_file(path,meshes):
    root=ET.Element(f'{{{NS}}}model',{'unit':'millimeter'});resources=ET.SubElement(root,'resources');build=ET.SubElement(root,'build')
    ET.SubElement(root,'metadata',{'name':'Title'}).text='Tinfox thigh — unsliced part and removable exterior support'
    for i,(name,mesh) in enumerate(meshes,1):
        obj=ET.SubElement(resources,'object',{'id':str(i),'type':'model','name':name});mm=ET.SubElement(obj,'mesh')
        vv=ET.SubElement(mm,'vertices');ff=ET.SubElement(mm,'triangles')
        for v in mesh.vertices:ET.SubElement(vv,'vertex',dict(zip(['x','y','z'],[f'{x:.5f}' for x in v])))
        for face in mesh.faces:ET.SubElement(ff,'triangle',dict(zip(['v1','v2','v3'],map(str,face))))
        ET.SubElement(build,'item',{'objectid':str(i)})
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))

def exterior_supports(part):
    # Samples the first surface above the bed. Internal bridges are deliberately
    # excluded; this is an accessible exterior support starting point only.
    lo,hi=part.bounds
    xy=np.array([(x,y) for x in np.arange(lo[0]+3,hi[0]-2,7) for y in np.arange(lo[1]+3,hi[1]-2,7)])
    offsets=np.array([[0,0]]+[[1.3*math.cos(a),1.3*math.sin(a)] for a in np.linspace(0,2*math.pi,8,endpoint=False)])
    positions=(xy[:,None,:]+offsets[None,:,:]).reshape(-1,2)
    origins=np.column_stack((positions,np.full(len(positions),-1.)))
    locations,rays,_=part.ray.intersects_location(origins,np.tile([0,0,1.],(len(origins),1)),multiple_hits=False)
    heights=np.full(len(origins),np.inf);heights[rays]=locations[:,2]
    heights=heights.reshape(len(xy),len(offsets))
    manager=trimesh.collision.CollisionManager();manager.add_object('finished_part',part)
    chunks=[];minimum=float('inf');accepted=0
    for center,row in zip(xy,heights):
        if not np.isfinite(row).all():continue
        top=math.floor((min(row)-.4)/.2)*.2
        if top<1:continue
        for attempt in range(8):
            tip=min(.8,top/2);stem=trimesh.creation.cylinder(radius=1.2,height=top-tip,sections=12)
            stem.apply_translation([*center,(top-tip)/2])
            taper=trimesh.creation.cone(radius=1.2,height=tip,sections=12)
            taper.apply_translation([*center,top-tip])
            post=trimesh.util.concatenate([stem,taper])
            gap=float(manager.min_distance_single(post))
            if not manager.in_collision_single(post) and gap>=.35:break
            top-=.2
        else:continue
        minimum=min(minimum,gap);chunks.append(post);accepted+=1
    assert accepted>20
    raft=trimesh.creation.box(extents=[hi[0]-lo[0]+6,hi[1]-lo[1]+6,.6])
    raft.apply_translation([(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,.3]);chunks.append(raft)
    result=trimesh.util.concatenate(chunks)
    assert not manager.in_collision_single(result)
    return result,{'exterior_posts':accepted,'minimum_rigid_gap_mm':min(minimum,float(manager.min_distance_single(raft))),
        'nominal_vertical_gap_mm':.4,'minimum_required_rigid_gap_mm':.35,
        'sampling_grid_mm':7,'layer_quantization_mm':.2,
        'scope':'Exterior support starting point. Internal bridges and unsupported regions between samples require slicer review. Supports are removed after printing.'}

parts=[]
for outer in [False,True]:
    key='thigh_'+('outer' if outer else 'inner');base_angle=-90 if outer else 90
    mesh=clean_mesh(trimesh.load_mesh(OUT/'stl'/(key+'.stl')))
    before=clean_mesh(trimesh.load_mesh(BASE/'stl'/(key+'.stl')))
    options=[]
    for tilt in ([-4,-2,0,2,4] if outer else [-18,-12,-6,0,6]):
        trial,transform=orient(mesh,base_angle+tilt);screen=metric(trial)
        options.append((screen['score'],trial,transform,tilt,screen))
    _,chosen,transform,tilt,screen=min(options,key=lambda x:x[0]);baseline,_=orient(before,base_angle)
    assert np.all(chosen.extents<np.array([305,300,315]))
    assert chosen.is_watertight and abs(chosen.volume-mesh.volume)<.01
    for right in [False,True]:
        name=key+('_right' if right else '');source=clean_mesh(trimesh.load_mesh(OUT/'stl'/(name+'.stl')))
        if right:
            oriented,m=orient(source,-(base_angle+tilt))
        else:m=transform;oriented=chosen
        assert abs(np.linalg.det(m[:3,:3])-1)<1e-9
        oriented.export(OUT/'print-stl'/(name+'.stl'))
        assert oriented.is_watertight and abs(oriented.volume-source.volume)<.01
        parts.append({'part':name,'transform':m.tolist(),'print_bounds_mm':oriented.extents.tolist(),
            'oriented_stl':'print-stl/'+name+'.stl','tilt_from_length_parallel_to_bed_deg':tilt,
            'downward_face_screen':screen,'previous_geometry_untilted_screen':metric(baseline),
            'scope':'Nominal orientation screen; projected area and height are proxies, not sliced support volume or structural qualification.'})
    plate=chosen.copy();plate.apply_translation([10,10,2.4])
    supports,report=exterior_supports(plate)
    assert np.all(supports.bounds[0]>=0) and np.all(supports.bounds[1]<[325,320,325])
    file=OUT/'print-preparation'/(key+'.3mf');plate_file(file,[(key,plate),('removable_exterior_support',supports)])
    with zipfile.ZipFile(file) as z:assert z.testzip() is None
    reopened=trimesh.load(file,force='scene');assert len(reopened.graph.nodes_geometry)==2
    preview={'part':{'vertices':plate.vertices.tolist(),'faces':plate.faces.tolist()},
        'supports':{'vertices':supports.vertices.tolist(),'faces':supports.faces.tolist()}}
    (OUT/'print-preparation'/(key+'.json')).write_text(json.dumps(preview,separators=(',',':')))
    for record in parts:
        if record['part']==key:record.update(support_preparation=report,plate='print-preparation/'+key+'.3mf')
    print('Print preparation',key,tilt,report['exterior_posts'],flush=True)

tool_checks=[]
new=cq.importers.importStep(str(OUT/'step/thigh_outer.step')).val()
old=cq.importers.importStep(str(BASE/'step/thigh_outer.step')).val()
for angle in range(0,360,60):
    is_slim='slim_rear_clamp_xz_mm' in model['parameters']
    x,z=model['parameters'].get('slim_rear_clamp_xz_mm',[-38,-70])
    a=math.radians(angle);r=7.2/math.sqrt(3)-(.5 if is_slim else 0)
    cutter=b.cyl(1.5,30,(x+r*math.cos(a),76,z+r*math.sin(a)))
    new_volume=max(0,sum(s.Volume() for s in new.intersect(cutter).Solids()))
    old_volume=max(0,sum(s.Volume() for s in old.intersect(cutter).Solids()))
    tool_checks.append({'nut_corner_deg':angle,'axial_cutter_overlap_mm3':new_volume,
        'previous_overlap_mm3':old_volume,'passed':new_volume<.001})
report={'model_sha256':stamp,'parts':parts,'tool_checks':tool_checks,
    'tool_diameter_mm':3,
    'scope':'Accessible corner-relief cutters checked as ideal cylinders. Full cutter paths, holder clearance, workholding forces and CNC quotes remain unqualified. 3MF files contain unsliced part and removable exterior support meshes.'}
(OUT/'manufacturing-review.json').write_text(json.dumps(report,indent=2))
assert all(r['passed'] for r in tool_checks)
print('Manufacturing preparation ready',len(parts),'orientations and',len(tool_checks),'corner cutters',flush=True)
