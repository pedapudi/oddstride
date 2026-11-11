"""Finish the paired native thigh shells with serviceable axle and clamp bores."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text() for p in ['intent_geometry.py','cohesive_limb_intent.py','cohesive_thigh_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);rows=[];paths=[]
 for outer in [False,True]:
  side='outer' if outer else 'inner';c=next(o.component for o in d.rootComponent.occurrences if o.component.partNumber=='CANDIDATE_cohesive_thigh_'+side);assert c.features.count==4;g=IntentGeometry(d,c);n=CohesiveThighIntent(g);body=c.bRepBodies.item(0)
  for key,value in {'lc_axle_head_clearance_radius':7.2,'lc_axle_nut_clearance_radius':9.2,'lc_axle_head_end_y':49.4,'lc_axle_nut_start_y':94.3,'lc_thigh_clamp_sleeve_radius':4.1,'lc_thigh_clamp_head_radius':4.4,'lc_thigh_rear_sleeve_start':58,'lc_thigh_rear_sleeve_end':76,'lc_thigh_front_sleeve_start':48,'lc_thigh_front_sleeve_end':90,'lc_thigh_rear_head_start':43,'lc_thigh_front_head_start':42}.items():g.parameter(key,value)
  def cut(y,depth,definitions,name):
   nonlocal body
   sk=n.circles(y,definitions,name);body=n.extrude_all(sk,depth,name,fusion.FeatureOperations.CutFeatureOperation,body)
  rear=lambda r:[('lc_thigh_clamp_rear_x','lc_thigh_clamp_rear_z',r)]
  front=lambda r:[('lc_thigh_clamp_front_x','lc_thigh_clamp_front_z',r)]
  cut('lc_thigh_inner_y-1 mm','lc_thigh_width+2 mm',[('0 mm','-lc_thigh_length','lc_axle_fit_radius')],'Removable 12 mm axle sleeve fit')
  if outer:cut('lc_axle_nut_start_y','lc_thigh_outer_y-lc_axle_nut_start_y+1 mm',[('0 mm','-lc_thigh_length','lc_axle_nut_clearance_radius')],'M8 flange nut and socket access')
  else:cut('lc_thigh_inner_y-1 mm','lc_axle_head_end_y-lc_thigh_inner_y+1 mm',[('0 mm','-lc_thigh_length','lc_axle_head_clearance_radius')],'M8 axle head access')
  cut('lc_thigh_inner_y-1 mm','lc_thigh_width+2 mm',rear('lc_clamp_bolt_radius')+front('lc_clamp_bolt_radius'),'Two M4 shell closure passages')
  cut('lc_thigh_rear_sleeve_start','lc_thigh_rear_sleeve_end-lc_thigh_rear_sleeve_start',rear('lc_thigh_clamp_sleeve_radius'),'Rear hard compression sleeve')
  if outer:
   sk=n.hexagons('lc_thigh_rear_sleeve_end',rear('lc_clamp_nut_af'),'Captured rear M4 nut');body=n.extrude_all(sk,'lc_thigh_outer_y-lc_thigh_rear_sleeve_end+2 mm','Rear nut service pocket',fusion.FeatureOperations.CutFeatureOperation,body)
  else:cut('lc_thigh_rear_head_start','lc_thigh_rear_sleeve_start-lc_thigh_rear_head_start',rear('lc_thigh_clamp_sleeve_radius'),'Rear M4 screw head access')
  cut('lc_thigh_front_sleeve_start','lc_thigh_front_sleeve_end-lc_thigh_front_sleeve_start',front('lc_thigh_clamp_sleeve_radius'),'Front hard compression sleeve')
  cut('lc_thigh_front_sleeve_end' if outer else 'lc_thigh_front_head_start','8 mm',front('lc_thigh_clamp_head_radius'),'Front M4 screw or nut access')
  assert c.bRepBodies.count==1;path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-thigh-'+side+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));paths.append(path);rows.append({'part':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count})
 print(json.dumps({'parts':rows,'paths':paths,'saved':False}))
'''
r=rpc(s,'cohesive-thigh-hardware',timeout=240);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-thigh-hardware.json').write_text(json.dumps(record,indent=2));print(record)
for path in record['paths']:fetch(path,Path(path).name)
