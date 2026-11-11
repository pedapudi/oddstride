"""Import only the frozen purchased references, never custom part geometry."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];hardware=json.loads((ROOT/'manifests/motor-complex-hardware.json').read_text())
s=(ROOT/'source/native_documents.py').read_text()+'''\nimport adsk.core as core,adsk.fusion as fusion,json,hashlib,tempfile,os,time,re

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;assert not any(c.partNumber=='BENCH_PURCHASED_LIBRARY'for c in d.allComponents);tick=time.monotonic();holder=root.occurrences.addNewComponent(core.Matrix3D.create());holder.component.name='Purchased bench reference library - construction';holder.component.partNumber='BENCH_PURCHASED_LIBRARY';path=os.path.join(tempfile.gettempdir(),'tinfox-native','motor-complex-purchased-references.step');assert hashlib.sha256(open(path,'rb').read()).hexdigest()==SHA;options=app.importManager.createSTEPImportOptions(path);options.isViewFit=False;assert app.importManager.importToTarget2(options,holder.component)is not None;rows=[]
 def inspect(c):
  if c.bRepBodies.count:
   original=c.name;name=re.sub(r' \(\d+\)$','',original);assert name in NAMES,name;c.attributes.add('Tinfox','BenchReferenceName',name);c.partNumber='BENCH_REFERENCE_'+name.replace(' ','_');c.name='Bench '+name;rows.append({'name':name,'import_name':original,'display_name':c.name,'bodies':c.bRepBodies.count,'body_names':[b.name for b in c.bRepBodies]})
  for child in list(c.occurrences):inspect(child.component)
 inspect(holder.component);assert len(rows)==103 and {r['name']for r in rows}==set(NAMES),(len(rows),[r['name']for r in rows]);assert all(r['bodies']==1 for r in rows);holder.isLightBulbOn=False;print(json.dumps({'saved':False,'reference_parts':rows,'source_sha256':SHA,'custom_imports':0,'elapsed_seconds':time.monotonic()-tick}))
'''.replace('SHA',repr(hardware['sha256'])).replace('NAMES',repr([p['name']for p in hardware['parts']]))
r=rpc(s,'motor-complex-reference-library',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/motor-complex-reference-library.json').write_text(json.dumps(record,indent=2));print({'references':len(record['reference_parts']),'seconds':record['elapsed_seconds']})
