"""Classify individual measured intersections; no geometry edits or exclusions."""
from pathlib import Path
import hashlib,json,math,re
H=Path(__file__).resolve().parent
path=H/'native-bench-static-screen.json';raw=path.read_bytes();report=json.loads(raw)
rules=[
 ('Roll motor',r'FL_roll_stator_bolt_(\d+)',range(0,360,40),1.5,3,0,[-85.5,-82.5]),
 ('Roll motor',r'FL_roll_output_bolt_(\d+)',range(0,360,60),2,4.2,0,[-82.7,-78.5]),
 ('Hip pitch motor',r'Hip output M4x8 (\d+)',range(0,360,60),2,4.3,1,[-4.3,0]),
 ('Hip pitch motor',r'FL_hip_stator_bolt_(\d+)',range(0,360,40),1.5,5.1,1,[-9.1,-4]),
 ('Knee pitch motor',r'Knee output M4x12 (\d+)',range(0,360,60),2,5.4,1,[49,54.4]),
 ('Knee pitch motor',r'Knee stator M3x8 (\d+)',range(20,380,40),1.5,4.9,1,[45.5,50.4])]
classified=[];unexpected=[]
for check in report['positive_pairs']:
 row=dict(check);row['classification']='unexpected_unresolved';row['accepted']=False
 for motor,regex,angles,radius,penetration,axis,interval in rules:
  if motor not in row['pair']:continue
  other=next(name for name in row['pair'] if name!=motor);match=re.fullmatch(regex,other)
  if not match or int(match[1])not in angles:continue
  target=math.pi*radius**2*penetration;measured=row['overlap_mm3'];bounds=row['intersection_bounds_mm'];err=max(abs(bounds[axis]-interval[0]),abs(bounds[axis+3]-interval[1]))
  row.update(classification='manufacturer_mounting_thread_volume_in_unthreaded_motor_reference',exception_basis='This exact screw role/angle, measured shaft volume and axial penetration match the documented motor mounting interface; the motor envelope omits its threaded void.',manufacturer_drawing='https://www.robstride.com/assets/product_manual_robStride02-e7f9f7c4.pdf',shaft_radius_mm=radius,penetration_mm=penetration,expected_overlap_volume_mm3=target,measured_volume_error_mm3=abs(measured-target),expected_axial_interval_mm=interval,measured_axial_interval_error_mm=err,accepted=abs(measured-target)<1e-4 and err<1e-5)
  break
 if not row['accepted']:
  patterns=[re.fullmatch(r'FL_(hip|knee|roll)_port_(-1|1)_(boot|plug|cable)',name)for name in row['pair']]
  if all(patterns) and patterns[0].groups()[:2]==patterns[1].groups()[:2] and set(m[3]for m in patterns)in ({'boot','plug'},{'boot','cable'}):
   row.update(classification='explicit_connected_connector_protective_envelope',exception_basis='The same named motor port has a protective boot reference deliberately enclosing part of its plug or cable reference. These are connected reference envelopes, not custom structure or fasteners.',accepted=True)
 classified.append(row)
 if not row['accepted']:unexpected.append(row)
categories=report['category_counts'];label_checks=[]
for binding in report['identity_binding']:
 norm=lambda s:re.sub('[^a-z0-9]','',s.lower())
 component=re.sub(r':\d+$','',binding['inventory']['path'].split('+')[-1])
 label_checks.append(dict(name=binding['inventory']['name'],native_occurrence_component=component,step_label=binding['step_label'],occurrence_label_matches=norm(component)in norm(binding['step_label']),other_label_matches=binding['semantic_label_matches']))
label_unmatched=[c['name']for c in label_checks if not c['occurrence_label_matches'] and not any(c['other_label_matches'].values())]
counts_ok=categories.get('custom')==13 and sum(v for k,v in categories.items()if k in ('stock','cut_stock'))==8 and categories.get('purchased')==100 and report['motor_count']==3 and report['connector_count']==24
valid=all(c.get('result_valid',False) for c in report['checks'])
native=H.parents[2]/'proposals/sculpted/model/fusion_native'
sources={}
for label,name in [('native_split','corrected-thigh-split-native.json'),('saved_reopen','corrected-bench-saved-reopen.json')]:
 p=native/'audits'/name;data=p.read_bytes();frozen=H/'static-bench-input'/report['step']['sha256']/name;frozen.write_bytes(data)
 sources[label]=dict(path=str(p),frozen_path=str(frozen),sha256=hashlib.sha256(data).hexdigest(),report=json.loads(data))
split=sources['native_split']['report'];reopen=sources['saved_reopen']['report']
proof=split['passed'] and split['saved_version']==24 and not split['working_modified'] and split['positive_interference_count']==0 and not split['coincident_faces_included'] and len(split['rows'])==2 and all(r['native_difference_succeeded'] and r['difference_mm3']==0 and r['before_volume_mm3']>0 and r['faces_before']==r['faces_after'] and r['edges_before']==r['edges_after'] for r in split['rows']) and reopen['passed'] and reopen['version']==24 and reopen['reopened'] and reopen['same_geometry_and_parameters'] and not reopen['modified']
resolved=[];unresolved=[]
for err in report['errors']:
 if proof and set(err['pair'])=={'CANDIDATE_sl_thigh_inner','CANDIDATE_mc_thigh_outer'}:
  resolved.append(dict(primary_failure=err,resolution='Saved native exact solids: zero material interference and two unchanged bidirectional temporary differences, with unchanged face/edge counts. Saved-reopen audit binds the same geometry to the exported checkpoint.',evidence=sources,independent_common_retries_path=str(H/'thigh-common-retries.json'),note='The failed external Common and two failed non-destructive retries remain failures. Native body.volume is a separate physical-property method; it is not compared numerically to STEP GK or native VeryHigh volume.'))
 else:unresolved.append(err)
out=dict(passed=not unexpected and not unresolved and not label_unmatched and counts_ok,status='independent_nominal_static_screen_classified_with_explicit_native_split_resolution',raw_screen_path=str(path),raw_screen_sha256=hashlib.sha256(raw).hexdigest(),assembly_step=report['step'],inventory=report['inventory'],category_counts=categories,motor_count=report['motor_count'],connector_count=report['connector_count'],body_count=report['solid_count'],total_pairs=report['total_pairs'],aabb_pruned_pairs=report['aabb_pruned_pairs'],exact_pair_count=report['exact_pair_count'],positive_intersection_count=len(classified),each_positive_pair=classified,unexpected_pairs=unexpected,preserved_primary_boolean_errors=report['errors'],all_external_boolean_results_valid=valid,resolved_boolean_exceptions=resolved,unresolved_boolean_errors=unresolved,all_pairs_have_valid_resolution=not unresolved,semantic_label_checks=label_checks,unmatched_semantic_labels=label_unmatched,counts_verified=counts_ok,conditions='Actual corrected native assembly at its exported bench pose; all possible pairs considered, AABB disjoint pairs removed, every remaining pair checked on exact BReps. One failed external Common is resolved by a documented targeted native solid check. No same-group or category blanket exclusion.',limitations=['Static nominal rigid geometry only; manufacturing tolerance, flexible cables, loaded motion, print strength and physical fit remain unqualified.','Motor-thread exceptions concern verified reference envelopes, not proof that purchased motor threads and screw lengths physically fit.','Connected boot/plug/cable envelopes are placeholders; their intentional overlap does not qualify actual connector or strain-relief design.','The primary external coincident-split Boolean and both retries remain invalid; the overall nominal static verdict uses the separately retained saved native resolution for that exact pair.'])
(H/'native-bench-static-classification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(passed=out['passed'],counts=categories,classified=len(classified),unexpected=unexpected,counts_ok=counts_ok,label_unmatched=label_unmatched,boolean_valid=valid),indent=2))
