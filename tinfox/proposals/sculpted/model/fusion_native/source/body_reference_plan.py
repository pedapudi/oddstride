"""Rigid placement datums for fixed purchased references and removable body details."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def plan():
 references=json.loads((ROOT/'audits/native-body-reference-import.json').read_text())['parts'];assignments={};groups={}
 def assign(name,group,x='0 mm',y='0 mm',z='0 mm'):
  entry={'x':x,'y':y,'z':z};assert group not in groups or groups[group]==entry;groups[group]=entry;assert name not in assignments;assignments[name]=group
 for row in references:
  name=row['name']
  if name.startswith(('chassis_tie_bolt_','chassis_tie_nut_')):
   x,side,_=map(float,name.rsplit('_',3)[1:]);front=1 if x>0 else -1;side=int(side);assign(name,f'corner_{front}_{side}',f'{front}*(robot_hip_x-185 mm)',f'{side}*(robot_roll_y-68 mm)')
  elif name.startswith(('chassis_bolt_','body_service_screw_')):
   side,x,_=map(float,name.rsplit('_',3)[1:]);front=1 if x>0 else -1;side=int(side);assign(name,f'corner_{front}_{side}',f'{front}*(robot_hip_x-185 mm)',f'{side}*(robot_roll_y-68 mm)')
  elif name.startswith(('cassette_screw_','cassette_nut_','battery_access_screw_','battery_')):
   side=int(name.split('_')[1] if name.startswith('battery_') and not name.startswith('battery_access_') else name.rsplit('_',2)[1]);assign(name,f'side_{side}',y=f'{side}*(robot_roll_y-68 mm)')
  elif name.startswith('chassis_brace_screw_'):
   side=int(name.rsplit('_',2)[1]);assign(name,f'brace_{side}',y=f'{side}*(robot_roll_y-68 mm)',z='frame_brace_bottom_z+frame_brace_thickness-3.5 mm')
  elif name.startswith('tray_screw_'):
   side=int(name.rsplit('_',2)[1]);assign(name,f'deck_{side}',y=f'{side}*(robot_roll_y-68 mm)',z='deck_top_z-7.5 mm')
  elif name in ['body_wordmark','body_serial','body_status_dot']:assign(name,'side_-1',y='-1*(robot_roll_y-68 mm)')
  elif name=='electronics_clearance':assign(name,'electronics',z='deck_top_z-7.5 mm')
  elif name in ['lidar','lidar_base']:assign(name,'lidar',x='saddle_x-reference_lidar_base_x',z='saddle_sensor_lid_bottom_z-reference_lidar_lid_base_z')
  elif name in ['status_display','status_display_dial']:assign(name,'roof',z='cover_roof_z-49.5 mm')
  elif name.startswith(('camera_','lens_ring_','iris_','lens_','sensor_')) or name=='depth_sensor':assign(name,'sensor',x='robot_hip_x-185 mm')
  else:raise ValueError('Unassigned frozen body reference: '+name)
 for side in [-1,1]:
  for prefix in ['battery_side_panel_','battery_latch_','battery_access_latch_']:assign(prefix+str(side),f'side_{side}',y=f'{side}*(robot_roll_y-68 mm)')
 assign('lidar_lid','lidar',x='saddle_x-reference_lidar_base_x',z='saddle_sensor_lid_bottom_z-reference_lidar_lid_base_z');assign('power_button','roof',z='cover_roof_z-49.5 mm')
 assert len(assignments)==90
 return {'groups':groups,'assignments':assignments,'source_model_sha256':'929c06ab624ed80192157e99ce43165c1416db414902cb0a36c19d6d2ad50da6','scope':'Placement only. Standard parts keep nominal dimensions. Thickness edits can require different screw lengths; button retention and selected battery interfaces remain unqualified.'}
if __name__=='__main__':
 data=plan();(ROOT/'manifests/body-reference-placement-plan.json').write_text(json.dumps(data,indent=2));print({'groups':len(data['groups']),'items':len(data['assignments'])})
