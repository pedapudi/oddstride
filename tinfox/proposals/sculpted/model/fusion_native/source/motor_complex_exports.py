"""Explicit canonical-component candidates; publication requires separate gate evidence."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
COMPONENTS={
 'hip_hub':('CANDIDATE_sl_hip_hub','slim-native-hip_hub-restored'),
 'motor_mount_ring':('CANDIDATE_sl_motor_mount_ring','slim-native-motor_mount_ring-restored'),
 'thigh_inner':('CANDIDATE_sl_thigh_inner','slim-native-thigh_inner'),
 'thigh_outer':('CANDIDATE_mc_thigh_outer','motor-complex-native-thigh_outer'),
 'input_crank':('CANDIDATE_mc_input_crank','motor-complex-native-input_crank'),
 **{k:('CANDIDATE_pr_'+k,'paired-native-'+k)for k in ['roll_cartridge_1','roll_stator_backplate_1','roll_inner_spacer_1','roll_outer_spacer_1','roll_inner_backplate_1','roll_outer_retainer_1','motor_carrier_1','hip_stator_closure_1']}}

def inventory():
 target=json.loads((ROOT/'manifests/motor-complex-native-target.json').read_text());rows={}
 for key,(component,label)in COMPONENTS.items():
  path=ROOT/'exports'/(label+'.step');rows[key]={'component_part_number':component,'native_step':str(path.relative_to(ROOT)),'native_step_sha256':hashlib.sha256(path.read_bytes()).hexdigest()if path.exists()else None,'target_step_sha256':target['parts'][key]['sha256'],'saved_version':None,'state':'unsaved_candidate'if path.exists()else 'authoring','assembly_translation_mm':[-5,0,0]if key.startswith(('roll_','motor_carrier','hip_stator_closure'))else[0,0,0]}
 report={'scope':'Detached three-RS02 motor complex only','authority':'generated reference until all native gates and saved-state checks pass','native_source_of_truth':False,'source_target':'manifests/motor-complex-native-target.json','parts':rows,'installed_master_version':62,'installed_leg_version':14,'latest_leg_checkpoint':17,'candidate_exports_are_not_manufacturing_release':True};(ROOT/'manifests/motor-complex-native-exports.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
 r=inventory();print(len(r['parts']),'parts;',sum(bool(p['native_step_sha256'])for p in r['parts'].values()),'exported candidates; authority pending')
