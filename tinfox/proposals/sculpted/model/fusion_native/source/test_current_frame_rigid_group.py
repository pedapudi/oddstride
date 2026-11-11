"""Qualify one explicit moving-frame rigid group before extending the relationship."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;module=next(o for o in root.occurrences if o.component.partNumber=='CURRENT_ASSEMBLY_FL');frame=next(o for o in module.component.occurrences if o.component.partNumber=='CURRENT_FRAME_FL_roll');fp=frame.createForAssemblyContext(module);assert not any(g.name=='FL roll mounted components'for g in root.rigidGroups);collection=core.ObjectCollection.create();collection.add(fp);members=[];tick=time.monotonic()
 for child in frame.component.occurrences:
  cp=child.createForAssemblyContext(fp)
  if cp.isGrounded:cp.isGrounded=False
  if cp.isGroundToParent:cp.isGroundToParent=False
  collection.add(cp);members.append(child.component.partNumber)
 group=root.rigidGroups.add(collection,False);assert group;group.name='FL roll mounted components';group.attributes.add('Tinfox','CurrentFrameAssembly','FL:roll');parameter=d.userParameters.itemByName('pose_FL_roll');before=parameter.expression;rows=[]
 def state(label):
  fresh_frame=frame.createForAssemblyContext(module);expected=fresh_frame.transform2;checks=[]
  for child in frame.component.occurrences:
   cp=child.createForAssemblyContext(fresh_frame);error=max(abs(a-b)for a,b in zip(cp.transform2.asArray(),expected.asArray()));assert error<1e-7,(label,child.component.partNumber,'matrix',error);vertex_error=None
   if child.component.bRepBodies.count:
    v=child.component.bRepBodies.item(0).vertices.item(0);p=v.geometry.copy();p.transformBy(expected);q=v.createForAssemblyContext(cp).geometry;vertex_error=p.distanceTo(q)*10;assert vertex_error<1e-6,(label,child.component.partNumber,'vertex',vertex_error)
   checks.append({'part':child.component.partNumber,'matrix_error_cm':error,'same_vertex_error_mm':vertex_error})
  return {'label':label,'checks':checks}
 rows.append(state('nominal'))
 try:parameter.expression='7 deg';rows.append(state('roll7'))
 finally:parameter.expression=before
 rows.append(state('restored'));print(json.dumps({'passed':True,'saved':False,'group':group.name,'members':members,'checks':rows,'elapsed_seconds':time.monotonic()-tick,'scope':'One current roll frame uses explicit rigid relationships instead of history-dependent child grounding; actual matrices and identical native vertices follow a7degree pose edit and restore.'}))
'''
compile(s,'test_current_frame_rigid_group.py','exec');a=rpc(s,'current-frame-rigid-group-proof',timeout=300);assert a[0]['success'],a;rec=json.loads(a[0]['message']);(ROOT/'audits/current-frame-rigid-group-proof.json').write_text(json.dumps(rec,indent=2));print({k:v for k,v in rec.items()if k!='checks'})
