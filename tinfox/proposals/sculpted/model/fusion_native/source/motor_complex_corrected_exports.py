"""Explicit native revision map; publication state is held in the authority manifest."""
from motor_complex_exports import COMPONENTS as BASE_COMPONENTS
COMPONENTS=dict(BASE_COMPONENTS)
COMPONENTS.update({
 'hip_hub':('CANDIDATE_hc_hip_hub','case-relieved-native-hip_hub'),
 'motor_mount_ring':('CANDIDATE_ks_motor_mount_ring','knee-seated-native-motor_mount_ring'),
 'motor_carrier_1':('CANDIDATE_rc_motor_carrier_1','recessed-restored-motor_carrier_1'),
 'hip_stator_closure_1':('CANDIDATE_rc_hip_stator_closure_1','recessed-restored-hip_stator_closure_1'),
})
RELATED={
 'motor_carrier_-1':('CANDIDATE_rc_motor_carrier_-1','recessed-restored-motor_carrier_-1'),
 'hip_hub_right':('CANDIDATE_hc_hip_hub_right','case-relieved-native-hip_hub_right'),
 'motor_mount_ring_right':('CANDIDATE_ks_motor_mount_ring_right','knee-seated-native-motor_mount_ring_right'),
}
ASSEMBLY_INVENTORY={'custom_parts':13,'cut_stock_bodies':8,'purchased_references':100,'motors':3,'connector_bodies':24,'total_visible_bodies':121}
