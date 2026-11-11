"""Check installed fasteners against the moving rod and measure CAD shin sections."""
import json,hashlib
import numpy as np
import cadquery as cq
import trimesh
from kinematics import ROOT,P,POSES,LEGS,matrix

data=json.loads((ROOT/'output/model.json').read_text())
parts=[p for p in data['parts'] if p['leg']=='FL' and (p['name'].endswith('_pushrod') or any(t in p['name'] for t in ['_bolt_','_sleeve_','_pod_tie_','_knee_axle','_knee_inner_spacer','_input_pin','_output_pin','_input_crank','_shin_inner','_shin_outer']))]
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
for z in range(-35,int(np.ceil(s.BoundingBox().zmin)),-5):
 slab=cq.Workplane('XY').box(200,200,.2).val().translate((0,60,z));cut=s.intersect(slab)
 if cut.Volume()<1:raise RuntimeError('Missing shin section')
 inertia=cq.Shape.matrixOfInertia(cut);b=cut.BoundingBox();c=cut.Center()
 iy=inertia[1][1]/.2-cut.Volume()/.2*.2**2/12
 section_modulus=iy/max(abs(b.xmin-c.x),abs(b.xmax-c.x))
 sections.append({'z_mm':z,'area_mm2':cut.Volume()/.2,'Iy_mm4':iy,'Ix_mm4':inertia[0][0]/.2-cut.Volume()/.2*.2**2/12,'section_modulus_y_mm3':section_modulus})
# Measure transverse material remaining beneath the curved groove at lower-cavity stations.
inner=cq.importers.importStep(str(ROOT/'output/step-parts/shin_inner.step')).val()
wall_samples=[]
for z in [-85,-95,-105,-115]:
    t=-z/P['shank_to_foot_center'];x=14*t*(1-t)-3.5
    probe=cq.Workplane('XY').box(.02,90,.02).val().translate((x,67,z))
    cut=inner.intersect(probe)
    spans=[piece.BoundingBox().ylen for piece in cut.Solids()]
    if not spans:raise RuntimeError('Missing outer shin wall')
    wall_samples.append({'x_mm':x,'z_mm':z,'transverse_wall_mm':min(spans)})
thigh_sections=[]
thigh=cq.importers.importStep(str(ROOT/'output/step-parts/thigh_inner.step')).val().fuse(cq.importers.importStep(str(ROOT/'output/step-parts/thigh_outer.step')).val())
for z in range(-65,-156,-5):
    probe=cq.Workplane('XY').box(200,200,.2).val().translate((0,60,z))
    cut=thigh.intersect(probe);bounds=cut.BoundingBox();center=cut.Center()
    inertia=cq.Shape.matrixOfInertia(cut)
    iy=inertia[1][1]/.2-cut.Volume()/.2*.2**2/12
    thigh_sections.append({'z_mm':z,'section_modulus_y_mm3':iy/max(abs(bounds.xmin-center.x),abs(bounds.xmax-center.x))})
report={'model_sha256':hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest(),'thigh_sections':thigh_sections,'minimum_thigh_section_modulus_y_mm3':min(v['section_modulus_y_mm3'] for v in thigh_sections),'groove_wall_samples':wall_samples,'minimum_sampled_groove_wall_mm':min(v['transverse_wall_mm'] for v in wall_samples),'rod_hardware_sweep':{'knee_range_deg':P['joint_limits_deg']['knee'],'step_deg':1,'collisions':hits},'shin_sections':sections,'minimum_shin_section_modulus_y_mm3':min(s['section_modulus_y_mm3'] for s in sections),'scope':'Nominal rod versus modeled fastening hardware at one-degree increments. Shin sections are 0.2 mm CAD slices at 5 mm intervals, measured about their centroids; no local stress, anisotropy, fatigue or torsion qualification.'}
(ROOT/'output/mounting-audit.json').write_text(json.dumps(report,indent=2))
print('Rod/hardware collision samples:',len(hits),'minimum section modulus:',report['minimum_shin_section_modulus_y_mm3'],flush=True)
if hits:print(hits[:3])
