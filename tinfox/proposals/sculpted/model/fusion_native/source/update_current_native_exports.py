"""Publish actual native export provenance without promoting incomplete migration."""
import datetime,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];targets=json.loads((ROOT/'manifests/current-targets.json').read_text());screen=json.loads((ROOT/'audits/current-target-geometry-screen.json').read_text());screen={(p['variant'],p['key']):p for p in screen['parts']}
checkpoint=json.loads((ROOT/'manifests/cohesive-leg-status.json').read_text());leg_inventory=json.loads((ROOT/'audits'/f"leg-v{checkpoint['saved_version']}-save-verification.json").read_text());leg_keys={p['part'] for p in leg_inventory['parts'] if p['bodies']}
keys=sorted({p['key'] for target in targets['targets'].values() for p in target['custom_parts']});rows={}
for key in keys:
 label=key;status='legacy_saved_export';cloud_part=key
 if key.startswith(('thigh_inner','thigh_outer','shin_inner','shin_outer')):label='cohesive-'+key.replace('_','-')+'-final';status='saved_leg_v6'
 elif key.startswith(('input_crank','pushrod','sleeve_0','sleeve_1','knee_axle','foot')):label='cohesive-'+key.replace('_','-');status='unsaved_qualified_candidate';cloud_part='CANDIDATE_'+key
 elif key.startswith('knee_inner_spacer'):label='cohesive-'+key.replace('_','-');status='unsaved_qualified_candidate';cloud_part='CANDIDATE_'+key
 elif key.startswith('motor_carrier_'):label='cohesive-'+key.replace('_','-');status='unsaved_candidate';cloud_part='CANDIDATE_'+key
 elif key=='foot_right':label='foot-right-repaired';status='unsaved_repaired_link'
 if key=='body_center_0' and (ROOT/'audits/chassis-v4-save-verification.json').exists():
  verification=json.loads((ROOT/'audits/chassis-v4-save-verification.json').read_text());assert verification['version']==4 and verification['complete'] and not verification['modified'];label='current-body-cover-native';status='saved_chassis_v4_candidate';cloud_part='CANDIDATE_current_body_center_0'
 if (ROOT/'audits/chassis-v5-save-verification.json').exists() and key in ['body_center_0','belly_center_0','chassis_crossmember_121','lidar_lid']:
  verification=json.loads((ROOT/'audits/chassis-v5-save-verification.json').read_text());assert verification['version']==5 and verification['complete'] and not verification['modified'];label={'body_center_0':'current-body-cover-native','belly_center_0':'current-belly-native','chassis_crossmember_121':'current-front-crossmember-native','lidar_lid':'current-lidar-lid-native'}[key];status='saved_chassis_v5';cloud_part=key
 if key=='belly_center_0' and (ROOT/'audits/chassis-v6-save-verification.json').exists():
  verification=json.loads((ROOT/'audits/chassis-v6-save-verification.json').read_text());assert verification['complete'] and not verification['modified'];label='compact-lower-shell-final';status='saved_chassis_v6';cloud_part=key
 if key in ['front_fascia','body_nose_surround']:
  candidate='current-sensor-'+('hood' if key=='front_fascia' else 'cradle')+'-native'
  if (ROOT/'exports'/f'{candidate}.step').exists():label=candidate;status='head_candidate_pending_checkpoint';cloud_part='CANDIDATE_current_'+key
  if (ROOT/'audits/head-v20-save-verification.json').exists():
   head=json.loads((ROOT/'audits/head-v20-save-verification.json').read_text());assert head['complete'] and not head['modified'];status='saved_head_v20';cloud_part=key
 if key in ['front_fascia','body_nose_surround'] and (ROOT/'audits/head-v22-save-verification.json').exists():
  label='current-sensor-'+('hood' if key=='front_fascia' else 'cradle')+'-family-restored';status='saved_head_v22';cloud_part=key
 path=ROOT/'exports'/f'{label}.step'
 if not path.exists():continue
 sha=hashlib.sha256(path.read_bytes()).hexdigest();audit=ROOT/'audits'/f'{label}-geometry.json';evidence=json.loads(audit.read_text()) if audit.exists() else {};qualified=evidence.get('geometric_gate_passed',False) and evidence.get('native_step_sha256')==sha
 if status=='unsaved_qualified_candidate' and not qualified:status='unsaved_candidate'
 checkpoint=json.loads((ROOT/'manifests/cohesive-leg-status.json').read_text())
 if status.startswith('unsaved') and checkpoint.get('saved_version',0)>=7 and checkpoint.get('save_verified'):
  status='saved_leg_v'+str(checkpoint['saved_version']);cloud_part=key
 if key in leg_keys and checkpoint.get('save_verified'):
  status='saved_leg_v'+str(checkpoint['saved_version']);cloud_part=key
 rows[key]={'path':str(path.relative_to(ROOT)),'sha256':sha,'cloud_component':cloud_part,'state':status,'shape_gate_passed_for_matching_export':qualified,'geometry_audit':str(audit.relative_to(ROOT)) if evidence else None,'target_screen':{variant:{'state':screen.get((variant,key),{}).get('state'),'passed':screen.get((variant,key),{}).get('passed',False),'screen_export_hash_matches':screen.get((variant,key),{}).get('native_sha256')==sha} for variant in targets['targets']},'source_of_truth':False}
result={'updated_utc':datetime.datetime.now(datetime.UTC).isoformat(),'root':str(ROOT),'source_model_sha256':{k:v['source_model_sha256'] for k,v in targets['targets'].items()},'parts':rows,'scope':'Local export inventory. Candidate and legacy states remain explicit; geometry evidence only applies to the recorded matching hash. The linked robot assembly maps all source items and the Leg includes qualified hardware placements. Cross-document family propagation, full robot motion/service and manufacturing qualification remain separate gates.'};(ROOT/'manifests/current-native-exports.json').write_text(json.dumps(result,indent=2));print(len(rows))
