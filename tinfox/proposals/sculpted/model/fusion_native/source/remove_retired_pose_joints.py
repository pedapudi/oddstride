"""Remove obsolete solvers without deleting the shared native construction history."""
import gzip,json,sys
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];target=json.loads((ROOT/'manifests/whole-robot-integration-target.json').read_text());model=json.loads(gzip.decompress((ROOT/target['reference_model']).read_bytes()));sys.path.insert(0,str(ROOT.parent));import kinematics as k
k.P.update(model['parameters']);frames={leg:{name:m.tolist()for name,m in k.frames(leg,model['poses']['stand'][leg]).items()}for leg in k.LEGS}
script=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time,os
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;tick=time.monotonic();progress_path=os.path.join(os.path.expanduser('~'),'Library','Caches','Tinfox','retired-pose-removal.json');old=[o for o in root.occurrences if o.component.partNumber in ['ASSEMBLY_FL','ASSEMBLY_FR','ASSEMBLY_RL','ASSEMBLY_RR']];current=[o for o in root.occurrences if o.component.partNumber.startswith('CURRENT_ASSEMBLY_')];assert len(old)==4 and len(current)==4;joints=[j for o in old for j in o.component.joints];assert len(joints)==24;keys={key+suffix for key in ['knee_inner_spacer','shin_clamp_sleeve_37','shin_clamp_sleeve_105','foot','pushrod']for suffix in ['', '_right']};aliases=[child for o in current for frame in o.component.occurrences if frame.component.partNumber.startswith('CURRENT_FRAME_')for child in frame.component.occurrences if child.component.partNumber in keys];assert len(aliases)==20;definitions={child.component.partNumber:child.component for child in aliases};assert len(definitions)==10
 def fingerprint(c):
  return [{'faces':b.faces.count,'edges':b.edges.count,'vertices':[list(v.geometry.asArray())for v in b.vertices],'bounds':[*b.boundingBox.minPoint.asArray(),*b.boundingBox.maxPoint.asArray()]}for b in c.bRepBodies]
 before={key:fingerprint(c)for key,c in definitions.items()};removed=[]
 def progress(stage,**values):open(progress_path,'w').write(json.dumps({'stage':stage,'elapsed_seconds':time.monotonic()-tick,**values}))
 for joint in sorted(joints,key=lambda j:j.timelineObject.index,reverse=True):
  row={'name':joint.name,'old_index':joint.timelineObject.index};assert joint.deleteMe();removed.append(row);progress('retired_old_solver',completed=len(removed),total=24)
 assert d.computeAll();assert all(o.component.joints.count==0 for o in old);reset=[]
 for occ in sorted(aliases,key=lambda o:o.timelineObject.index):
  assert occ.timelineObject.rollTo(False);assert occ.isVaildForEditInitialPosition;occ.initialTransform=core.Matrix3D.create();reset.append(occ.component.partNumber);progress('rebase_reused_definition',completed=len(reset),total=20)
 d.timeline.moveToEnd();assert d.computeAll();definition_checks=[]
 for key,c in definitions.items():
  after=fingerprint(c);assert len(after)==len(before[key]);maximum=0
  for a,b in zip(before[key],after):
   assert (a['faces'],a['edges'],len(a['vertices']))==(b['faces'],b['edges'],len(b['vertices']));assert max(abs(x-y)for x,y in zip(a['bounds'],b['bounds']))<1e-7;error=max((min(sum((x-y)**2 for x,y in zip(v,w))for w in b['vertices'])for v in a['vertices']),default=0)**.5*10;assert error<.00001,(key,error);maximum=max(maximum,error)
  definition_checks.append({'part':key,'maximum_vertex_error_mm':maximum,'topology_and_bounds_preserved':True})
 checks=[]
 for module in current:
  leg=module.component.partNumber[-2:];assert module.component.joints.count==6 and all(j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for j in module.component.joints)
  for frame in module.component.occurrences:
   if not frame.component.partNumber.startswith('CURRENT_FRAME_'):continue
   group=frame.component.partNumber.split('_')[-1];fp=frame.createForAssemblyContext(module);expected=[v*(.1 if j==3 and i<3 else 1)for i,row in enumerate(FRAMES[leg][group])for j,v in enumerate(row)];assert max(abs(a-b)for a,b in zip(fp.transform2.asArray(),expected))<1e-7,(leg,group,'frame')
   for child in frame.component.occurrences:
    cp=child.createForAssemblyContext(fp);error=max(abs(a-b)for a,b in zip(cp.transform2.asArray(),expected));assert error<1e-7,(leg,group,child.component.partNumber,error);checks.append({'part':child.component.partNumber,'leg':leg,'group':group,'matrix_error_cm':error})
 for o in old:o.isLightBulbOn=False;o.component.name='Retired '+o.component.partNumber[-2:]+' construction frames';o.component.attributes.add('Tinfox','RetirementStatus','Obsolete24 pose solvers removed. Native component feature histories remain as shared construction dependencies; current physical assembly uses CURRENT_ASSEMBLY frames.')
 result={'passed':True,'saved':False,'deleted_pose_joints':removed,'retained_historical_modules':4,'deleted_custom_definitions':0,'rebound_occurrences':20,'definition_checks':definition_checks,'standing_checks':checks,'elapsed_seconds':time.monotonic()-tick,'scope':'Permanent obsolete solver retirement. Current shared native part geometry and standing placement preserved; moving pose checks follow.'};open(progress_path,'w').write(json.dumps({'stage':'complete','result':result}));print(json.dumps(result))
'''.replace('FRAMES',repr(frames))
reply=rpc(script,'remove-obsolete-pose-joints',timeout=1800);assert reply[0]['success'],reply;record=json.loads(reply[0]['message']);(ROOT/'audits/removed-obsolete-pose-joints.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k not in ['deleted_pose_joints','standing_checks']})
