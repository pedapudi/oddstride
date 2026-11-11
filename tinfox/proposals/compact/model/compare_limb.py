"""Compare current limb geometry with the preserved preceding CAD revision."""
import json,hashlib
import numpy as np
import trimesh,fcl
from kinematics import ROOT,POSES,matrix,frames

OUT=ROOT/'output'
before=json.loads((ROOT.parent/'analysis/07-limb-baseline.json').read_text())
after=json.loads((OUT/'model.json').read_text())
poses={leg:[0,45,-75] for leg in POSES['stand']}

def mesh_for(model,p):
    m=model['meshes'][p['mesh']]
    return trimesh.Trimesh(vertices=m['vertices'],faces=m['faces'],process=False)

def inertia(model,parts,joint,pose):
    f=frames('FL',pose['FL'])[joint];axis=f[:3,1];origin=f[:3,3];total=0.
    for p in parts:
        mesh=mesh_for(model,p);mass=p['mass_kg'];t=matrix(p,pose);r=t[:3,:3]
        ic=mesh.moment_inertia*(mass/mesh.volume)
        center=r@mesh.center_mass+t[:3,3];d=center-origin
        total+=float(axis@(r@ic@r.T)@axis+mass*(d@d-(axis@d)**2))/1e6
    return total

def metrics(model):
    leg=[p for p in model['parts'] if p['leg']=='FL' and p['group'] in ['thigh','crank','rod','knee']]
    shin=[p for p in leg if p['name'] in ['FL_shin_inner','FL_shin_outer']]
    distal=[p for p in leg if p['group']=='knee']
    thigh=[p for p in leg if p['name'].endswith(('_thigh_inner','_thigh_outer','_knee_transition_inset'))]
    report={}
    for name,items in [('printed_shin_pair',shin),('printed_thigh_pair_and_finish',thigh),('distal_knee_assembly',distal),('moving_leg',leg)]:
        report[name]={'mass_kg':sum(p['mass_kg'] for p in items),'hip_pitch_inertia_stand_kg_m2':inertia(model,items,'thigh',POSES['stand'])}
        if name in ['printed_shin_pair','distal_knee_assembly']:
            report[name]['knee_pitch_inertia_kg_m2']=inertia(model,items,'knee',POSES['stand'])
    manager=trimesh.collision.CollisionManager()
    names=['FL_thigh_inner','FL_thigh_outer','FL_shin_inner','FL_shin_outer']
    lookup={p['name']:p for p in model['parts']}
    for name in names:manager.add_object(name,mesh_for(model,lookup[name]))
    gaps={}
    for pose in ['crouch','fold']:
        for name in names:manager.set_transform(name,matrix(lookup[name],POSES[pose]))
        distances=[]
        for a in names[:2]:
            for b in names[2:]:
                distance=fcl.distance(manager._objs[a]['obj'],manager._objs[b]['obj'])
                distances.append({'parts':[a,b],'distance_mm':float(distance)})
        gaps[pose]=min(distances,key=lambda x:x['distance_mm'])
    report['thigh_shin_paired_gaps']=gaps
    return report

def thigh_sections(model):
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    from shapely.geometry.polygon import orient
    parts=[p for p in model['parts'] if p['name'] in ['FL_thigh_inner','FL_thigh_outer']]
    meshes=[mesh_for(model,p) for p in parts];rows=[]
    for z in range(-70,-151,-10):
        shapes=[]
        for mesh in meshes:
            section=mesh.section(plane_origin=[0,0,z],plane_normal=[0,0,1])
            combined=Polygon()
            for loop in section.discrete:
                polygon=Polygon(loop[:,:2])
                if polygon.area>1e-7:combined=combined.symmetric_difference(polygon)
            shapes.append(combined)
        shape=unary_union(shapes)
        polys=list(shape.geoms) if hasattr(shape,'geoms') else [shape]
        area=sx=iy=0.
        for polygon in polys:
            polygon=orient(polygon,sign=1)
            for ring in [polygon.exterior,*polygon.interiors]:
                points=np.array(ring.coords);a=points[:-1];b=points[1:]
                cross=a[:,0]*b[:,1]-b[:,0]*a[:,1]
                area+=float(cross.sum())/2
                sx+=float(((a[:,0]+b[:,0])*cross).sum())/6
                iy+=float(((a[:,0]**2+a[:,0]*b[:,0]+b[:,0]**2)*cross).sum())/12
        center=sx/area;iy-=area*center**2
        modulus=iy/max(shape.bounds[2]-center,center-shape.bounds[0])
        rows.append({'z_mm':z,'area_mm2':area,'section_modulus_y_mm3':modulus})
    return {'minimum_section_modulus_y_mm3':min(r['section_modulus_y_mm3'] for r in rows),'samples':rows,
            'scope':'Combined printed thigh halves, tessellated XY sections every 10 mm from z=-70 to -150; values exclude proximal cradle and knee seat. This geometric section comparison omits local stress, fastener load paths, anisotropy and fatigue.'}

old=metrics(before);new=metrics(after)
deltas={}
for group in ['printed_shin_pair','printed_thigh_pair_and_finish','distal_knee_assembly','moving_leg']:
    deltas[group]={k:{'absolute':new[group][k]-v,'percent':100*(new[group][k]/v-1)} for k,v in old[group].items()}
engineering=json.loads((OUT/'engineering.json').read_text());audit=json.loads((OUT/'mounting-audit.json').read_text())
result={'model_sha256':hashlib.sha256((OUT/'model.json').read_bytes()).hexdigest(),'baseline_model_sha256':before['model_sha256'],'before':old,'after':new,'delta':deltas,'thigh_section_comparison':{'before':thigh_sections(before),'after':thigh_sections(after)},
        'section_modulus_y_mm3':{'before':before['audit']['minimum_shin_section_modulus_y_mm3'],'after':audit['minimum_shin_section_modulus_y_mm3']},
        'base_mass_kg':{'before':before['engineering']['mass']['base_kg'],'after':engineering['mass']['base_kg']},
        'scope':'Per front-left limb. Nominal CAD masses; tessellated mass moments are scaled to CAD mass. Hip-pitch inertia uses the standing pose; knee-pitch inertia is about the knee axis. These are comparisons of this geometry revision, not proof of an optimal design, material strength or dynamic capability.'}
assert engineering['model_sha256']==audit['model_sha256']==result['model_sha256']
result['comparison_summary']={
 'moving_leg_mass_delta_g':1000*deltas['moving_leg']['mass_kg']['absolute'],
 'hip_pitch_inertia_change_percent':deltas['moving_leg']['hip_pitch_inertia_stand_kg_m2']['percent'],
 'knee_pitch_inertia_change_percent':deltas['distal_knee_assembly']['knee_pitch_inertia_kg_m2']['percent'],
 'shin_section_modulus_change_percent':100*(result['section_modulus_y_mm3']['after']/result['section_modulus_y_mm3']['before']-1),
 'thigh_section_modulus_change_percent':100*(result['thigh_section_comparison']['after']['minimum_section_modulus_y_mm3']/result['thigh_section_comparison']['before']['minimum_section_modulus_y_mm3']-1),
 'fold_min_thigh_shin_gap_mm_before':old['thigh_shin_paired_gaps']['fold']['distance_mm'],
 'fold_min_thigh_shin_gap_mm_after':new['thigh_shin_paired_gaps']['fold']['distance_mm'],
 'scope':'Front-left moving leg mass and hip-pitch inertia in nominal stand; complete distal knee assembly inertia about knee pitch. Fold gaps are the minimum across the four printed thigh/shin pairings in the prescribed fold pose.'}
thigh_moment=max(abs(v['joint_Nm'][1]) for v in engineering['torque_cases'])
shin_moment=max(abs(v['joint_Nm'][2]) for v in engineering['torque_cases'])
thigh_modulus=result['thigh_section_comparison']['after']['minimum_section_modulus_y_mm3']
shin_modulus=result['section_modulus_y_mm3']['after']
thigh_stress=1000*thigh_moment/thigh_modulus;shin_stress=1000*shin_moment/shin_modulus
result['nominal_sagittal_bending_screen']={
 'thigh':{'maximum_hip_pitch_joint_moment_Nm':thigh_moment,'minimum_sampled_section_modulus_y_mm3':thigh_modulus,'nominal_M_over_W_MPa':thigh_stress},
 'shin':{'maximum_knee_pitch_joint_moment_Nm':shin_moment,'minimum_sampled_section_modulus_y_mm3':shin_modulus,'nominal_M_over_W_MPa':shin_stress},
 'thigh_to_shin_nominal_stress_ratio':thigh_stress/shin_stress,
 'scope':'Uniform maximum prescribed sagittal joint moment divided by minimum sampled section modulus about local transverse Y. Thigh uses tessellated sections; shin uses CAD solid sections. Includes combined halves but omits shear transfer, local stress concentration, hip-roll/frontal loading, torsion, fasteners, material anisotropy, fatigue and creep. It is a comparison screen, not a structural qualification or material allowable.'}
(OUT/'limb-profile-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

# Actual projected triangle unions preserve concave outlines in the side view.
from shapely.geometry import Polygon
from shapely.ops import unary_union

def silhouette(model,name):
    p=next(p for p in model['parts'] if p['name']==name);mesh=mesh_for(model,p)
    transform=matrix(p,poses);vertices=mesh.vertices@transform[:3,:3].T+transform[:3,3]
    xy=np.column_stack([vertices[:,0]-frames('FL',poses['FL'])['thigh'][0,3],-vertices[:,2]])
    polygons=[Polygon(xy[t]) for t in mesh.faces if abs((xy[t[1],0]-xy[t[0],0])*(xy[t[2],1]-xy[t[0],1])-(xy[t[1],1]-xy[t[0],1])*(xy[t[2],0]-xy[t[0],0]))>1e-6]
    return unary_union(polygons)

def path(shape):
    polys=list(shape.geoms) if hasattr(shape,'geoms') else [shape]
    out=[]
    for poly in polys:
        for ring in [poly.exterior,*poly.interiors]:
            pts=list(ring.coords);out.append('M'+' L'.join(f'{x:.2f},{y:.2f}' for x,y in pts)+' Z')
    return ' '.join(out)
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="690" viewBox="0 0 1000 690"><rect width="1000" height="690" fill="#f0eee8"/><style>text{font-family:Arial,sans-serif;fill:#242927}</style><text x="35" y="42" font-size="24">Tinfox · limb profile comparison</text><text x="35" y="70" font-size="14">Projected CAD silhouettes · identical joint centers and comparison pose</text>']
for x,title,model in [(300,'Previous compound curve',before),(780,'Current shallow sweep',after)]:
    svg.append(f'<text x="{x-235}" y="108" font-size="18">{title}</text><g transform="translate({x},205) scale(1.35)">')
    for name,color in [('FL_pushrod','#9c9f98'),('FL_shin_outer','#323935'),('FL_foot','#1b211e'),('FL_thigh_outer','#d5d2c8'),('FL_hip_disc','#b5b7b0'),('FL_knee_bezel','#353c38'),('FL_knee_end_cap','#aeb2aa')]:
        svg.append(f'<path d="{path(silhouette(model,name))}" fill="{color}" stroke="#4b514c" stroke-width=".5" fill-rule="evenodd"/>')
    svg.append('</g>')
svg.append('<text x="35" y="655" font-size="14">170 mm links · proximal knee actuator · fixed bearing and contact centers · strength remains unqualified</text></svg>')
(ROOT.parent/'design/14-limb-profile.svg').write_text(''.join(svg))
