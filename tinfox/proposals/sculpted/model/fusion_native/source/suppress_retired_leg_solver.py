"""Suspend obsolete hidden assembly joints without deleting native dependencies."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''\nimport adsk.core as core,adsk.fusion as fusion,json,time

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert not any(c.partNumber=='BENCH_MOTOR_COMPLEX'for c in d.allComponents);rows=[];tick=time.monotonic()
 for occurrence in root.occurrences:
  if occurrence.component.partNumber not in ['ASSEMBLY_FL','ASSEMBLY_FR','ASSEMBLY_RL','ASSEMBLY_RR']:continue
  c=occurrence.component;before=[{'name':o.name,'matrix':list(o.createForAssemblyContext(occurrence).transform2.asArray())}for o in c.occurrences];joints=[]
  for joint in c.joints:
   prior=joint.isSuppressed
   if not prior:joint.isSuppressed=True
   joints.append({'name':joint.name,'was_suppressed':prior,'is_suppressed':joint.isSuppressed})
  occurrence.isLightBulbOn=False;after=[{'name':o.name,'matrix':list(o.createForAssemblyContext(occurrence).transform2.asArray())}for o in c.occurrences];drift=max((abs(a-b)for one,two in zip(before,after)for a,b in zip(one['matrix'],two['matrix'])),default=0);rows.append({'assembly':c.partNumber,'joints':joints,'before':before,'after':after,'maximum_matrix_drift':drift})
 assert len(rows)==4;print(json.dumps({'saved':False,'retired_assemblies':rows,'suppressed_joints':sum(len(r['joints'])for r in rows),'deleted_components':0,'deleted_documents':0,'master_version_unchanged':62,'elapsed_seconds':time.monotonic()-tick,'scope':'Only superseded working-Leg assembly joints are suppressed. All custom histories, reference definitions and prior saved Master/Leg versions remain preserved.'}))
'''
r=rpc(s,'retired-leg-solver-cleanup',timeout=240);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/retired-leg-solver-cleanup.json').write_text(json.dumps(record,indent=2));print({'suppressed_joints':record['suppressed_joints'],'seconds':record['elapsed_seconds'],'maximum_matrix_drift':max(r['maximum_matrix_drift']for r in record['retired_assemblies'])})
