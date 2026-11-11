"""Verify cloud completion and optionally reopen the same saved native Leg document."""
import json,sys
from pathlib import Path
from run_native import rpc
from motor_complex_exports import COMPONENTS
ROOT=Path(__file__).resolve().parents[1];reopen='--reopen'in sys.argv
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc.dataFile.isComplete and not doc.isModified;file=doc.dataFile;version=file.versionNumber;tick=time.monotonic()
 def capture(document):
  d=fusion.Design.cast(document.products.itemByProductType('DesignProductType'));parts={}
  for key,number in PARTS.items():
   c=next(c for c in d.allComponents if c.partNumber==number);assert c.bRepBodies.count==1 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),key;b=c.bRepBodies.item(0);bb=b.boundingBox;parts[key]={'features':c.features.count,'sketches':c.sketches.count,'faces':b.faces.count,'edges':b.edges.count,'volume_mm3':b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000,'bounds_mm':[v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]]}
  parameters={p.name:p.expression for p in d.userParameters};visible=[o.component.partNumber for o in d.rootComponent.occurrences if o.isLightBulbOn];bench=[o for o in d.rootComponent.occurrences if o.component.partNumber=='BENCH_MOTOR_COMPLEX'];placement={}
  if bench:
   for o in bench[0].component.occurrences:
    a=o.attributes.itemByName('Tinfox','BenchPart')
    if a:placement[a.value]=list(o.createForAssemblyContext(bench[0]).transform2.asArray())
  return {'parts':parts,'parameters':parameters,'visible_root':visible,'placement':placement}
 before=capture(doc)
 if REOPEN:
  assert before['visible_root']==['BENCH_MOTOR_COMPLEX'];assert len(before['placement'])==13;assert doc.close(False);doc=app.documents.open(file,True);assert doc and doc.dataFile.versionNumber==version and doc.dataFile.isComplete and not doc.isModified;after=capture(doc);assert before['parameters']==after['parameters'] and before['visible_root']==after['visible_root'] and before['placement']==after['placement'];
  for key,initial in before['parts'].items():
   restored=after['parts'][key];assert all(initial[k]==restored[k]for k in ['features','sketches','faces','edges']);assert max(abs(a-b)for a,b in zip(initial['bounds_mm'],restored['bounds_mm']))<.000001;assert abs(initial['volume_mm3']-restored['volume_mm3'])<.001
 else:after=before
 print(json.dumps({'passed':True,'file_id':file.id,'version':version,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'reopened':REOPEN,'same_geometry_and_parameters':True,'snapshot':after,'editable_files':len(app.data.personalUseLimits.editableFiles),'elapsed_seconds':time.monotonic()-tick}))
'''.replace('PARTS',repr({k:v[0]for k,v in COMPONENTS.items()})).replace('REOPEN',repr(reopen))
tag='motor-complex-saved-reopen'if reopen else'motor-complex-saved-checkpoint';r=rpc(s,tag,timeout=600,read_only=not reopen);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits'/(tag+'.json')).write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k!='snapshot'})
