"""Place purchased references in existing native frames without custom imports."""
import json,gzip
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'manifests/current-exact-hardware-references.json').read_text());groups=[g for g in manifest['groups'] if not g['group'].startswith('Body')]
model=json.loads(gzip.decompress((ROOT/'snapshots/current-hardware'/manifest['source_model_sha256']/'reference-geometry.json.gz').read_bytes()))
for group in groups:group['names']=[p['name'] for p in model['parts'] if (p.get('leg') or 'Body')+'_'+p['group']==group['group']]
keys=[p['part'] for p in json.loads((ROOT/'audits/leg-v9-save-verification.json').read_text())['parts'] if p['bodies']]
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,time,hashlib

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;tick=time.monotonic();custom={c.partNumber:c for c in d.allComponents if c.partNumber in CUSTOM_KEYS};assert len(custom)==44;before={key:(c.features.count,c.sketches.count,c.bRepBodies.count) for key,c in custom.items()};rows=[]
 for item in GROUPS:
  name=item['group'];lname,group=name.split('_',1);frame=next(c for c in d.allComponents if c.partNumber=='FRAME_'+name);leg=next(o for o in root.occurrences if o.component.partNumber=='ASSEMBLY_'+lname);frame_occ=next(o for o in leg.component.occurrences if o.component==frame);existing=[o for o in frame.occurrences if o.component.partNumber=='REFERENCE_'+name];started=time.monotonic()
  if existing:assert len(existing)==1;occ=existing[0];c=occ.component
  else:
   occ=frame.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name=lname+' '+group+' purchased references';c.partNumber='REFERENCE_'+name;path=os.path.join(tempfile.gettempdir(),'tinfox-native','reference-hardware',name+'-reference-assembly.step');assert hashlib.sha256(open(path,'rb').read()).hexdigest()==item['sha256'];options=app.importManager.createSTEPImportOptions(path);options.isViewFit=False;assert app.importManager.importToTarget2(options,c) is not None
  def ground(component):
   for child in list(component.occurrences):
    ground(child.component)
    if not child.isGroundToParent:child.isGroundToParent=True
  ground(c);occ.isGroundToParent=True;frame_occ.createForAssemblyContext(leg).isGroundToParent=False;c.attributes.add('Tinfox','GeometryRole','Purchased hardware/vendor reference only; not custom native authoring');c.attributes.add('Tinfox','SourceSTEP_SHA256',item['sha256']);c.attributes.add('Tinfox','KinematicFrame',name)
  leaves=[]
  def inspect(component,path):
   for b in component.bRepBodies:leaves.append({'name':component.name,'body':b.name,'volume_mm3':b.volume*1000,'path':path})
   for child in list(component.occurrences):inspect(child.component,path+'/'+child.name)
  inspect(c,c.name);assert sorted(r['name'] for r in leaves)==sorted(item['names']),(name,item['names'],leaves);rows.append({'group':name,'parts':leaves,'created':not bool(existing),'seconds':time.monotonic()-started})
 assert d.computeAll()
 for key,c in custom.items():assert before[key]==(c.features.count,c.sketches.count,c.bRepBodies.count),key
 for leg in root.occurrences:
  if leg.component.partNumber.startswith('ASSEMBLY_'):assert all(j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for j in leg.component.joints),leg.name
 assert sum(len(r['parts']) for r in rows)==248;print(json.dumps({'saved':False,'passed':True,'groups':rows,'references':248,'custom_definitions_unchanged':44,'elapsed_seconds':time.monotonic()-tick,'scope':'Vendor/hardware references only. Imported component names and native custom histories verified. Pose placement and reference shape audits follow.'}))
'''.replace('GROUPS',repr(groups)).replace('CUSTOM_KEYS',repr(keys))
r=rpc(s,'native-leg-reference-import',timeout=900);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/native-leg-reference-import.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'references':record['references'],'seconds':record['elapsed_seconds']})
