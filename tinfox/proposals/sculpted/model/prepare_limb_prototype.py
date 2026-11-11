"""Prepare one front-left fit prototype and a bearing-coupon plate."""
import hashlib,json,shutil,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
import trimesh
import cadquery as cq
from kinematics import ROOT
from cad_authority import require_generated_authority
require_generated_authority(ROOT)
import build as b
from mesh_cleanup import clean_mesh

OUT=ROOT/'output/paired-roll-work'
PACK=OUT/'prototype-limb'
for folder in ['print-stl','print-3mf','coupons','reference-step']:(PACK/folder).mkdir(parents=True,exist_ok=True)
raw=(OUT/'model.json').read_bytes();model=json.loads(raw);stamp=hashlib.sha256(raw).hexdigest()
rows=[]

def orient(mesh,axis,angle):
    m=mesh.copy();v=np.array(axis);m.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(angle),v))
    bb=m.bounds;m.apply_translation([-(bb[0,0]+bb[1,0])/2,-(bb[0,1]+bb[1,1])/2,-bb[0,2]])
    return m

def write_3mf(file,items):
    ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns)
    root=ET.Element('{'+ns+'}model',unit='millimeter',attrib={'xml:lang':'en-US'})
    resources=ET.SubElement(root,'resources');build=ET.SubElement(root,'build')
    for i,(name,m) in enumerate(items,1):
        obj=ET.SubElement(resources,'object',id=str(i),type='model',name=name)
        mesh=ET.SubElement(obj,'mesh');vv=ET.SubElement(mesh,'vertices');ff=ET.SubElement(mesh,'triangles')
        for v in m.vertices:ET.SubElement(vv,'vertex',x=f'{v[0]:.6f}',y=f'{v[1]:.6f}',z=f'{v[2]:.6f}')
        for f in m.faces:ET.SubElement(ff,'triangle',v1=str(f[0]),v2=str(f[1]),v3=str(f[2]))
        ET.SubElement(build,'item',objectid=str(i))
    types='<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
    rels='<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    with zipfile.ZipFile(file,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',types);z.writestr('_rels/.rels',rels)
        z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))

keys=['thigh_inner','thigh_outer','shin_inner','shin_outer','motor_carrier_1','hip_stator_closure_1',
      'roll_cartridge_1','roll_stator_backplate_1','roll_outer_retainer_1','roll_inner_backplate_1','roll_inner_spacer_1','roll_outer_spacer_1',
      'hip_hub','motor_mount_ring','input_crank','pushrod']
for key in keys:
    r=next(p for p in model['parts'] if p['leg']=='FL' and p['mesh']==key)
    mesh=clean_mesh(trimesh.Trimesh(**{k:np.array(v) for k,v in model['meshes'][key].items()},process=False))
    if key in ['thigh_outer','shin_outer']:axis,angle=(1,0,0),-90
    elif key.startswith('roll_'):axis,angle=(0,1,0),-90
    else:axis,angle=(1,0,0),90
    mesh=orient(mesh,axis,angle)
    assert mesh.is_watertight and mesh.is_winding_consistent,key
    assert np.all(mesh.extents<np.array([305,300,305])),(key,mesh.extents)
    mesh.export(PACK/'print-stl'/(key+'.stl'))
    onbed=mesh.copy();onbed.apply_translation([162.5,160,0])
    write_3mf(PACK/'print-3mf'/(key+'.3mf'),[(key,onbed)])
    file=OUT/'step'/(key+'.step')
    if file.exists():shutil.copy2(file,PACK/'reference-step'/file.name)
    rows.append(dict(part=key,quantity=1,print_stl='print-stl/'+key+'.stl',print_3mf='print-3mf/'+key+'.3mf',
        stl_sha256=hashlib.sha256((PACK/'print-stl'/(key+'.stl')).read_bytes()).hexdigest(),
        three_mf_sha256=hashlib.sha256((PACK/'print-3mf'/(key+'.3mf')).read_bytes()).hexdigest(),
        oriented_bounds_mm=mesh.extents.tolist(),rotation_axis=list(axis),rotation_deg=angle,
        process='Printed fit prototype only' if r['material']=='aluminum' or key=='pushrod' else 'Structural-shell fit print; loaded use unqualified',
        support_note='Support the horizontal roll journal and inspect the three open nut approaches; keep support removable through the open motor cup.' if key=='motor_carrier_1' else 'Inspect curved bed contact and local bridges in the slicer. Keep support out of bearing seats and use removable exterior support where needed.'))
for key in ['knee_axle','knee_inner_spacer','sleeve_0','sleeve_1','shin_clamp_sleeve_37','shin_clamp_sleeve_105','pod_sleeve_90','pod_sleeve_210','pod_sleeve_330']:
    file=OUT/'step'/(key+'.step')
    if file.exists():shutil.copy2(file,PACK/'reference-step'/file.name)

coupons=[]
for family,diameters,outer,inner in [
    ('6810-seat',[65.05,65.15,65.25],73,None),
    ('6810-journal',[49.80,49.90,50.00],None,44),
    ('6001-seat',[28.00,28.10,28.20],38,None)]:
    for index,d in enumerate(diameters):
        s=b.ring((outer or d)/2,(inner or d)/2,8.5)
        vv,ff=s.tessellate(.04,.08)
        m=trimesh.Trimesh(vertices=[v.toTuple() for v in vv],faces=ff,process=True)
        # Match the carrier's horizontal journal axis; vertical seat coupons
        # alone cannot characterize support scars on this perpendicular seat.
        m=orient(m,(0,0,1),90) if family=='6810-journal' else orient(m,(1,0,0),90)
        name=family+'-'+f'{d:.2f}'.replace('.','p')
        m.export(PACK/'coupons'/(name+'.stl'))
        positioned=m.copy();positioned.apply_translation([162.5+85*(index-1),160+{'6810-seat':-80,'6810-journal':5,'6001-seat':75}[family],0])
        coupons.append((name,positioned))
write_3mf(PACK/'bearing-fit-coupons.3mf',coupons)
manifest=dict(model_sha256=stamp,limb='front-left',units='mm',parts=rows,
    coupon_count=len(coupons),coupons=[n for n,_ in coupons],
    status='Unpowered fit prototype. No loaded or powered release.',
    print_volume_mm=[325,320,325],bed_margin_mm=10,
    scope='Oriented closed meshes and generic unsliced 3MF files. Printer/material/support settings and layer previews must be chosen in the slicer. Thin precision spacers/backplate are fit surrogates; operating material and tolerances need qualification.')
(PACK/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('Prepared',len(rows),'parts and',len(coupons),'coupons for',stamp,flush=True)
