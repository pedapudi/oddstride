"""Render the exported CAD meshes without replacing or inventing geometry.

Run in a Python environment containing bpy. The manifest binds the image to CAD.
"""
import sys,json,math,hashlib
from pathlib import Path
import bpy
from mathutils import Matrix,Vector
sys.path.insert(0,'/home/sunil/git/oddstride/tinfox/model')
from kinematics import ROOT,matrix
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
data=json.loads((ROOT/'output/model.json').read_text())
render_pose={leg:[0,45,-75] for leg in data['poses']['stand']}
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=64
scene.cycles.use_denoising=True
scene.render.resolution_x=1536;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.8,.82,.85,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.08
scene.view_settings.view_transform='AgX'
materials={}
def material(name,hexcolor,metal=0,rough=.4):
    if name in materials:return materials[name]
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    rgb=[int(hexcolor[i:i+2],16)/255 for i in (1,3,5)]
    rgb=[((v+.055)/1.055)**2.4 if v>.04045 else v/12.92 for v in rgb]
    bs.inputs['Base Color'].default_value=(*rgb,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
    materials[name]=m;return m
low=0
for part in data['parts']:
    m=data['meshes'][part['mesh']];mesh=bpy.data.meshes.new(part['mesh'])
    mesh.from_pydata([[x/1000 for x in v] for v in m['vertices']],[],m['faces']);mesh.update()
    obj=bpy.data.objects.new(part['name'],mesh);scene.collection.objects.link(obj)
    transform=matrix(part,render_pose);transform[:3,3]/=1000;obj.matrix_world=Matrix(transform.tolist())
    metal=part['material'] in ['steel','aluminum']
    mat=material(part['color']+part['material'],part['color'],.72 if metal else .03,.24 if metal else .34)
    obj.data.materials.append(mat)
    # Preserve CAD creases while smoothing tessellated analytic surfaces.
    for poly in mesh.polygons:poly.use_smooth=True
    mod=obj.modifiers.new('CAD surface normals','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=30
    for v in mesh.vertices:low=min(low,(obj.matrix_world@v.co).z)
# A soft warm cyclorama and studio lamps are presentation-only geometry.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,low-.001))
floor=bpy.context.object;floor.name='studio_floor';floor.data.materials.append(material('floor','#c4c1b8',0,.8))
def area(name,pos,power,size,color):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,-.1))-o.location).to_track_quat('-Z','Y').to_euler()
area('key',(.2,-.65,1.1),45,.65,(1,.94,.84))
area('fill',(.8,.6,.5),8,.8,(.86,.94,1))
area('rim',(-.7,.3,.8),50,.55,(1,1,.95))
d=bpy.data.cameras.new('Studio camera');cam=bpy.data.objects.new('Studio camera',d);scene.collection.objects.link(cam)
cam.location=(.55,-1.5,.25);target=Vector((0,0,-.105));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=.78;scene.camera=cam
path=ROOT.parent/'proposals/baseline-studio-view.png'
scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
(ROOT.parent/'proposals/baseline-studio-view-provenance.json').write_text(json.dumps({'image':str(path.relative_to(ROOT.parent)),'model_sha256':hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest(),'method':'Blender Cycles rendering of exported CAD meshes; studio floor, lights and camera are presentation only.','script':'proposals/render_baseline.py','camera':{'position':[.55,-1.5,.25],'target':[0,0,-.105],'ortho_scale':.78},'pose':render_pose},indent=2))
print(path)
