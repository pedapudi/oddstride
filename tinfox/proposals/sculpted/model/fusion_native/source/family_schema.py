"""Define independent design-family dimensions and their required dependencies.

This is a migration specification, not evidence that dimensions are connected.
Vendor interfaces remain independent of robot size. The 20 kg variant requires
new actuator, structure, thermal, stability, and motion qualification.
"""
PARAMETERS={
 'chassis_length':{'units':'mm','baseline':464,'owners':['chassis'],'dependencies':['chassis rails and crossmembers','shell section station positions','head and rear interfaces'],'qualified':False},
 'chassis_width':{'units':'mm','baseline':222.4,'owners':['chassis'],'dependencies':['rail separation','shell transverse profiles','electronics support widths'],'qualified':False},
 'hip_spacing_longitudinal':{'units':'mm','baseline':370,'owners':['chassis','leg','assembly'],'dependencies':['front/rear shoulder datums','motor support locations','body motion clearances'],'qualified':False},
 'hip_roll_axis_spacing':{'units':'mm','baseline':136,'owners':['chassis','leg','assembly'],'dependencies':['left/right shoulder datums','roll cartridges','shoulder clearances'],'qualified':False},
 'hip_pitch_lateral_offset':{'units':'mm','baseline':0,'owners':['leg','assembly'],'dependencies':['roll-to-pitch axis placement','motor carrier and axial stack'],'qualified':False},
 'thigh_center_distance':{'units':'mm','baseline':170,'owners':['leg','assembly'],'dependencies':['thigh distal bearing datum','thigh shell span with rigid motor/knee interface zones','pushrod center distance','knee frame and closure'],'qualified':False},
 'shank_contact_length':{'units':'mm','baseline':170,'owners':['leg','assembly'],'dependencies':['shin length','foot center datum','support-contact kinematics'],'qualified':False},
 'foot_radius':{'units':'mm','baseline':22,'owners':['leg','assembly'],'dependencies':['foot native geometry','shank-to-foot-center derived dimension'],'qualified':False},
 'shank_to_foot_center':{'units':'mm','expression':'shank_contact_length - foot_radius','owners':['leg','assembly'],'dependencies':['foot mounting datum','shin distal interface'],'qualified':False},
 'linkage_crank_radius':{'units':'mm','baseline':28,'owners':['leg','assembly'],'dependencies':['input-crank rod eye','integral shin crank eye','crank/rod motion frames'],'qualified':False},
 'linkage_phase':{'units':'deg','baseline':-78,'owners':['leg','assembly'],'dependencies':['integral shin crank-eye angle','input/output phase','motion and closure'],'qualified':False},
 'pushrod_center_distance':{'units':'mm','expression':'thigh_center_distance','owners':['leg','assembly'],'dependencies':['pushrod eye spacing','four-bar closure'],'qualified':False},
 'bearing_outer_diameter':{'units':'mm','baseline':28,'owners':['leg'],'dependencies':['bearing seats only; not scaled with limb length'],'qualified':False},
 'bearing_inner_diameter':{'units':'mm','baseline':12,'owners':['leg'],'dependencies':['bearing reference and compatible shaft family'],'qualified':False},
 'bearing_width':{'units':'mm','baseline':8,'owners':['leg'],'dependencies':['axial shoulders and spacer stack','extraction access'],'qualified':False},
 'knee_shaft_diameter':{'units':'mm','baseline':12,'owners':['leg'],'dependencies':['axle','shaft clearance bores','bushing bore family'],'qualified':False},
 'bearing_seat_diametral_allowance':{'units':'mm','baseline':0,'owners':['leg'],'dependencies':['bearing seat diameter = bearing_outer_diameter + allowance'],'physical_fit_verified':False,'qualified':False},
 'shaft_clearance_diametral':{'units':'mm','baseline':.2,'owners':['leg'],'dependencies':['12.2 mm shaft clearance bores only'],'physical_fit_verified':False,'qualified':False},
 'body_shell_wall':{'units':'mm','baseline':2.8,'owners':['chassis'],'dependencies':['inner body-shell profiles','local reinforced interfaces remain independently sized'],'qualified':False},
 'limb_shell_wall':{'units':'mm','baseline':2.8,'owners':['leg'],'dependencies':['inner limb profiles','structural ribs','bearing roots remain independently sized'],'qualified':False},
 'body_motion_clearance':{'units':'mm','baseline':1.5,'owners':['chassis','leg','assembly'],'dependencies':['shoulder sweep reliefs','plug and wire corridors'],'qualified':False},
 'sensor_top_mount_length':{'units':'mm','baseline':None,'owners':['chassis','head'],'dependencies':['shared sensor top mounting interface; dimension mapping pending'],'qualified':False},
 'sensor_top_mount_width':{'units':'mm','baseline':None,'owners':['chassis','head'],'dependencies':['shared sensor top mounting interface; dimension mapping pending'],'qualified':False},
}
MOTOR_FAMILIES={
 'RS02':{'state':'baseline native geometry; semantic interface mapping pending','envelope_diameter_mm':78.5,'envelope_depth_mm':45.4,'mount_patterns':'Must be mapped from frozen source interfaces and verified vendor drawing; never inferred from diameter','scale_with_robot':False},
 'RS03':{'state':'not implemented or qualified','scale_with_robot':False},
 'RS04':{'state':'not implemented or qualified','scale_with_robot':False},
}
EDIT_GATES=[
 {'parameter':'thigh_center_distance','test_value':180,'checks':['knee datum shifts exactly 10 mm','motor bolt patterns unchanged','bearing dimensions unchanged','pushrod center distance follows','both handed components regenerate','linkage closure and assembly placements remain consistent','baseline restored']},
 {'parameter':'hip_spacing_longitudinal','test_value':390,'checks':['shoulder datums shift symmetrically 10 mm each','support mounts and shell relief follow','leg geometry and vendor interfaces unchanged','assembly and service paths checked','baseline restored']},
 {'parameter':'body_shell_wall','test_value':3.2,'checks':['material volume changes','outer envelope preserved','interfaces remain aligned','no thin/invalid faces','baseline restored']},
]
if __name__=='__main__':
 import json
 from pathlib import Path
 path=Path(__file__).resolve().parents[1]/'manifests/design-family.json'
 path.write_text(json.dumps({'schema':1,'parameterization_gate_passed':False,'parameters':PARAMETERS,'motor_families':MOTOR_FAMILIES,'required_edit_tests':EDIT_GATES,'current_limitation':'Native sketches and operations are editable, but many profile coordinates and primitive dimensions are still independent constants. Named parameter count does not qualify a scalable robot family.','payload_20kg_qualified':False},indent=2))
 print(path)
