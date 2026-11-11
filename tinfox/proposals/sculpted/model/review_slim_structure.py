"""Measure material removal and gross sections without assigning strength allowables."""
import hashlib,json,math,sys
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
import build as b
import slim_limb as design
from mesh_cleanup import clean_mesh
from kinematics import ROOT

OUT=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'output/slim-limb-work'
BASE=design.BASE
raw=(OUT/'model.json').read_bytes();model=json.loads(raw);source=json.loads((BASE/'model.json').read_text())
def props(shape):
    p=GProp_GProps();BRepGProp.VolumePropertiesGK_s(shape.wrapped,p,1e-8,True,True);return p
def part(folder,key):return cq.importers.importStep(str(folder/'step'/(key+'.step'))).val()
def pair(folder):return cq.Compound.makeCompound([part(folder,'thigh_inner'),part(folder,'thigh_outer')])
old,new=pair(BASE),pair(OUT);rows=[]
def section_meshes(folder):return [clean_mesh(trimesh.load_mesh(folder/'stl'/(key+'.stl'))) for key in ['thigh_inner','thigh_outer']]
def section_geometry(meshes,z):
    polygons=[];transform=np.eye(4);transform[2,3]=-z
    for mesh in meshes:
        path=mesh.section(plane_origin=[0,0,z],plane_normal=[0,0,1])
        if path is not None:
            flat,_=path.to_2D(to_2D=transform);polygons.extend(flat.polygons_full)
    result=unary_union(polygons);assert result.is_valid and result.area>0
    cx,cy=result.centroid.coords[0];ix=iy=ixy=0.;boundary=[]
    components=list(result.geoms) if result.geom_type=='MultiPolygon' else [result]
    for poly in components:
        poly=orient(poly,sign=1)
        for ring in [poly.exterior,*poly.interiors]:
            v=np.array(ring.coords)-[cx,cy];a=v[:-1];b=v[1:];cross=a[:,0]*b[:,1]-b[:,0]*a[:,1]
            boundary.extend(v.tolist())
            ix+=float(np.sum((a[:,1]**2+a[:,1]*b[:,1]+b[:,1]**2)*cross)/12)
            iy+=float(np.sum((a[:,0]**2+a[:,0]*b[:,0]+b[:,0]**2)*cross)/12)
            ixy+=float(np.sum((2*a[:,0]*a[:,1]+a[:,0]*b[:,1]+b[:,0]*a[:,1]+2*b[:,0]*b[:,1])*cross)/24)
    x0,y0,x1,y1=result.bounds;sx=ix/max(y1-cy,cy-y0);sy=iy/max(x1-cx,cx-x0)
    return {'area_mm2':result.area,'width_mm':x1-x0,'depth_mm':y1-y0,'Ixx_mm4':ix,'Iyy_mm4':iy,
        'Ixy_mm4':ixy,'centroid_xy_mm':[cx,cy],'boundary_relative_xy_mm':boundary,
        'Sx_mm3':sx,'Sy_mm3':sy,'17Nm_gross_bending_stress_MPa':[17000/sx,17000/sy],
        '34Nm_gross_bending_stress_MPa':[34000/sx,34000/sy]}
old_meshes,new_meshes=section_meshes(BASE),section_meshes(OUT)
for z in range(-45,-161,-5):
    sample=[]
    for meshes in [old_meshes,new_meshes]:sample.append(section_geometry(meshes,z))
    rows.append({'z_mm':z,'source':sample[0],'candidate':sample[1],
        'Ixx_ratio':sample[1]['Ixx_mm4']/sample[0]['Ixx_mm4'],
        'Iyy_ratio':sample[1]['Iyy_mm4']/sample[0]['Iyy_mm4'],
        'Sx_ratio':sample[1]['Sx_mm3']/sample[0]['Sx_mm3'],
        'Sy_ratio':sample[1]['Sy_mm3']/sample[0]['Sy_mm3']})
    print('Section',z,round(sample[0]['depth_mm'],1),'->',round(sample[1]['depth_mm'],1),flush=True)
from kinematics import rotation
import engineering as eng
eng.DATA=model;eng.PARTS=model['parts'];eng.P.update(model['parameters'])
mass=eng.mass_budget()['base_kg'];load_cases=[]
for knee in [-156,-130,-100,-75,-60,-48]:
    phase=math.radians(knee-78);pin=np.array([28*math.cos(phase),70,-170-28*math.sin(phase)])
    center=np.array([0.,69.,-170.])
    for hip in [-10,30,65]:
        for roll in [-25,0,25]:
            transform=(rotation('x',roll)@rotation('y',hip))[:3,:3].T
            foot=rotation('y',knee)[:3,:3]@np.array([0.,67.,-148.])+[0,0,-170]
            foot-=transform@np.array([0.,0.,22.])
            for label,fz in [('loaded_single_support',(mass+1)*9.81),('unloaded_three_g_two_support',mass*9.81*1.5)]:
                for sx,sy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                    ground=transform@np.array([.3*sx*fz,.3*sy*fz,fz])
                    for torque in [-17,17]:
                        rod=np.array([0.,0.,-torque/pin[0]*1000]);force=ground+rod
                        moment=np.cross(foot-center,ground)+np.cross(pin-center,rod);moment[1]=0
                        load_cases.append({'case':label,'hip_deg':hip,'roll_deg':roll,'knee_deg':knee,
                            'motor_torque_Nm':torque,'shaft_force_N':force,'shaft_moment_Nmm':moment})
for row in rows:
    for key in ['source','candidate']:
        section=row[key];cx,cy=section['centroid_xy_mm'];vertices=np.array(section.pop('boundary_relative_xy_mm'))
        tensor=np.array([[section['Iyy_mm4'],section['Ixy_mm4']],[section['Ixy_mm4'],section['Ixx_mm4']]])
        outer_section=section_geometry([(old_meshes if key=='source' else new_meshes)[1]],row['z_mm'])
        first_moment=outer_section['area_mm2']*(np.array(outer_section['centroid_xy_mm'])-[cx,cy])
        maximum=0.;worst=None;max_shear_flow=0.
        for load in load_cases:
            force=load['shaft_force_N'];moment=load['shaft_moment_Nmm']+np.cross(np.array([-cx,69-cy,-170-row['z_mm']]),force)
            gradient=np.linalg.solve(tensor,[-moment[1],moment[0]])
            # Local prismatic-beam estimate of shear transferred between the
            # halves; this is a requirement on the connection, not its capacity.
            shear_gradient=np.linalg.solve(tensor,force[:2])
            max_shear_flow=max(max_shear_flow,abs(float(first_moment@shear_gradient)))
            stress=force[2]/section['area_mm2']+vertices@gradient;peak=float(np.max(np.abs(stress)))
            if peak>maximum:
                maximum=peak;worst={k:v for k,v in load.items() if k not in ['shaft_force_N','shaft_moment_Nmm']}
                worst.update(shaft_force_N=force.tolist(),section_moment_Nmm=moment.tolist())
        section.update(load_envelope_peak_normal_stress_MPa=maximum,double_envelope_required_normal_strength_MPa=2*maximum,
            worst_load=worst,required_seam_shear_flow_N_per_mm=max_shear_flow,
            required_transfer_over_100mm_N=100*max_shear_flow)
def shell_mass(data):return sum(p['mass_kg'] for p in data['parts'] if p['leg']=='FL' and p['mesh'] in ['thigh_inner','thigh_outer'])
def mount_mass(data):return sum(p['mass_kg'] for p in data['parts'] if p['leg']=='FL' and p['mesh'] in ['hip_hub','motor_mount_ring'])
def width(shape):
    vv,_=shape.tessellate(.02,.05);xx=[v.x for v in vv];return max(xx)-min(xx)
material=[];plate=part(OUT,'motor_mount_ring');hub=part(OUT,'hip_hub')
for angle in range(20,380,40):
    a=math.radians(angle);x,z=36.5*math.cos(a),36.5*math.sin(a)
    probe=b.ring(4.0,1.701,3,50.5,z,x)
    fraction=props(plate.intersect(probe)).Mass()/props(probe).Mass()
    material.append({'feature':'stator screw surround','angle_deg':angle,'minimum_required_ligament_mm':2.3,
        'coverage_fraction':fraction,'passed':fraction>.999})
for angle in b.POD_TIE_ANGLES:
    a=math.radians(angle);x,z=design.TIE_RADIUS*math.cos(a),design.TIE_RADIUS*math.sin(a)
    for label,shape,y in [('stator tie',plate,50.5),('hub tie',hub,5)]:
        probe=b.ring(4.5,1.701,3,y,z,x);fraction=props(shape.intersect(probe)).Mass()/props(probe).Mass()
        material.append({'feature':label,'angle_deg':angle,'minimum_required_ligament_mm':2.8,
            'coverage_fraction':fraction,'passed':fraction>.999})
assert all(r['passed'] for r in material),[r for r in material if not r['passed']]
root_widths=[width(shape.intersect(b.box(200,150,125,(0,60,-10)))) for shape in [old,new]]
report={'model_sha256':hashlib.sha256(raw).hexdigest(),
    'upper_thigh_width_mm':{'source':root_widths[0],'candidate':root_widths[1]},
    'shell_mass_one_leg_kg':{'source':shell_mass(source),'candidate':shell_mass(model)},
    'mount_mass_one_leg_kg':{'source':mount_mass(source),'candidate':mount_mass(model)},
    'gross_sections':rows,'mount_hole_surround_checks':material,
    '17Nm_equal_sharing_force_screens_N':{'tie_source':17/(3*b.POD_TIE_RADIUS/1000),
        'tie_candidate':17/(3*design.TIE_RADIUS/1000),'stator_screw_candidate':17/(9*.0365)},
    'motor_to_tie_sleeve_nominal_radial_gap_mm':design.TIE_RADIUS-2.5-b.P['motor_radius'],
    'force_envelope':{'actuator_peak_torque_Nm':17,'structural_screen_torque_Nm':34,
        'crank_radius_mm':28,'minimum_transmission_cosine':math.cos(math.radians(54)),
        'pushrod_at_actuator_peak_N':17/(.028*math.cos(math.radians(54))),
        'pushrod_at_double_peak_screen_N':34/(.028*math.cos(math.radians(54))),
        'local_stator_overturning_arm_mm':19.5,
        'local_stator_overturning_at_actuator_peak_Nm':17/(.028*math.cos(math.radians(54)))*.0195,
        'ideal_max_tie_axial_reaction_at_actuator_peak_N':17/(.028*math.cos(math.radians(54)))*.0195/(1.5*design.TIE_RADIUS/1000),
        'scope':'Conservative local actuator bracket screen. Internal rod forces are not treated as whole-robot ground forces. Real impacts can exceed commanded motor torque.'},
    'load_envelope':{'cases':len(load_cases),'robot_mass_estimate_kg':mass,
        'ground_cases':'One kilogram payload, single support at 1 g; unloaded two-foot support at 3 g. Horizontal ground forces independently ±30% of vertical.',
        'section_loading':'Ideal knee shaft transmits force and X/Z overturning moment; its free Y rotation carries no bearing torque. Shaft loads include independent ±17 Nm actuator rod force. Unsymmetric bending uses the full area-moment tensor.',
        'scope':'Independent conservative force envelope, not a dynamically consistent gait simulation. Normal stress only; torsional/shear stress, local bearing/pin stresses, joint flexibility and fatigue remain unqualified.'},
    'unverified':['Actuator output-bearing radial and overturning ratings','Material allowables at print direction and operating temperature','Fastener grades, preload and fatigue'],
    'connection_assumption':{'section':'Combined-half properties assume full composite action. That connection has not been qualified.',
        'seam_shear':'Reported shear flow is a local prismatic-beam requirement. Closure sleeves can bypass the printed faces; bolt torque alone does not establish seam pressure or friction capacity.',
        'sleeves_per_leg':6,'sleeve_lengths_mm':[41,6],'sleeve_OD_ID_mm':[5,3.4],
        'tube_end_area_mm2':math.pi*(2.5**2-1.7**2),
        'ideal_overturning_tube_end_pressure_MPa_before_preload':(17/(.028*math.cos(math.radians(54)))*.0195/(1.5*design.TIE_RADIUS/1000))/(math.pi*(2.5**2-1.7**2)),
        'scope':'Local pad bearing/punching, thread engagement, plate prying, hole-clearance slip and tolerance stack need separate qualification.'},
    'clearance_allowance_example':{'nominal_motor_to_sleeve_gap_mm':design.TIE_RADIUS-2.5-b.P['motor_radius'],
        'illustrative_radial_allowances_mm':{'motor_OD_radius':.2,'axis_position':.15,'sleeve_OD_radius':.05,'bracket_deflection':.25},
        'validated':False,'scope':'Example budget only. Actual purchased dimensions, process capability and loaded deflection remain unmeasured.'},
    'section_method':'Planar cuts through welded exported meshes; polygon area moments by Green theorem. Source tessellation tolerance 0.1 mm; candidate 0.08 mm. This is a gross-section comparison, not FEA.',
    'scope':'Gross section area moments describe stiffness-related geometry only. They omit fastener slip, open-shell torsion, stress concentrations, print anisotropy, creep, heat, fatigue and impacts. Hole surrounds establish geometric ligaments, not bolt or material strength. New mounts and slimmer shells require load and fatigue qualification.'}
(OUT/'slim-structure-review.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['gross_sections','mount_hole_surround_checks']}),flush=True)
