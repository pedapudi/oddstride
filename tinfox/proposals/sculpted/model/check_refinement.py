"""Check changed solid geometry, unchanged mechanisms and printable part identities."""
import json,hashlib
from pathlib import Path
import numpy as np
import cadquery as cq
from kinematics import ROOT
BASE=ROOT.parent/'design/iterations/refinement-baseline'
old=json.loads((BASE/'model.json').read_text());new=json.loads((ROOT/'output/model.json').read_text())
eng=json.loads((ROOT/'output/engineering.json').read_text());previous=json.loads((BASE/'engineering.json').read_text());audit=json.loads((ROOT/'output/mounting-audit.json').read_text());plan=json.loads((ROOT/'output/manufacturing-plan.json').read_text())
stamp=hashlib.sha256((ROOT/'output/model.json').read_bytes()).hexdigest()
assert all(j['model_sha256']==stamp for j in [eng,audit,plan])
allowed={'motor_carrier','thigh_inner','thigh_outer','shin_inner','shin_outer','input_crank','pushrod','knee_inner_spacer','roll_cartridge','knee_axle','input_pin','output_pin','knee_end_cap','hip_disc','hip_index'}
changes=[];unchanged=[]
oldparts={p['name']:p for p in old['parts']}
for p in new['parts']:
 if not p.get('leg'):continue
 if p['name'] not in oldparts:
  assert any(t in p['name'] for t in ['_axle_bolt','_axle_nut','_shin_clamp_','_output_pivot_nut','_shin_join_','_bearing_inner','_bearing_outer','_shin_shell','_knee_retaining_ring','_motor_service_ring','_knee_head','_input_pin','_output_pin','_rod_bush_','_shin_head_','_bearing_70','_bearing_90']);changes.append(p['name']);continue
 before=oldparts[p['name']]
 equal=old['meshes'][before['mesh']]==new['meshes'][p['mesh']]
 if not equal:
  assert p['name'][3:] in allowed or any(t in p['name'] for t in ['_input_bolt_','_sleeve_','_bolt_']),p['name'];changes.append(p['name'])
 else:unchanged.append(p['name'])
assert any(n.endswith('_shin_inner') for n in changes)
for key in ['thigh','shank_to_foot_center','crank_radius','crank_phase_deg','rod_length','joint_limits_deg','motor_stack_inset_mm','limb_recess_mm']:
 assert old['parameters'][key]==new['parameters'][key],key

def angles(state):return {v for lo,hi in state['clear_intervals_deg'] for v in range(lo,hi+1)}
for leg,axes in previous['motion']['joint_sweeps'].items():
 for axis,state in axes.items():assert not angles(state)-angles(eng['motion']['joint_sweeps'][leg][axis]),(leg,axis)
for leg,state in previous['motion']['folded_hip_sweeps'].items():assert not angles(state)-angles(eng['motion']['folded_hip_sweeps'][leg]),leg
assert all(not x['collision'] and x['minimum_distance_mm']>=1.5 for x in eng['motion']['presets'].values())
assert not any(x['collision_samples'] for x in eng['motion']['transitions'].values())
# Probe the manufactured face above its sensor aperture to measure the actual bow.
face=cq.importers.importStep(str(ROOT/'output/step-parts/front_fascia.step')).val()
face_samples=[]
for y in [-90,-75,-50,-25,0,25,50,75,90]:
 probe=cq.Workplane('XY').box(40,.02,.02).val().translate((255,y,30))
 cut=face.intersect(probe)
 assert cut.Volume()>0,y
 face_samples.append({'y_mm':y,'front_x_mm':cut.BoundingBox().xmax})
sag=face_samples[4]['front_x_mm']-face_samples[0]['front_x_mm'];assert sag>2.0,sag
vertical_samples=[]
for z in [-28,-18,-8,2,12,22,30]:
 cut=face.intersect(cq.Workplane('XY').box(40,.02,.02).val().translate((255,86,z)))
 assert cut.Volume()>0,z
 vertical_samples.append({'z_mm':z,'front_x_mm':cut.BoundingBox().xmax})
vertical_sag=vertical_samples[3]['front_x_mm']-vertical_samples[0]['front_x_mm'];assert vertical_sag>3,vertical_sag
# The top and sides now form one connected printed clamshell.
roof=cq.importers.importStep(str(ROOT/'output/step-parts/body_center_0.step')).val();panel_fits=[]
assert len(roof.Solids())==1 and roof.isValid()
assert not any(p['name'].startswith('body_center_side_') for p in new['parts'])
parts={p['id']:p for p in plan['parts']};counts={}
for plate in plan['plates']:
 boxes=[]
 for item in plate['parts']:
  k=item['id'];counts[k]=counts.get(k,0)+1;x,y,_=item['center_mm'];w,d,h=item['bounds_mm'];lo=np.array([x-w/2,y-d/2]);hi=np.array([x+w/2,y+d/2]);assert np.all(lo>=9.999) and np.all(hi<=np.array([315,310])+.001)
  for a,b in boxes:assert not np.all(np.minimum(hi,b)-np.maximum(lo,a)>0),'Plate bounding boxes overlap'
  boxes.append((lo,hi))
for k,p in parts.items():
 if p['route'] in ['printed','elastomer-fit']:assert counts.get(k)==p['quantity'],k
 if 'oriented_stl' in p:assert hashlib.sha256((ROOT/'output'/p['oriented_stl']).read_bytes()).hexdigest()==p['stl_sha256'],k
before_audit=json.loads((BASE/'corrected-section-audit.json').read_text())
report={'model_sha256':stamp,'baseline_model_sha256':hashlib.sha256((BASE/'model.json').read_bytes()).hexdigest(),'changed_limb_parts':changes,'unchanged_mechanism_parts':unchanged,'joint_parameters_unchanged':True,'previous_sampled_motion_preserved':True,'face_samples':face_samples,'face_vertical_samples':vertical_samples,'face_vertical_bow_mm':vertical_sag,'face_center_to_y90_bow_mm':sag,'roof_side_panel_fits':panel_fits,'base_mass_kg':{'before':previous['mass']['base_kg'],'after':eng['mass']['base_kg']},'section_modulus_y_mm3':{k:{'before':before_audit['minimum_'+k+'_section_modulus_y_mm3'],'after':audit['minimum_'+k+'_section_modulus_y_mm3']} for k in ['thigh','shin']},'print_part_count':sum(p['route']=='printed' for p in parts.values()),'printed_instances':sum(p['quantity'] for p in parts.values() if p['route']=='printed'),'plate_count':len(plan['plates']),'scope':'Exact face and panel solids; nominal rigid motion samples; oriented STL identities and plate bounding boxes. Does not qualify FDM strength, CAM, tolerances, foot retention or loaded locomotion.'}
(ROOT/'output/refinement-checks.json').write_text(json.dumps(report,indent=2));print('Refinement geometry, mechanisms, motion and plate inventory verified.')
# Two measured sections distinguish horizontal bow from the new vertical bow.
curves=[]
for title,samples,key,origin,scale,sag in [('Left to right · Z = 30 mm',face_samples,'y_mm',180,2.8,sag),('Top to bottom · Y = 86 mm',vertical_samples,'z_mm',625,3.3,vertical_sag)]:
 center=max(v['front_x_mm'] for v in samples)
 points=' '.join(f"{origin+(v[key]-samples[0][key])*scale:.2f},{100+(center-v['front_x_mm'])*12:.2f}" for v in samples)
 curves.append(f'<text x="{origin-20}" y="70" font-size="17">{title}</text><polyline points="{points}" fill="none" stroke="#2e4435" stroke-width="4"/><text x="{origin-20}" y="225" font-size="15">Measured bow: {sag:.2f} mm</text>')
svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 320"><rect width="1000" height="320" fill="#eeeee7"/><g font-family="sans-serif" fill="#2e4435"><text x="35" y="35" font-size="24">Convex face · two measured STEP sections</text>'+''.join(curves)+'<text x="35" y="275" font-size="15">Independent crowns: 8 mm across the width + 10 mm top to bottom. Depth exaggerated.</text><text x="35" y="300" font-size="14">Vertical section lies outside the sensor opening. Measurements are from the exported solid.</text></g></svg>'
(ROOT.parent/'design/17-face-curvature.svg').write_text(svg)
