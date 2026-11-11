"""Measure critical attachment sections instead of trusting solid connectivity alone."""
import json,hashlib
import cadquery as cq
from kinematics import ROOT
out=ROOT/'output'
def solid(n):return cq.importers.importStep(str(out/'step-parts'/f'{n}.step')).val()
thigh=solid('thigh_outer');inner=solid('shin_inner');outer=solid('shin_outer')
collar=[]
for y in [60,64,68]:
 probe=cq.Solid.makeCylinder(50,.2,cq.Vector(0,y,0),cq.Vector(0,1,0))
 area=thigh.intersect(probe).Volume()/.2;collar.append({'local_y_mm':y,'section_area_mm2':area});assert area>400,(y,area)
lands=[]
for name,shape in [('shin_inner',inner),('shin_outer',outer)]:
 faces=[f for f in shape.Faces() if f.geomType()=='PLANE' and f.BoundingBox().xlen<1e-5 and abs(f.Center().x)<1e-5]
 area=sum(f.Area() for f in faces);lands.append({'part':name,'split_face_area_mm2':area});assert area>250,(name,area)
 for x,z in ([(15,0)] if name=='shin_outer' else [(-15,0)]):
  probe=cq.Solid.makeCylinder(.02,45,cq.Vector(x,45,z),cq.Vector(0,1,0))
  cut=shape.intersect(probe);segments=[s.BoundingBox().ylen for s in cut.Solids()]
  assert segments and max(segments)>=2.99,(name,x,segments)
root=[]
for name,x in [('body_nose_surround',140.2),('body_aft_0',-140.2)]:
 shape=solid(name);probe=cq.Workplane('XY').box(.2,48,3.4).val().translate((x,0,44.55));area=shape.intersect(probe).Volume()/.2
 root.append({'part':name,'root_x_mm':x,'minimum_sampled_attachment_section_mm2':area});assert area>70,(name,area)
model=json.loads((out/'model.json').read_text());assert not any(p['name'].endswith(('_hip_disc','_hip_index','_knee_end_cap')) for p in model['parts'])
report={'model_sha256':hashlib.sha256((out/'model.json').read_bytes()).hexdigest(),'motor_collar_sections':collar,'shin_mating_lands':lands,'end_cap_attachment_roots':root,'dimensions_mm':{'collar_radial_wall':7.5,'collar_axial_length':20.2,'shin_retaining_shoulders':3,'fork_outer_ear':7.8,'fork_boss_diameter':21,'structural_shin_bearing_wall':5,'end_cap_lap_length':26,'end_cap_rib_width':28,'shin_join_rib_length':16,'integrated_motor_face':3},'scope':'Selected exact-solid sections and mating faces, not a universal wall-thickness search or strength certification. Standard metal hardware retains process-specific thicknesses.'}
(out/'broad-root-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
