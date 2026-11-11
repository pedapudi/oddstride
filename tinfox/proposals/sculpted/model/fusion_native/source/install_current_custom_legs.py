"""Install shared native definitions in the current pose frames; no custom imports."""
import gzip,json,sys
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];target=json.loads((ROOT/'manifests/whole-robot-integration-target.json').read_text());model=json.loads(gzip.decompress((ROOT/target['reference_model']).read_bytes()));mapping=json.loads((ROOT/'manifests/whole-native-component-map-candidate.json').read_text())['parts'];selection=sys.argv[1];assert selection in ['FL','FR','RL','RR'];instances=[]
for p in model['parts']:
 if p.get('leg')!=selection:continue
 key=p['mesh']
 if key.startswith('bench_stock_'):key=p['name'].split('_',1)[1]+('_right'if selection.endswith('R')else'')
 if key in mapping:instances.append({'name':p['name'],'key':key,'group':p['group'],'component':mapping[key]['component_part_number']})
assert len(instances)==26,(selection,len(instances),instances)
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time,os

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;module=next(o for o in root.occurrences if o.component.partNumber=='CURRENT_ASSEMBLY_'+LEG);
 for joint in module.component.joints:
  if joint.isSuppressed:joint.isSuppressed=False
 tick=time.monotonic();rows=[];reference_rows=[];definitions_by_number={}
 for component in d.allComponents:definitions_by_number.setdefault(component.partNumber,[]).append(component)
 progress_path=os.path.join(os.path.expanduser('~'),'Library','Caches','Tinfox','current-native-install-'+LEG+'.json');os.makedirs(os.path.dirname(progress_path),exist_ok=True)
 def progress():
  open(progress_path,'w').write(json.dumps({'leg':LEG,'custom_complete':len(rows),'references_complete':len(reference_rows),'last_custom':rows[-1]['name']if rows else None,'elapsed_seconds':time.monotonic()-tick}))
 def place(frame,component):
  fp=frame.createForAssemblyContext(module);desired=fp.transform2.copy();occ=frame.component.occurrences.addExistingComponent(component,core.Matrix3D.create())
  if max(abs(a-b)for a,b in zip(occ.transform2.asArray(),core.Matrix3D.create().asArray()))>1e-8:
   assert occ.isVaildForEditInitialPosition;assert occ.timelineObject.rollTo(False);occ.initialTransform=desired;d.timeline.moveToEnd()
  occ.isGroundToParent=True;assert max(abs(a-b)for a,b in zip(occ.createForAssemblyContext(fp).transform2.asArray(),desired.asArray()))<1e-8,(component.partNumber,'world placement');return occ
 for item in INSTANCES:
  frame=next(o for o in module.component.occurrences if o.component.partNumber=='CURRENT_FRAME_'+LEG+'_'+item['group']);existing=[o for o in frame.component.occurrences if o.attributes.itemByName('Tinfox','SourceInstance')and o.attributes.itemByName('Tinfox','SourceInstance').value==item['name']];assert len(existing)<=1,item['name'];candidates=definitions_by_number.get(item['component'],[]);assert len(candidates)==1,(item['component'],len(candidates));c=candidates[0];assert c.bRepBodies.count in [1,2] and c.meshBodies.count==0 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),(item['name'],'definition',c.bRepBodies.count,[(f.name,f.errorOrWarningMessage)for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]);occ=existing[0]if existing else place(frame,c);assert occ.component.partNumber==item['component'];occ.attributes.add('Tinfox','SourceInstance',item['name']);occ.attributes.add('Tinfox','NativePart',item['key']);occ.attributes.add('Tinfox','KinematicFrame',LEG+':'+item['group']);occ.attributes.add('Tinfox','GeometryRole','native_cut_stock'if any(x in item['key']for x in ['sleeve','axle'])else'native_custom');matrix=list(occ.transform2.asArray());assert max(abs(a-b)for a,b in zip(matrix,core.Matrix3D.create().asArray()))<1e-8,(item['name'],'local',matrix);rows.append({**item,'bodies':c.bRepBodies.count,'local_matrix_cm':matrix});progress()
 assert sum(r['bodies']for r in rows)==29
 for group in ['mount','roll','thigh','crank','rod','knee']:
  frame=next(o for o in module.component.occurrences if o.component.partNumber=='CURRENT_FRAME_'+LEG+'_'+group);number='CURRENT_REFERENCE_'+LEG+'_'+group;definitions=definitions_by_number.get(number,[]);assert len(definitions)==1,(number,len(definitions));assert not any(o.component.partNumber==number for o in frame.component.occurrences);reference=place(frame,definitions[0]);reference.isLightBulbOn=True;reference.attributes.add('Tinfox','ReferenceFrame',LEG+':'+group);assert max(abs(a-b)for a,b in zip(reference.transform2.asArray(),core.Matrix3D.create().asArray()))<1e-8;reference_rows.append({'group':group,'component':number});progress()
 module.isLightBulbOn=False;print(json.dumps({'passed':True,'saved':False,'leg':LEG,'target_model_sha256':TARGET,'instances':rows,'custom_instances':len(rows),'custom_bodies':29,'reference_groups':reference_rows,'elapsed_seconds':time.monotonic()-tick,'scope':'Native shared instances installed at frame-local identity using explicit initial-position edits in root context and grounded native identity relative to each frame. Actual world placement and restored joint behavior pending.'}))
'''.replace('LEG',repr(selection)).replace('INSTANCES',repr(instances)).replace('TARGET',repr(target['model_sha256']))
compile(s,'install_current_custom_legs.py','exec');tag='current-native-custom-'+selection;r=rpc(s,tag,timeout=1800);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits'/(tag+'.json')).write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k!='instances'})
