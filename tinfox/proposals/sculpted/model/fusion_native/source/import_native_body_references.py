"""Place frozen purchased body references alongside native chassis components."""
import json,gzip
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'manifests/current-exact-hardware-references.json').read_text());group=next(g for g in manifest['groups'] if g['group']=='Body_body');model=json.loads(gzip.decompress((ROOT/'snapshots/current-hardware'/manifest['source_model_sha256']/'reference-geometry.json.gz').read_bytes()));names=[p['name'] for p in model['parts'] if not p.get('leg')]
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,time,hashlib

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:R7U8KNNBSA6o3YwVNF2ZQQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert not any(c.partNumber=='REFERENCE_Body_body' for c in d.allComponents);before={c.partNumber:(c.features.count,c.sketches.count,c.bRepBodies.count) for c in d.allComponents};tick=time.monotonic();occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Purchased electronics, power and body fasteners';c.partNumber='REFERENCE_Body_body';path=os.path.join(tempfile.gettempdir(),'tinfox-native','reference-hardware','Body_body-reference-assembly.step');assert hashlib.sha256(open(path,'rb').read()).hexdigest()==EXPECTED_SHA;options=app.importManager.createSTEPImportOptions(path);options.isViewFit=False;assert app.importManager.importToTarget2(options,c) is not None
 def ground(component):
  for child in list(component.occurrences):
   ground(child.component)
   if not child.isGroundToParent:child.isGroundToParent=True
 ground(c);occ.isGrounded=True;assert d.computeAll();leaves=[]
 def bodies(component):
  result=list(component.bRepBodies)
  for child in list(component.occurrences):result+=bodies(child.component)
  return result
 def inspect(component):
  if component.name in NAMES:
   solids=bodies(component);assert solids,component.name;bounds=[min(getattr(b.boundingBox.minPoint,a) for b in solids)*10 for a in ['x','y','z']]+[max(getattr(b.boundingBox.maxPoint,a) for b in solids)*10 for a in ['x','y','z']];leaves.append({'name':component.name,'bodies':len(solids),'volume_mm3':sum(b.volume for b in solids)*1000,'bounds_mm':bounds});return
  for child in list(component.occurrences):inspect(child.component)
 inspect(c);assert sorted(r['name'] for r in leaves)==sorted(NAMES),{'actual':[r['name'] for r in leaves],'expected':NAMES};assert len(leaves)==82
 for key,counts in before.items():
  part=next(c for c in d.allComponents if c.partNumber==key);assert counts==(part.features.count,part.sketches.count,part.bRepBodies.count),key
 c.attributes.add('Tinfox','GeometryRole','Purchased hardware/vendor reference only; not custom native authoring');c.attributes.add('Tinfox','SourceSTEP_SHA256',EXPECTED_SHA);print(json.dumps({'passed':True,'saved':False,'parts':leaves,'reference_instances':82,'custom_histories_unchanged':True,'elapsed_seconds':time.monotonic()-tick}))
'''.replace('EXPECTED_SHA',repr(group['sha256'])).replace('NAMES',repr(names))
r=rpc(s,'native-body-reference-import',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/native-body-reference-import.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'references':82,'seconds':record['elapsed_seconds']})
