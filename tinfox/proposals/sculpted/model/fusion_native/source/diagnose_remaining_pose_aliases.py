"""Identify residual occurrence compensation without changing part geometry."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
rows=json.loads((ROOT/'audits/current-native-installed-all.json').read_text())['instances']
by_path={r['native_path']:{'name':n,**r}for n,r in rows.items()}
script=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;p=d.userParameters.itemByName('pose_FL_hip');original=p.expression;assert d.userParameters.itemByName('qa_current_pose_case')is None;results=[];tick=time.monotonic()
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
 results.append(inspect('restored'));assert all(r['checked']==592 for r in results);assert not results[0]['failures']and not results[-1]['failures'];print(json.dumps({'diagnostic_complete':True,'geometry_changed':False,'restored':True,'cases':results,'saved_version':doc.dataFile.versionNumber,'modified':doc.isModified,'elapsed_seconds':time.monotonic()-tick}))
'''.replace('ROWS',repr(by_path))
reply=rpc(script,'remaining-current-pose-alias-diagnostic',timeout=900);assert reply[0]['success'],reply
record=json.loads(reply[0]['message']);(ROOT/'audits/remaining-current-pose-alias-diagnostic.json').write_text(json.dumps(record,indent=2));print({'cases':[(r['case'],len(r['failures']))for r in record['cases']],'elapsed_seconds':record['elapsed_seconds']})
