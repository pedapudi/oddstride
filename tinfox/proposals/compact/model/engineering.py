"""Recompute motion, quasi-static torque and structural screens from exported CAD.

No dynamic performance or material qualification is implied by these screens.
"""
import csv, json, math, hashlib, copy
from collections import defaultdict
import numpy as np
from kinematics import ROOT,P,LEGS,POSES,frames,matrix,contacts,point
from collision import Checker

DATA=json.loads((ROOT/'output'/'model.json').read_text())
PARTS=DATA['parts'];G=9.81

def intervals(samples):
    out=[];start=prev=None
    for a,ok in samples:
        if ok:
            if start is None:start=a
            prev=a
        elif start is not None:out.append([start,prev]);start=prev=None
    if start is not None:out.append([start,prev])
    return out

def motion():
    c=Checker();result={'presets':{},'joint_sweeps':{},'transitions':{},'step_deg':1}
    for name,poses in POSES.items():
        state=c.check(poses)
        result['presets'][name]={**state,**c.clearance(poses)}
    for leg in LEGS:
        result['joint_sweeps'][leg]={}
        limits=[P['joint_limits_deg']['roll'],P['joint_limits_deg']['hip_front' if leg.startswith('F') else 'hip_rear'],P['joint_limits_deg']['knee']]
        for j,(name,lim) in enumerate(zip(['roll','hip','knee'],limits)):
            checks=[];first_hit=None
            for a in range(lim[0],lim[1]+1):
                poses=copy.deepcopy(POSES['stand']);poses[leg][j]=a
                r=c.check(poses);checks.append((a,not r['collision']))
                if r['collision'] and first_hit is None:first_hit={'angle':a,'pairs':r['pairs']}
            result['joint_sweeps'][leg][name]={'samples':len(checks),'clear_intervals_deg':intervals(checks),'first_collision':first_hit}
        print('Motion sweep complete:',leg,flush=True)
    for name,target in POSES.items():
        failed=[];count=101
        for t in np.linspace(0,1,count):
            pose={l:(np.array(POSES['stand'][l])*(1-t)+np.array(target[l])*t).tolist() for l in LEGS}
            r=c.check(pose)
            if r['collision']:failed.append({'fraction':round(float(t),3),'pairs':r['pairs']})
        result['transitions'][name]={'samples':count,'collision_samples':len(failed),'first_collision':failed[0] if failed else None}
    coordinated=[]
    for a in range(-60,61):
        pose={leg:[a if leg.endswith('L') else -a,-35 if leg.startswith('F') else 35,-70] for leg in LEGS}
        coordinated.append((a,not c.check(pose)['collision']))
    result['coordinated_roll']={'samples':len(coordinated),'clear_intervals_deg':intervals(coordinated),'pose_rule':'left roll = a, right roll = -a; front hip -35 degrees, rear hip 35 degrees, knee -70 degrees. Free-space motion, not a grounded gait.'}
    # Fold the knee while sweeping hip pitch to distinguish joint travel from
    # collisions caused by an extended leg reaching the adjacent shoulder.
    result['folded_hip_sweeps']={}
    for leg in LEGS:
        lim=P['joint_limits_deg']['hip_front' if leg.startswith('F') else 'hip_rear']
        checks=[]
        for a in range(lim[0],lim[1]+1):
            pose=copy.deepcopy(POSES['stand']);pose[leg]=[0,a,-130]
            checks.append((a,not c.check(pose)['collision']))
        result['folded_hip_sweeps'][leg]={'samples':len(checks),'knee_deg':-130,'clear_intervals_deg':intervals(checks)}
    result['scope']='Rigid moving pairs, sampled poses. Static fits, pin interfaces, wires, tolerance stacks, ground and load deflection are not certified. Sampled clearance is not continuous collision proof.'
    return result

def battery_fit():
    c=Checker();c.check(POSES['stand'])
    _,pairs=c.manager.in_collision_internal(return_names=True)
    batteries={p['name'] for p in PARTS if p['name'].startswith('battery_') and p['material']=='envelope'}
    hits=sorted([list(pair) for pair in pairs if batteries.intersection(pair)])
    return {'intersections':hits,'scope':'Battery envelope versus all checked rigid meshes, including fixed body parts. Adapter and electrical-contact fits remain unselected.'}

def fixed_packaging():
    c=Checker();c.check(POSES['stand'])
    _,pairs=c.manager.in_collision_internal(return_names=True)
    def is_cover(n):return n.startswith(('body_','belly_'))
    def is_internal(n):return n.startswith(('chassis_beam','electronics_shelf','electronics_clearance','battery_rail')) or n.endswith(('_roll_motor','_roll_cartridge'))
    hits=[]
    for a,b in pairs:
        if (is_cover(a) and is_internal(b)) or (is_cover(b) and is_internal(a)) or ('chassis_beam' in a+b and '_roll_motor' in a+b):hits.append(sorted([a,b]))
    return {'intersections':sorted(hits),'scope':'Torso covers versus fixed frame, shelf, cassette rails and roll assemblies; also frame versus roll motors. Intended bolted interfaces excluded.'}

def mass_budget():
    by=defaultdict(float)
    # The electronics allowance replaces mass placeholders for the sensor/display envelopes.
    sensors={'lidar','lidar_base','sensor_window','camera_-38','camera_38','camera_-30','camera_30','camera_-24','camera_24','camera_-27','camera_27','status_display'}
    for p in PARTS:
        if p['name'] in sensors or p['name'].startswith('camera_'):continue
        category='motors' if p['name'].endswith('_motor') else ('batteries' if p['name'].startswith('battery_') and p['material']=='envelope' else p['material'])
        by[category]+=p['mass_kg']
    by['compute_sensors_wiring_allowance']=P['compute_sensors_wiring_mass_kg_assumed']
    by['unmodeled_mounts_cables_fasteners_allowance']=.4
    return {'categories_kg':dict(by),'base_kg':sum(by.values()),'status':'CAD solid volumes at PETG/aluminum/steel density, nominal motors, assumed packs and electronics. Not a weighed robot.'}

def limb_potential(leg,q):
    poses={l:q if l==leg else POSES['stand'][l] for l in LEGS}
    return sum(p['mass_kg']*G*point(matrix(p,poses),p['com_mm'])[2]/1000 for p in PARTS if p['leg']==leg)

def torque(q,force):
    foot,origins,axes=contacts('FL',q)
    jac=np.column_stack([np.cross(a,(foot-o)/1000) for a,o in zip(axes,origins)])
    eps=1e-4;gravity=[]
    for j in range(3):
        hi=list(q);lo=list(q);hi[j]+=math.degrees(eps);lo[j]-=math.degrees(eps)
        gravity.append((limb_potential('FL',hi)-limb_potential('FL',lo))/(2*eps))
    external=jac.T@np.array(force);required=np.array(gravity)-external
    motor=np.abs(required)/[1,1,P['knee_efficiency_assumption']]
    a=math.radians(q[2]+P['crank_phase_deg'])
    rod_force=abs(required[2])/(P['crank_radius']/1000*abs(math.cos(a)))
    return {'joint_Nm':required.tolist(),'limb_gravity_Nm':gravity,'contact_Nm':external.tolist(),'motor_Nm':motor.tolist(),'rod_force_N':rod_force,'foot_mm':foot.tolist()}

def torques(mass):
    rows=[]
    cases=[('four_foot_stand',P['nominal_pose_deg'],.25,1,0,0),('two_foot_stand',P['nominal_pose_deg'],.5,1,0,0),
           ('three_foot_crouch',[0,65,-130],1/3,1,0,0),('stair_reach_60_percent',[8,-10,-75],.6,1,0,0),
           ('reach_with_braking',[8,-10,-75],.6,1,-.25,0),('splayed_two_foot',[25,35,-70],.5,1,0,.2)]
    for payload in P['payload_cases_kg']:
        for name,q,share,factor,fx,fy in cases:
            fz=(mass+payload)*G*share*factor
            result=torque(q,[fx*fz,fy*fz,fz])
            rows.append({'case':name,'payload_kg':payload,'total_kg':mass+payload,'q_deg':q,'force_N':[fx*fz,fy*fz,fz],**result})
    for name,factor in [('unloaded_2p5g_pulse',2.5),('unloaded_3g_landing_screen',3)]:
        q=P['nominal_pose_deg'];fz=mass*G*.5*factor
        rows.append({'case':name,'payload_kg':0,'total_kg':mass,'q_deg':q,'force_N':[0,0,fz],**torque(q,[0,0,fz])})
    return rows

def structural(rows):
    audit=json.loads((ROOT/'output/mounting-audit.json').read_text())
    assert audit['model_sha256']==hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest(),'Run audit_mounting.py before engineering.py'
    section=min(audit['shin_sections'],key=lambda x:x['section_modulus_y_mm3'])
    iy=section['Iy_mm4'];ix=section['Ix_mm4']
    max_t=max(abs(x) for r in rows for x in r['joint_Nm'])
    stress=max_t*1000/section['section_modulus_y_mm3']
    shaft_span=36
    shaft_bending=32*(17/(P['crank_radius']/1000*math.cos(math.radians(54))))*shaft_span/4/(math.pi*P['knee_shaft_diameter']**3*(1-(8/P['knee_shaft_diameter'])**4))
    minimum_cos=min(abs(math.cos(math.radians(a+P['crank_phase_deg']))) for a in np.linspace(*P['joint_limits_deg']['knee'],1001))
    force=17/(P['crank_radius']/1000*minimum_cos)
    pin_bending=32*force*4/(math.pi*6**3)
    pin_shear=4*force/(math.pi*6**2)
    # Round 6 mm core is smaller than the CAD's 6 mm square central pushrod section.
    inertia=math.pi*6**4/64;critical=math.pi**2*200_000*inertia/P['rod_length']**2
    return {'shin_screen_section_mm':section,'gross_Iy_mm4':iy,'gross_Ix_mm4':ix,
            'maximum_case_moment_Nm':max_t,'gross_bending_stress_MPa':stress,
            'coupon_strength_needed_for_factor_2_MPa':stress*2,
            'shaft_12x8mm_conservative_bending_MPa':shaft_bending,
            'rod_force_at_17Nm_and_worst_transmission_angle_N':force,
            'rod_ideal_pinned_euler_N':critical,'ideal_buckling_ratio':critical/force,
            'pin_6mm_single_shear_bending_MPa':pin_bending,
            'pin_6mm_nominal_vm_MPa':math.sqrt(pin_bending**2+3*pin_shear**2),
            'pin_material_yield_needed_for_factor_2_MPa':2*math.sqrt(pin_bending**2+3*pin_shear**2),
            'fixed_shaft_span_assumption_mm':shaft_span,'section_model':'Smallest sampled sagittal section modulus from both CAD shin halves, at 5 mm intervals from z=-35 to -145 mm; 0.2 mm slice thickness. Applies the maximum case joint moment uniformly as a conservative bending screen.',
            'limitations':'Gross-section linear screens omit holes, stress concentration, open-fork torsion, shaft retention, torsion/bending interaction, local buckling, layer anisotropy, creep, fatigue, fastener slip, bearing seats and impacts. Pin bending assumes 4 mm overhang and must be recalculated for the selected shoulder-pin stack. Required coupon strength is not an assigned PETG allowable. Metal grade and joints also require qualification.'}

def printability():
    rows=[];seen=set()
    for p in PARTS:
        if p['material']!='petg' or p['mesh'] in seen:continue
        seen.add(p['mesh']);dims=sorted(p['bounds_mm']);bed=sorted([x-2*P['print_bed_margin_mm'] for x in P['h2d_single_nozzle_volume_mm']])
        rows.append({'part':p['name'],'bounds_mm':p['bounds_mm'],'fits_rotated_bounding_box':all(x<=y for x,y in zip(dims,bed))})
    return {'parts':rows,'all_fit':all(r['fits_rotated_bounding_box'] for r in rows),'scope':'Bounding boxes only; intended leg print orientation has shell joint plane on the bed. Slicer supports, overhangs and material setup not validated.'}

def main():
    mass=mass_budget();rows=torques(mass['base_kg'])
    baseline=json.loads((ROOT/'weight-baseline.json').read_text())
    comparison={'target_base_kg':P['weight_target_kg'],'baseline_base_kg':baseline['mass']['base_kg'],'current_base_kg':mass['base_kg'],'total_reduction_kg':baseline['mass']['base_kg']-mass['base_kg'],'battery_allowance_reduction_kg':baseline['battery_allowance_kg']-2*P['battery_each_mass_kg_assumed'],'electronics_allowance_reduction_kg':baseline['electronics_allowance_kg']-P['compute_sensors_wiring_mass_kg_assumed'],'baseline_model_sha256':baseline['model_sha256']}
    comparison['geometry_and_component_reduction_kg']=comparison['total_reduction_kg']-comparison['battery_allowance_reduction_kg']-comparison['electronics_allowance_reduction_kg']
    report={'weight_comparison':comparison,'model_sha256':hashlib.sha256((ROOT/'output'/'model.json').read_bytes()).hexdigest(),'mass':mass,'motion':motion(),'torque_cases':rows,'structure':structural(rows),'printability':printability(),'battery_fit':battery_fit(),'fixed_packaging':fixed_packaging(),
        'torque_scope':'Quasi-static generalized torques from prescribed foot loads plus gravity of modeled moving parts. Knee assumed 1:1 at 90% efficiency. Pulses are force screens, not simulated gaits or inverse dynamics. Thermal, velocity, joint acceleration and impact response are not predicted.',
        'sources':{'unitree':'https://github.com/unitreerobotics/unitree_ros/blob/master/robots/go2_description/urdf/go2_description.urdf','motor':'https://github.com/RobStride/Product_Information/blob/main/Product%20Literature/CAN2.0/RS02/RS02User%20Manual260713.pdf','printer':'https://cdn1.bambulab.com/documentation/h2d/en/H2D_Laser_Full_Combo_20250305.pdf'}}
    (ROOT/'output'/'engineering.json').write_text(json.dumps(report,indent=2))
    flat=[]
    for r in rows:
        a={k:r[k] for k in ['case','payload_kg','total_kg','rod_force_N']}
        for i,j in enumerate(['roll','hip','knee']):a[j+'_motor_Nm']=r['motor_Nm'][i]
        flat.append(a)
    with (ROOT/'output'/'torques.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
    print('Base mass estimate',round(mass['base_kg'],3),'kg; print envelopes fit:',report['printability']['all_fit'],flush=True)
    for r in rows:
        if r['payload_kg']==1 or 'unloaded' in r['case']:print(r['case'],r['payload_kg'],[round(x,2) for x in r['motor_Nm']],flush=True)

if __name__=='__main__':main()
