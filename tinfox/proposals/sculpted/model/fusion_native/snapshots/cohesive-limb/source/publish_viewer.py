"""Publish portable viewer metadata from the accepted and candidate CAD exports."""
import json,hashlib,re
from pathlib import Path
from kinematics import ROOT
import engineering as eng
VIEW=ROOT.parents[2]/'viewer'
assert VIEW.name=='viewer'
LABELS={'body_center_0':'Upper body shell','body_nose_surround':'Head bridge','belly_center_0':'Lower body shell','thigh_inner':'Inner thigh shell','thigh_outer':'Outer thigh shell','shin_inner':'Inner shin shell','shin_outer':'Outer shin shell','motor_carrier_1':'Front hip carrier','motor_carrier_-1':'Rear hip carrier','motor_mount_ring':'Knee motor mounting plate','front_fascia':'Camera face','hip_hub':'Hip output hub','knee_axle':'Knee axle sleeve','knee_inner_spacer':'Knee bearing spacer','pushrod':'Knee pushrod','input_crank':'Knee input crank','electronics_shelf':'Electronics deck','chassis_lower_brace':'Lower chassis brace'}
def label(key):
 right=key.endswith('_right');plain=key.removesuffix('_right')
 name=LABELS.get(plain,plain.replace('_',' ').capitalize())
 return name+(' · right side' if right else '')
def url(path):return '../'+str(path.relative_to(ROOT.parents[2]))
def category(p):
 if p.get('service_role') or p['material']=='envelope':return 'Sensors and wiring'
 if p['material']=='steel':return 'Hardware'
 return 'Legs' if p.get('leg') else 'Body and chassis'
rows=[]
v0_folder = 'v0-rounded-body' if (ROOT/'output/v0-rounded-body/model.json').exists() else 'service-design'
designs=[('v0',v0_folder,'V0 · rounded body' if v0_folder!='service-design' else 'Reference robot · V0','V0 limbs and carriers with the rounded body cover. Fixed cover/frame contacts require fit review.' if v0_folder!='service-design' else 'Accepted mechanical design being rebuilt as editable native Fusion components.'),('v1','rounded-design','Rounded enclosure · V1','Candidate body and limb shapes built around the reference mechanism. Manufacturing details and mobility remain under review.')]
if (ROOT/'output/integrated-candidate/audit.json').exists():
 designs.append(('v2','integrated-candidate','Flowing thigh + structural neck','Continuous thigh-to-knee shells, conventional shoulder screws and a deeper camera neck mounted across both chassis rails. Review geometry; stock quantities and structural strength remain unverified.'))
if (ROOT/'output/raised-head-prototype/audit.json').exists():
 designs.append(('v3','raised-head-prototype','Attentive head posture','Head set slightly forward with a gentle upward gaze, close to the shoulders. The lidar stays level on an integral lid seat. Cable access and removable mounting are retained.'))
if (ROOT/'output/shoulder-head-prototype/audit.json').exists():
 designs.append(('v4','shoulder-head-prototype','V1 redesign · shoulder-mounted head','Compact head over the shoulders, supported by a broad hollow plinth and metal rail saddle. Review candidate; extreme chassis collisions and structural qualification remain unresolved.'))
if (ROOT/'output/limb-refinement/audit.json').exists():
 designs.append(('v5','limb-refinement','Continuous limb · candidate','Matched structural thigh halves, a continuous motor-to-knee shell and cam-shaped shin head. Low sensor pod and reference chassis retained. Review the interface and motion reports before fabrication.'))
for id,folder,title,description in designs:
 out=ROOT/'output'/folder;raw=(out/'model.json').read_bytes();model=json.loads(raw);stamp=hashlib.sha256(raw).hexdigest()
 interface_path=out/'limb-interfaces.json'
 interface_report=json.loads(interface_path.read_text()) if interface_path.exists() else {}
 bearing_review_failed=interface_report.get('model_sha256')==stamp and any(not r.get('passed',True) and ('full-width bearing wall' in r.get('interface','') or 'continuous axial bearing shoulder' in r.get('interface','')) for r in interface_report.get('checks',[]))
 if bearing_review_failed:description='Shin bearing support needs redesign: the pushrod clearance interrupts the outer bearing shoulder and seat edge. '+description
 eng.DATA=model;eng.PARTS=model['parts'];eng.P.update(model['parameters']);mass=eng.mass_budget();torques=eng.torques(mass['base_kg'])
 (out/'torques.json').write_text(json.dumps({'model_sha256':stamp,'mass':mass,'torque_cases':torques,'scope':'Prescribed foot-force and link-gravity estimate. Does not establish gait performance, impact capacity or thermal endurance.'},indent=2))
 library=[]
 for key in sorted({p['mesh'] for p in model['parts']}):
  instances=[p for p in model['parts'] if p['mesh']==key];p=instances[0]
  if p.get('service_role') in ['keepout','withdrawal']:continue
  record={'id':key,'label':label(key),'instances':[q['name'] for q in instances],'quantity':len(instances),'category':category(p),'material':p['material'],'mass_kg':p['mass_kg'],'dimensions_mm':p['bounds_mm'],'volume_mm3':p.get('volume_mm3'),'note':p.get('note','')}
  for ext,sub in [('step','step'),('stl','stl')]:
   for candidate in [out/sub/f'{key}.{ext}',*([ROOT/'output/integrated-candidate'/sub/f'{key}.{ext}'] if id in ['v3','v4','v5'] else []),ROOT/'output/v0-rounded-body'/sub/f'{key}.{ext}',ROOT/'output/service-design'/sub/f'{key}.{ext}',ROOT/'output'/('step-parts' if ext=='step' else 'stl')/f'{key}.{ext}']:
    if candidate.exists():record[ext]=url(candidate);break
  record['custom']=('step' in record and p['material'] in ['petg','aluminum']) or key in ['pushrod','knee_axle','knee_inner_spacer']
  if bearing_review_failed and key.startswith('shin_') and key.removesuffix('_right') in ['shin_inner','shin_outer']:
   record['note']='Not ready for fabrication: restore continuous bearing support and recheck the pushrod clearance before printing or machining. '+record['note']
  print_file=out/'print-stl'/f'{key}.stl'
  if print_file.exists():record['print_stl']=url(print_file)
  if id=='v2' and key=='body_nose_surround':record['label']='Camera chassis cradle'
  if id=='v2' and key=='front_fascia':record['label']='Camera hood and face'
  if id=='v2' and key.removesuffix('_right') in ['input_pin','output_pin']:
   record['note']=p.get('note','')+' Conventional fastener is modeled; current on-hand stock quantities remain unverified.'
  library.append(record)
 export_report=out/'assembly-export.json'
 assembly_current=export_report.exists() and json.loads(export_report.read_text()).get('model_sha256')==stamp
 rows.append({'id':id,'title':title,'description':description,'model':url(out/'model.json'),'audit':url(out/'audit.json'),'assembly':url(out/'updated-robot.step') if assembly_current and (out/'updated-robot.step').exists() else None,'model_sha256':stamp,'estimated_mass_kg':mass['base_kg'],'physical_components':sum(p.get('service_role') not in ['keepout','withdrawal'] for p in model['parts']),'parts':library,'scope':('Preview: fixed cover/frame contacts need review. Whole-assembly STEP export is pending; individual part exports are available. ' if folder=='v0-rounded-body' else '')+'CAD prototype. Nominal rigid-part checks do not validate printed strength, flexible cables, tolerances or loaded motion.'})
 reports=[]
 for filename,title in [('installation-fit.json','Installation fit'),('neck-fit.json','Fastener and tool access'),('head-clearance.json','Head clearance sweep'),('chassis-limits.json','Chassis motion limits'),('torques.json','Mass and torque estimates'),('manufacturing-review.json','Print and assembly review'),('limb-folding.json','Knee folding sweep'),('limb-interfaces.json','Limb interfaces and bearing service'),('step-roundtrip.json','STEP solid export checks'),('knee-design-review.json','Knee geometry and load estimates')]:
  path=out/filename
  if path.exists() and json.loads(path.read_text()).get('model_sha256')==stamp:reports.append({'title':title,'url':url(path)})
 rows[-1]['reports']=reports
VIEW.mkdir(exist_ok=True);(VIEW/'catalog.json').write_text(json.dumps({'designs':rows},indent=2));print('Viewer catalog:',VIEW,flush=True)
