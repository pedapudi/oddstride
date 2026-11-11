"""Retire obsolete pose solvers while retaining shared native construction definitions."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
rows=json.loads((ROOT/'audits/current-native-installed-all.json').read_text())['instances']
by_path={r['native_path']:{'name':n,**r}for n,r in rows.items()}
script=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;p=d.userParameters.itemByName('pose_FL_hip');original=p.expression;assert d.userParameters.itemByName('qa_current_pose_case')is None;results=[];tick=time.monotonic();old_modules=[o for o in root.occurrences if o.component.partNumber in ['ASSEMBLY_FL','ASSEMBLY_FR','ASSEMBLY_RL','ASSEMBLY_RR']];old_joints=[j for o in old_modules for j in o.component.joints];assert len(old_modules)==4 and len(old_joints)==24;retired=[{'name':j.name,'index':j.timelineObject.index,'was_suppressed':j.isSuppressed}for j in old_joints]
 for j in old_joints:j.isSuppressed=True
 assert d.computeAll();assert all(j.isSuppressed for j in old_joints)
 def inspect(label):
  failures=[];checked=0
  for module in root.occurrences:
   if not module.component.partNumber.startswith('CURRENT_ASSEMBLY_'):continue
   for frame in module.component.occurrences:
    if not frame.component.partNumber.startswith('CURRENT_FRAME_'):continue
    fp=frame.createForAssemblyContext(module);fm=list(fp.transform2.asArray())
    def visit(cp):
     nonlocal checked
     if cp.component.bRepBodies.count:
      checked+=1;row=ROWS[cp.fullPathName];lm=row['local_matrix_cm'];wanted=[sum(fm[i*4+k]*lm[k*4+j]for k in range(4))for i in range(4)for j in range(4)];actual=list(cp.transform2.asArray());error=max(abs(a-b)for a,b in zip(wanted,actual))
      if error>1e-7:
       native=cp.nativeObject or cp;failures.append({'name':row['name'],'component':cp.component.partNumber,'path':cp.fullPathName,'matrix_error_cm':error,'wanted':wanted,'actual':actual,'native_matrix':list(native.transform2.asArray()),'initial_matrix':list(native.initialTransform.asArray()),'world_grounded':cp.isGrounded,'parent_grounded':cp.isGroundToParent,'timeline_index':native.timelineObject.index,'features':[{'name':f.name,'type':f.objectType,'index':f.timelineObject.index}for f in cp.component.features]})
     for c in cp.component.occurrences:visit(c.createForAssemblyContext(cp))
    for c in frame.component.occurrences:visit(c.createForAssemblyContext(fp))
  return {'case':label,'checked':checked,'failures':failures}
 results.append(inspect('before'))
 try:p.expression='35 deg';assert d.computeAll();results.append(inspect('hip35'))
 finally:p.expression=original;assert d.computeAll()
 results.append(inspect('restored'));assert all(r['checked']==592 for r in results);assert not results[0]['failures']and not results[-1]['failures'];assert all(j.isSuppressed for j in old_joints)
 for o in old_modules:o.isLightBulbOn=False;o.component.attributes.add('Tinfox','RetirementStatus','Historical assembly and shared construction retained; superseded pose solvers suppressed. Current physical instances are under CURRENT_ASSEMBLY modules.')
 print(json.dumps({'diagnostic_complete':True,'pose_alias_gate_passed':not any(r['failures']for r in results),'geometry_changed':False,'restored':True,'retired_pose_joints':retired,'retained_historical_modules':4,'deleted_definitions':0,'cases':results,'saved_version':doc.dataFile.versionNumber,'modified':doc.isModified,'elapsed_seconds':time.monotonic()-tick}))
'''.replace('ROWS',repr(by_path))
reply=rpc(script,'retired-legacy-pose-driver-check',timeout=1200);assert reply[0]['success'],reply
record=json.loads(reply[0]['message']);(ROOT/'audits/retired-legacy-pose-driver-check.json').write_text(json.dumps(record,indent=2));print({'cases':[(r['case'],len(r['failures']))for r in record['cases']],'elapsed_seconds':record['elapsed_seconds']})
