"""Bind real native feature dimensions to nominal hardware and process fits."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text() for p in ['intent_geometry.py','leg_fit_parameters.py'])+'''
def run(_context: str):
 import json,re,time
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';assert doc.dataFile.versionNumber>=8;d=fusion.Design.cast(app.activeProduct);components={c.partNumber:c for c in d.allComponents if c.partNumber};physical={key:c for key,c in components.items() if c.bRepBodies.count};assert len(physical)==44;assert d.userParameters.itemByName('fit_process_cnc') is None;tick=time.monotonic()
 def state(c):return {'volumes':[b.volume for b in c.bRepBodies],'bounds':[[*b.boundingBox.minPoint.asArray(),*b.boundingBox.maxPoint.asArray()] for b in c.bRepBodies],'faces':[b.faces.count for b in c.bRepBodies],'edges':[b.edges.count for b in c.bRepBodies]}
 before={key:state(c) for key,c in physical.items()};n=LegFitParameters(IntentGeometry(d,d.rootComponent));bindings=n.apply();features=[]
 mappings={
 'input_crank':{'lc_pin_shoulder_clearance':'fit_crank_pin_shoulder_radius','lc_pin_head_clearance':'fit_crank_pin_head_radius','lc_pin_nut_af':'fit_crank_pin_nut_af','lc_rs02_output_hole_radius':'fit_crank_output_hole_radius','lc_rs02_output_head_radius':'fit_crank_output_head_radius'},
 'motor_carrier_1':{'lc_rs02_output_hole_radius':'fit_carrier_output_hole_radius'},
 'motor_carrier_-1':{'lc_rs02_output_hole_radius':'fit_carrier_output_hole_radius'},
 'knee_inner_spacer':{'lc_axle_fit_radius':'fit_metal_spacer_axle_bore_radius'},
 }
 for key,mapping in mappings.items():
  count=0
  for parameter in components[key].modelParameters:
   old=parameter.expression;new=old
   for source,target in mapping.items():new=re.sub(r'\\b'+source+r'\\b',target,new)
   if new!=old:parameter.expression=new;features.append({'part':key,'model_parameter':parameter.name,'old_expression':old,'expression':new});count+=1
  assert count>=len(mapping),(key,count,mapping)
 for key in ['shin_inner','shin_outer','thigh_inner','thigh_outer']:
  c=components[key];plane=next(p for p in c.constructionPlanes if p.name in ['Structural clamshell split','Shared limb split datum']);parameter=plane.definition.offset;old=parameter.expression;sign='+' if key.endswith('outer') else '-';parameter.expression='lc_shin_split_y'+sign+'(fit_shell_total_seam_gap+fit_seam_compensation)/2';features.append({'part':key,'feature':plane.name,'old_expression':old,'expression':parameter.expression})
 c=components['shin_design_master'];plane=next(p for p in c.constructionPlanes if p.name=='Bushing flange clearance datum');old=plane.definition.offset.expression;plane.definition.offset.expression='fit_fork_center_y-lc_drive_fork_gap/2';features.append({'part':c.partNumber,'feature':plane.name,'old_expression':old,'expression':plane.definition.offset.expression});feature=next(f for f in c.features.extrudeFeatures if f.name.startswith('Bushing flange clearance'));old=feature.extentOne.distance.expression;feature.extentOne.distance.expression='lc_drive_fork_gap';features.append({'part':c.partNumber,'feature':feature.name,'old_expression':old,'expression':feature.extentOne.distance.expression})
 assert d.computeAll();worst=0
 for key,c in physical.items():
  assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),key;after=state(c);assert after['faces']==before[key]['faces'] and after['edges']==before[key]['edges'],(key,before[key],after);error=max(abs(a-b) for aa,bb in zip(before[key]['bounds'],after['bounds']) for a,b in zip(aa,bb));worst=max(worst,error);assert error<1e-7,(key,error);assert max(abs(a-b) for a,b in zip(before[key]['volumes'],after['volumes']))<1e-5,(key,before[key]['volumes'],after['volumes'])
 print(json.dumps({'passed':True,'saved':False,'baseline_geometry_unchanged':True,'user_parameter_bindings':bindings,'native_feature_bindings':features,'maximum_bound_error_cm':worst,'fit_parameter_count':sum(p.name.startswith('fit_') for p in d.userParameters),'elapsed_seconds':time.monotonic()-tick,'physical_fit_qualified':False,'remaining':'Actual edit/restore propagation and tolerance stack checks are next; vendor pilot, connector envelopes, locating features and complete rigid-motion uncertainty remain incomplete.'}))
'''
r=rpc(s,'native-leg-fit-bindings',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/native-leg-fit-bindings.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k not in ['user_parameter_bindings','native_feature_bindings']})
