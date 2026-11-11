"""Import one standard reference group into its existing native motion frame."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
expected=next(g['sha256'] for g in json.loads((ROOT/'manifests/current-exact-hardware-references.json').read_text())['groups'] if g['group']=='FL_mount')
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,time,hashlib

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert not any(c.partNumber=='REFERENCE_FL_mount' for c in d.allComponents);frame=next(c for c in d.allComponents if c.partNumber=='FRAME_FL_mount');leg=next(o for o in root.occurrences if o.component.partNumber=='ASSEMBLY_FL');frame_occ=next(o for o in leg.component.occurrences if o.component==frame);before={c.partNumber:(c.features.count,c.sketches.count,c.bRepBodies.count) for c in d.allComponents if c.partNumber and not c.partNumber.startswith(('FRAME_','ASSEMBLY_','DATUM_'))};tick=time.monotonic();occ=frame.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Fixed shoulder hardware references';c.partNumber='REFERENCE_FL_mount';path=os.path.join(tempfile.gettempdir(),'tinfox-native','reference-hardware','FL_mount-reference-assembly.step');assert hashlib.sha256(open(path,'rb').read()).hexdigest()==EXPECTED_SHA;options=app.importManager.createSTEPImportOptions(path);options.isViewFit=False;result=app.importManager.importToTarget2(options,c);assert result is not None;rows=[]
 def visit(component,path):
  for b in component.bRepBodies:rows.append({'path':path,'component':component.name,'body':b.name,'volume_mm3':b.volume*1000,'bounds_mm':[v*10 for v in b.boundingBox.minPoint.asArray()+b.boundingBox.maxPoint.asArray()]})
  for child in component.occurrences:
   child.isGroundToParent=True;visit(child.component,path+'/'+child.name)
 visit(c,c.name);occ.isGroundToParent=True;frame_occ.createForAssemblyContext(leg).isGroundToParent=False;assert d.computeAll();assert len(rows)==10,rows
 for key,counts in before.items():
  component=next(c for c in d.allComponents if c.partNumber==key);assert counts==(component.features.count,component.sketches.count,component.bRepBodies.count),key
 assert all(j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for j in leg.component.joints);print(json.dumps({'saved':False,'reference_only':True,'rows':rows,'elapsed_seconds':time.monotonic()-tick,'scope':'One ten-part vendor/hardware import probe; no custom geometry was imported.'}))
'''.replace('EXPECTED_SHA',repr(expected))
r=rpc(s,'reference-hardware-import-probe',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/reference-hardware-import-probe.json').write_text(json.dumps(record,indent=2));print(record)
