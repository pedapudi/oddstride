"""Publish portable viewer metadata from the accepted and candidate CAD exports."""
import json,hashlib,re,sys
from pathlib import Path
from kinematics import ROOT
from cad_authority import require_generated_authority
import engineering as eng
VIEW=ROOT.parents[2]/'viewer'
assert VIEW.name=='viewer'
sys.path.insert(0,str(VIEW))
from catalog_io import write_catalog
require_generated_authority(ROOT)
existing_catalog=VIEW/'catalog.json'
if existing_catalog.exists():
 existing=json.loads(existing_catalog.read_text())
 if any(row.get('source',{}).get('kind')=='fusion-native' and not row.get('archived') for row in existing['designs']):
  raise RuntimeError('An active native Fusion review exists. Publish its saved native exports instead of replacing it with legacy generated geometry.')
LABELS={'body_center_0':'Upper body shell','body_nose_surround':'Head bridge','belly_center_0':'Lower body shell','thigh_inner':'Inner thigh shell','thigh_outer':'Outer thigh shell','shin_inner':'Inner shin shell','shin_outer':'Outer shin shell','motor_carrier_1':'Front hip carrier','motor_carrier_-1':'Rear hip carrier','motor_mount_ring':'Knee motor mounting plate','front_fascia':'Camera face','hip_hub':'Hip output hub','knee_axle':'Knee axle sleeve','knee_inner_spacer':'Knee bearing spacer','pushrod':'Knee pushrod','input_crank':'Knee input crank','electronics_shelf':'Electronics deck','chassis_lower_brace':'Lower chassis brace'}
for front,title in [(1,'Front'),(-1,'Rear')]:
 for key,name in [('roll_cartridge','bearing housing'),('roll_stator_backplate','removable motor mounting plate'),('roll_outer_retainer','outer-race retainer'),('hip_stator_closure','hip motor closure'),('roll_inner_backplate','roll drive backplate'),('roll_inner_spacer','inner-race spacer'),('roll_outer_spacer','outer-race spacer')]:
  LABELS[f'{key}_{front}']=title+' '+name
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
 designs.append(('v5','limb-refinement','Low profile · sensor saddle','Low continuous camera hood and lidar seat supported directly above the chassis crossmember. Hood and main cover have separate upward removal paths. Sensor mounting and printed strength remain unqualified.'))
if (ROOT/'output/compact-thigh-work/audit.json').exists():
 designs.append(('v6','compact-thigh-work','Integrated motor cup · slimmer thigh','Two structural thigh halves wrap around the proximal knee motor. A stepped service seam exposes the mounting plate; the outer motor cap moves inward 6 mm. Review candidate; printed strength and extreme coupled motion remain unqualified.'))
if (ROOT/'output/integrated-pitch-work/audit.json').exists():
 designs.append(('v7','integrated-pitch-work','Integrated pitch carrier · opposed outputs','Packaging study: inward-facing knee actuator and structural thigh halves replace the external stator ring and tie cage. Standing clears, but several walking and folded poses collide with the body. This is not a qualified replacement limb.'))
if (ROOT/'output/seamless-limb-work/audit.json').exists():
 designs.append(('v8','seamless-limb-work','Rounded structural limb','Coordinated motor cup, crowned thigh and rounded shin retain the established actuator, linkage and bearing planes. Two structural halves per segment. See interface, service and sampled motion checks; printed strength and production tolerances remain unqualified.'))
if (ROOT/'output/manufacturing-thigh-work/audit.json').exists():
 designs.append(('v9','manufacturing-thigh-work','Manufacturing-refined thigh','Rounded two-piece thigh with an analytic motor cup, blended straight service split, cutter-relieved nut pocket, fixture contacts and motor-bore lead-in. Oriented print files and unsliced exterior supports are available. CNC toolpaths, printed fit and loaded strength remain unqualified.'))
if (ROOT/'output/slim-limb-work/audit.json').exists():
 designs.append(('v10','slim-limb-work','Slender structural limb','Rounded three-point motor mounts, a narrower motor cup and tapered thigh web retain the motor, tie-circle, linkage and bearing datums. Reinforced internal walls and hub ribs support the revised load paths. Strength, seam load transfer, printed fits and CNC toolpaths remain unqualified.'))
if (ROOT/'output/cohesive-chassis-work/audit.json').exists():
 designs.append(('v11','cohesive-chassis-work','Continuous shoulder enclosure','Smooth shoulder openings replace corner tabs around the fixed roll motors. Integral tapped metal frame pads simplify tie assembly; the thigh face has no waist depression. Review candidate; frame strength, printed fits and fastener tolerances remain unqualified.'))
if (ROOT/'output/closed-thigh-work/audit.json').exists():
 designs.append(('v12','closed-thigh-work','Closed thigh · continuous front wall','The modeled boot folds outside a continuous thigh wall. The full-sphere relief is removed while preserving the joint axes, 170 mm link and service access. Retired frame-mount remnants are cleared. Actual boot deformation, manufacturing fit and strength remain unqualified.'))
if (ROOT/'output/clamp-seat-work/audit.json').exists():
 designs.append(('v13','clamp-seat-work','Current limb · supported shell clamps','Continuous thigh wall and open washer seats with metal compression sleeves. Nominal washer contact is checked. Fit, clamp preload, printed strength and CNC access remain under review. The paired-bearing hip is a separate work in progress.'))
if (ROOT/'output/paired-roll-work/audit.json').exists():
 designs.append(('v14','paired-roll-work','Prototype limb · paired hip bearings','Bench limb with two 6810 bearings, a removable hip-motor flange and M5 knee retention. M3, M4 and M5 fasteners serve the limb. Fit prints are available; stationary chassis contacts, operating fits, preload and loaded strength remain unresolved.'))
for id,folder,title,description in designs:
 out=ROOT/'output'/folder;raw=(out/'model.json').read_bytes();model=json.loads(raw);stamp=hashlib.sha256(raw).hexdigest()
 interface_path=out/'limb-interfaces.json'
 interface_report=json.loads(interface_path.read_text()) if interface_path.exists() else {}
 bearing_review_failed=interface_report.get('model_sha256')==stamp and any(not r.get('passed',True) and ('full-width bearing wall' in r.get('interface','') or 'continuous axial bearing shoulder' in r.get('interface','')) for r in interface_report.get('checks',[]))
 if bearing_review_failed:description='Shin bearing support needs redesign: the pushrod clearance interrupts the outer bearing shoulder and seat edge. '+description
 mass_report=json.loads((out/'torques.json').read_text()) if (out/'torques.json').exists() else {}
 if mass_report.get('model_sha256')==stamp:
  mass=mass_report['mass']
 else:
  eng.DATA=model;eng.PARTS=model['parts'];eng.P.clear();eng.P.update(model['parameters']);mass=eng.mass_budget();torques=eng.torques(mass['base_kg'])
  (out/'torques.json').write_text(json.dumps({'model_sha256':stamp,'mass':mass,'torque_cases':torques,'scope':'Prescribed foot-force and link-gravity estimate. Does not establish gait performance, impact capacity or thermal endurance.'},indent=2))
 library=[]
 for key in sorted({p['mesh'] for p in model['parts']}):
  instances=[p for p in model['parts'] if p['mesh']==key];p=instances[0]
  if p.get('service_role') in ['keepout','withdrawal']:continue
  record={'id':key,'label':label(key),'instances':[q['name'] for q in instances],'quantity':len(instances),'category':category(p),'material':p['material'],'mass_kg':p['mass_kg'],'dimensions_mm':p['bounds_mm'],'volume_mm3':p.get('volume_mm3'),'note':p.get('note','')}
  if id=='v5' and key=='front_fascia':record['label']='Camera hood and lidar seat'
  if id=='v5' and key=='body_nose_surround':record['label']='Sensor saddle cradle'
  if id=='v7' and key.removesuffix('_right') in ['thigh_inner','thigh_outer']:
   record['label']=('Aft structural carrier half' if key.startswith('thigh_inner') else 'Fore structural carrier half')+(' · right side' if key.endswith('_right') else '')
  for ext,sub in [('step','step'),('stl','stl')]:
   for candidate in [out/sub/f'{key}.{ext}',*([ROOT/'output/limb-refinement'/sub/f'{key}.{ext}'] if id in ['v7','v8'] else []),*([ROOT/'output/integrated-candidate'/sub/f'{key}.{ext}'] if id in ['v3','v4','v5','v6','v7','v8'] else []),ROOT/'output/v0-rounded-body'/sub/f'{key}.{ext}',ROOT/'output/service-design'/sub/f'{key}.{ext}',ROOT/'output'/('step-parts' if ext=='step' else 'stl')/f'{key}.{ext}']:
    if candidate.exists():record[ext]=url(candidate);break
  record['custom']=('step' in record and p['material'] in ['petg','aluminum']) or key in ['pushrod','knee_axle','knee_inner_spacer']
  if bearing_review_failed and key.startswith('shin_') and key.removesuffix('_right') in ['shin_inner','shin_outer']:
   record['note']='Not ready for fabrication: restore continuous bearing support and recheck the pushrod clearance before printing or machining. '+record['note']
  print_file=out/'print-stl'/f'{key}.stl'
  if id=='v14':print_file=out/'prototype-limb/print-stl'/f'{key}.stl'
  if print_file.exists():record['print_stl']=url(print_file)
  plate_file=out/'print-preparation'/f'{key}.3mf'
  if id=='v14':plate_file=out/'prototype-limb/print-3mf'/f'{key}.3mf'
  if plate_file.exists():record['print_3mf']=url(plate_file)
  if id=='v2' and key=='body_nose_surround':record['label']='Camera chassis cradle'
  if id=='v2' and key=='front_fascia':record['label']='Camera hood and face'
  if id=='v2' and key.removesuffix('_right') in ['input_pin','output_pin']:
   record['note']=p.get('note','')+' Conventional fastener is modeled; current on-hand stock quantities remain unverified.'
  library.append(record)
 export_report=out/'assembly-export.json'
 assembly_current=export_report.exists() and json.loads(export_report.read_text()).get('model_sha256')==stamp
 rows.append({'id':id,'title':title,'description':description,'model':url(out/'model.json'),'audit':url(out/'audit.json'),'assembly':url(out/'updated-robot.step') if assembly_current and (out/'updated-robot.step').exists() else None,'model_sha256':stamp,'estimated_mass_kg':mass['base_kg'],'physical_components':sum(p.get('service_role') not in ['keepout','withdrawal'] for p in model['parts']),'parts':library,'scope':('Preview: fixed cover/frame contacts need review. Whole-assembly STEP export is pending; individual part exports are available. ' if folder=='v0-rounded-body' else '')+'CAD prototype. Nominal rigid-part checks do not validate printed strength, flexible cables, tolerances or loaded motion.'})
 reports=[]
 for filename,title in [('installation-fit.json','Installation fit'),('neck-fit.json','Fastener and tool access'),('head-clearance.json','Head clearance sweep'),('chassis-limits.json','Chassis motion limits'),('torques.json','Mass and torque estimates'),('manufacturing-review.json','Print and assembly review'),('limb-folding.json','Knee folding sweep'),('limb-interfaces.json','Limb interfaces and bearing service'),('step-roundtrip.json','STEP solid export checks'),('knee-design-review.json','Knee geometry and load estimates'),('lidar-neck-review.json','Lidar sightlines and assembly'),('saddle-interfaces.json','Sensor saddle interfaces'),('sensor-service.json','Sensor module removal paths'),('compact-thigh-review.json','Motor cup and compactness comparison'),('motor-cup-assembly.json','Motor insertion and shell service')]:
  path=out/filename
  if path.exists() and json.loads(path.read_text()).get('model_sha256')==stamp:reports.append({'title':title,'url':url(path)})
 rows[-1]['reports']=reports
 if id=='v7':
  path=out/'integrated-pitch-review.json'
  if path.exists() and json.loads(path.read_text()).get('model_sha256')==stamp:
   reports.append({'title':'Integrated pitch architecture and tradeoffs','url':url(path)})
 if id=='v8':
  path=out/'seamless-limb-review.json'
  if path.exists() and json.loads(path.read_text()).get('model_sha256')==stamp:
   reports.append({'title':'Rounded limb design and motion comparison','url':url(path)})
 if id=='v9':
  path=out/'manufacturing-thigh-review.json'
  if path.exists() and json.loads(path.read_text()).get('model_sha256')==stamp:
   reports.append({'title':'Thigh manufacturing changes and motion comparison','url':url(path)})
  reports.append({'title':'Inspect print orientation and removable supports','url':'thigh-manufacturing.html'})
 if id=='v10':
  rows[-1]['reference_design']='v9'
  rows[-1]['comparison_parts']=['thigh_inner','thigh_outer','hip_hub','motor_mount_ring',
      'pod_tie_90','pod_tie_210','pod_tie_330','pod_sleeve_90','pod_sleeve_210','pod_sleeve_330',
      'sleeve_0','bolt_0','thigh_clamp_nut_0']
  for filename,title in [('slim-limb-review.json','Slimming measurements and motion comparison'),('slim-structure-review.json','Section and mounting load screens')]:
   path=out/filename
   if path.exists() and json.loads(path.read_text()).get('model_sha256')==stamp:
    reports.append({'title':title,'url':url(path)})
  reports.append({'title':'Inspect print orientation and removable supports','url':'thigh-manufacturing.html?design=v10'})
 if id=='v11':
  rows[-1]['reference_design']='v10'
  rows[-1]['comparison_parts']=['body_center_0','belly_center_0','chassis_beam_-102','chassis_beam_102','chassis_crossmember_-121','chassis_crossmember_121','thigh_outer']
  for filename,title in [('chassis-review.json','Chassis changes and motion comparison'),('chassis-assembly.json','Frame joints and driver access'),('sensor-service.json','Sensor and cover removal paths'),('cnc-access-screen.json','CNC access review flags')]:
   path=out/filename
   if path.exists() and json.loads(path.read_text()).get('model_sha256')==stamp:reports.append({'title':title,'url':url(path)})
 if id=='v12':
  rows[-1]['reference_design']='v11'
  rows[-1]['comparison_parts']=['thigh_outer','chassis_beam_-102','chassis_beam_102']
  for filename,title in [('closed-thigh-review.json','Closed wall and motion comparison'),('foot-clearance.json','Exact boot clearance and continuous bound'),('chassis-assembly.json','Frame joints and driver access'),('sensor-service.json','Sensor and cover removal paths')]:
   path=out/filename
   if path.exists() and json.loads(path.read_text()).get('model_sha256')==stamp:reports.append({'title':title,'url':url(path)})
 if id=='v13':
  rows[-1]['reference_design']='v12'
  rows[-1]['comparison_parts']=['thigh_inner','thigh_outer','shin_inner','shin_outer']
  for filename,title in [('clamp-seat-review.json','Shell clamp geometry'),('foot-clearance.json','Exact boot clearance and continuous bound'),('limb-interfaces.json','Limb interfaces'),('motor-cup-assembly.json','Thigh motor service paths')]:
   path=out/filename
   if path.exists() and json.loads(path.read_text()).get('model_sha256')==stamp:reports.append({'title':title,'url':url(path)})
 if id=='v14':
  rows[-1]['reference_design']='v13';rows[-1]['default_focus']='FL'
  rows[-1]['comparison_parts']=['motor_carrier_1','roll_cartridge_1','thigh_inner','thigh_outer','knee_axle']
  for filename,title in [('paired-roll-interfaces.json','Hip interfaces and bench assembly'),('knee-retention.json','M5 knee retention'),('paired-roll-motion.json','Motion comparison'),('body-integration.json','Pending chassis integration'),('foot-clearance.json','Exact foot-fold clearance'),('prototype-limb/manifest.json','Prototype print inventory')]:
   path=out/filename
   if path.exists() and json.loads(path.read_text()).get('model_sha256')==stamp:reports.append({'title':title,'url':url(path)})
  reports.append({'title':'Prototype printing and hardware guide','url':'../design/prototype-limb.md'})
current=rows[-1]['id']
for row in rows:
 row['archived']=row['id']!=current
 row['lifecycle']='archived' if row['archived'] else 'current-review'
 row['archive_note']='Earlier proposal retained for comparison; use the current design for ongoing part review.' if row['archived'] else ''
for row in rows:
 row['source']={'kind':'generated-reference','label':'Generated CAD reference · native Fusion promotion pending'}
 if row['id']=='v14':
  row['title']='Whole-robot reference · paired hip bearings'
  row['description']='Whole-robot reference before the motor-complex assembly-access fixes. Use the current motor-fit and motor-complex packages for supported, unpowered bench assembly. Chassis contacts, physical fits and loaded strength remain unresolved.'
  for part in row['parts']:
   part.pop('print_stl',None);part.pop('print_3mf',None)
  row['reports']=[r for r in row['reports'] if r['title'] not in ['Prototype print inventory','Prototype printing and hardware guide']]
  row['reports'] += [{'title':'Current motor-fit tests','url':'../design/motor-complex-fit.md'},
                     {'title':'Current motor-complex assembly guide','url':'../design/motor-complex-fit.md'}]
VIEW.mkdir(exist_ok=True);write_catalog(VIEW,{'current_design':current,'designs':rows});print('Viewer catalog:',VIEW,flush=True)
