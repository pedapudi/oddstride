"""Compare projected CAD limbs and approximate moving inertias at fixed poses."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
import trimesh
sys.path.insert(0,str(Path(__file__).resolve().parent/'.cache/profile-deps'))
from shapely.geometry import Polygon
from shapely.ops import unary_union
from kinematics import ROOT,P,POSES,frames,matrix

baseline=ROOT.parent/'design/iterations/refinement-baseline'
old=json.loads((baseline/'model.json').read_text())
old['model_sha256']=hashlib.sha256((baseline/'model.json').read_bytes()).hexdigest()
old['engineering']=json.loads((baseline/'engineering.json').read_text())
new=json.loads((ROOT/'output/model.json').read_text())
current_hash=hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest()
GROUPS=['thigh','knee','crank','rod']

def moving(data,groups):
    return [p for p in data['parts'] if p['leg']=='FL' and p['group'] in groups]

def metrics(data):
    poses={leg:[0,30,-60] for leg in ['FL','FR','RL','RR']}
    f=frames('FL',poses['FL'])
    result={}
    for label,groups,frame in [('hip_pitch',GROUPS,'thigh'),('knee',['knee'],'knee')]:
        origin=f[frame][:3,3];axis=f[frame][:3,1];mass=0;inertia=0
        for p in moving(data,groups):
            geom=data['meshes'][p['mesh']]
            mesh=trimesh.Trimesh(vertices=geom['vertices'],faces=geom['faces'],process=False)
            props=mesh.mass_properties
            if not props.mass or not p['mass_kg']:continue
            t=matrix(p,poses);rot=t[:3,:3]
            local=props.inertia*p['mass_kg']/props.mass
            com=rot@np.asarray(p['com_mm'])+t[:3,3]
            r=com-origin
            tensor=rot@local@rot.T+p['mass_kg']*((r@r)*np.eye(3)-np.outer(r,r))
            inertia+=float(axis@tensor@axis)*1e-6;mass+=p['mass_kg']
        result[label]={'moving_mass_kg':mass,'inertia_about_axis_kg_m2':inertia}
    return result

def folded_thigh_shin_gap(data):
    poses={leg:[0,77,-154] for leg in ['FL','FR','RL','RR']}
    managers=[trimesh.collision.CollisionManager(),trimesh.collision.CollisionManager()]
    for p in data['parts']:
        if p['leg']!='FL':continue
        if p['name'] in ['FL_thigh_inner','FL_thigh_outer']:index=0
        elif p['name'] in ['FL_shin_inner','FL_shin_outer','FL_shin_shell']:index=1
        else:continue
        geom=data['meshes'][p['mesh']]
        mesh=trimesh.Trimesh(vertices=geom['vertices'],faces=geom['faces'],process=False)
        managers[index].add_object(p['name'],mesh,matrix(p,poses))
    return float(managers[0].min_distance_other(managers[1]))

def silhouette(data,q):
    poses={leg:q for leg in ['FL','FR','RL','RR']};hip=frames('FL',q)['thigh'][:3,3]
    triangles=[]
    for p in moving(data,GROUPS):
        geom=data['meshes'][p['mesh']];v=np.asarray(geom['vertices']);t=matrix(p,poses)
        v=v@t[:3,:3].T+t[:3,3]-hip
        for face in geom['faces']:
            poly=Polygon([(float(v[i,0]),float(-v[i,2])) for i in face])
            if poly.area>1e-7:triangles.append(poly)
    return unary_union(triangles).simplify(.05,preserve_topology=True)

def svg_path(geom,color,opacity,ox,oy,scale):
    paths=[]
    polygons=list(geom.geoms) if geom.geom_type=='MultiPolygon' else [geom]
    for poly in polygons:
        for ring in [poly.exterior,*poly.interiors]:
            paths.append('M'+' L'.join(f'{ox+x*scale:.2f},{oy+y*scale:.2f}' for x,y in ring.coords)+' Z')
    return f'<path d="{" ".join(paths)}" fill="{color}" fill-opacity="{opacity}" fill-rule="evenodd"/>'

svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="800" viewBox="0 0 1100 800">',
'<rect width="1100" height="800" fill="#f5f4ed"/>',
'<g font-family="sans-serif" fill="#28392f"><text x="35" y="40" font-size="26">Whole-limb CAD / profile and articulation</text>',
'<text x="35" y="70" font-size="16">Tan: preceding S-profile limb. Dark green: revised taper and single shallow arc.</text>',
'<text x="35" y="96" font-size="14">Actual mesh silhouettes; hip, knee and foot centers retained. Orange lines join the fixed joint centers.</text></g>']
for title,q,ox,oy,scale in [('Open stance · hip 45° / knee −75°',[0,45,-75],350,220,1.6),('Fold · hip 77° / knee −154°',[0,77,-154],895,310,1.6)]:
    svg.append(f'<text x="{ox-285}" y="140" font-family="sans-serif" font-size="20" fill="#28392f">{title}</text>')
    svg.append(svg_path(silhouette(old,q),'#b5a99b',1,ox,oy,scale))
    svg.append(svg_path(silhouette(new,q),'#294e41',.8,ox,oy,scale))
    f=frames('FL',q);hip=f['thigh'][:3,3];knee=f['knee'][:3,3]-hip
    foot=(f['knee']@np.array([0,P['shin_y'],-P['shank_to_foot_center'],1]))[:3]-hip
    coords=[(ox,oy),(ox+knee[0]*scale,oy-knee[2]*scale),(ox+foot[0]*scale,oy-foot[2]*scale)]
    svg.append('<polyline points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in coords)+'" fill="none" stroke="#e77735" stroke-width="1.5" stroke-dasharray="4 4"/>')
    for x,y in coords:svg.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#f5f4ed" stroke="#e77735" stroke-width="2"/>')
svg.extend(['<g font-family="sans-serif" fill="#28392f"><text x="35" y="735" font-size="15">Projected silhouette does not show transverse gaps or establish loaded mobility.</text>',
'<text x="35" y="764" font-size="13">Mesh triangle unions simplified within 0.05 mm; nominal hinge centers are unchanged. No lighting or camera perspective.</text></g></svg>'])
(ROOT.parent/'design/14-limb-profile.svg').write_text('\n'.join(svg))

import cadquery as cq
baseline_audit=json.loads((baseline/'corrected-section-audit.json').read_text())
baseline_sections=baseline_audit['thigh_sections']

before=metrics(old);after=metrics(new)
report={'previous_model_sha256':old['model_sha256'],'model_sha256':current_hash,'pose_deg':[0,30,-60],
 'before':before,'after':after,'deltas':{},'scope':'One front-left limb. Moving mass uses modeled part masses. Inertia uses tessellated solids scaled to each nominal mass, transformed into a fixed pose and summed about hip-pitch or knee axes. No motor rotor/gear inertia, commanded acceleration, controller or gait model; no claim of globally optimal motion.'}
for label in before:
 report['deltas'][label]={k:after[label][k]-before[label][k] for k in before[label]}
 for k in before[label]:report['deltas'][label][k+'_percent']=100*(after[label][k]/before[label][k]-1)
engineering=json.loads((ROOT/'output/engineering.json').read_text())
if engineering['model_sha256']==current_hash:
 report['base_mass_kg']={'before':old['engineering']['mass']['base_kg'],'after':engineering['mass']['base_kg']}
 report['preset_clearance_mm']={name:{'before':old['engineering']['motion']['presets'][name]['minimum_distance_mm'],'after':value['minimum_distance_mm']} for name,value in engineering['motion']['presets'].items()}
 report['structure']={'before':old['engineering']['structure'],'after':engineering['structure']}
 audit=json.loads((ROOT/'output/mounting-audit.json').read_text())
 baseline_audit=json.loads((baseline/'corrected-section-audit.json').read_text())
 report['minimum_shin_section_modulus_y_mm3']={'before':baseline_audit['minimum_shin_section_modulus_y_mm3'],'after':audit['minimum_shin_section_modulus_y_mm3']}
 report['minimum_sampled_groove_wall_mm']=audit['minimum_sampled_groove_wall_mm']
 report['minimum_thigh_section_modulus_y_mm3']={'before':min(v['section_modulus_y_mm3'] for v in baseline_sections),'after':audit['minimum_thigh_section_modulus_y_mm3']}
 report['thigh_section_samples']={'before':baseline_sections,'after':audit['thigh_sections']}
 thigh_case=max(engineering['torque_cases'],key=lambda row:abs(row['joint_Nm'][1]))
 shin_case=max(engineering['torque_cases'],key=lambda row:abs(row['joint_Nm'][2]))
 report['nominal_bending_screen']={
  'thigh':{'case':thigh_case['case'],'moment_Nm':abs(thigh_case['joint_Nm'][1]),'section_modulus_y_mm3':audit['minimum_thigh_section_modulus_y_mm3'],'nominal_M_over_W_MPa':1000*abs(thigh_case['joint_Nm'][1])/audit['minimum_thigh_section_modulus_y_mm3']},
  'shin':{'case':shin_case['case'],'moment_Nm':abs(shin_case['joint_Nm'][2]),'section_modulus_y_mm3':audit['minimum_shin_section_modulus_y_mm3'],'nominal_M_over_W_MPa':1000*abs(shin_case['joint_Nm'][2])/audit['minimum_shin_section_modulus_y_mm3']},
  'scope':'Sagittal bending about each local pitch Y axis. Each maximum prescribed joint moment is applied uniformly to that member and divided by its smallest sampled section modulus. This compares nominal geometric utilization only under a common material allowable; transmission point forces, distributed loads, holes, torsion, fatigue and print anisotropy are excluded.'}
 report['comparison_summary']={
  'moving_leg_mass_delta_g':1000*report['deltas']['hip_pitch']['moving_mass_kg'],
  'hip_pitch_inertia_change_percent':report['deltas']['hip_pitch']['inertia_about_axis_kg_m2_percent'],
  'knee_pitch_inertia_change_percent':report['deltas']['knee']['inertia_about_axis_kg_m2_percent'],
  'shin_section_modulus_change_percent':100*(audit['minimum_shin_section_modulus_y_mm3']/baseline_audit['minimum_shin_section_modulus_y_mm3']-1),
  'thigh_section_modulus_change_percent':100*(audit['minimum_thigh_section_modulus_y_mm3']/report['minimum_thigh_section_modulus_y_mm3']['before']-1),
  'fold_min_thigh_shin_gap_mm_before':folded_thigh_shin_gap(old),
  'fold_min_thigh_shin_gap_mm_after':folded_thigh_shin_gap(new)}
(ROOT/'output/limb-revision-comparison.json').write_text(json.dumps(report,indent=2))
print('Wrote whole-limb silhouette and mass/inertia comparison.')
