"""One native exact-solid interference batch over every visible bench body."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);bench=next(o for o in d.rootComponent.occurrences if o.component.partNumber=='BENCH_MOTOR_COMPLEX');entities=core.ObjectCollection.create();inventory=[];labels={};placed={};tm=fusion.TemporaryBRepManager.get();tick=time.monotonic()
 def walk(o):
  c=o.component;ref=c.attributes.itemByName('Tinfox','BenchReferenceName');role=c.attributes.itemByName('Tinfox','BenchReferenceRole')
  for index,b in enumerate(c.bRepBodies):
   proxy=b.createForAssemblyContext(o);assert proxy.isVisible;name=ref.value if ref else c.partNumber+(' / '+str(index)if c.bRepBodies.count>1 else'');entities.add(proxy);labels[proxy.entityToken]=name;labels[b.entityToken]=name;bb=proxy.boundingBox;inventory.append({'name':name,'path':o.fullPathName,'body_name':b.name,'part_number':c.partNumber,'role':role.value if role else'custom_or_cut_stock','category':'purchased'if role else'cut_stock'if c.partNumber.startswith('CANDIDATE_bt_')else'custom','bounds_mm':[v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]],'native_very_high_volume_mm3':b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000,'volume_checker':'Fusion VeryHigh physical properties; trimmed surfaces may differ numerically from span-aware GK STEP integration.','matrix_cm':list(o.transform2.asArray())})
   copy=tm.copy(b);assert tm.transform(copy,o.transform2);cb=copy.boundingBox;assert max(abs(a-b)*10 for a,b in zip([*cb.minPoint.asArray(),*cb.maxPoint.asArray()],[*bb.minPoint.asArray(),*bb.maxPoint.asArray()]))<1e-5;placed[name]=copy
  for child in c.occurrences:walk(child.createForAssemblyContext(o))
 walk(bench);assert entities.count==121,entities.count
 def label(entity):
  if entity.entityToken in labels:return labels[entity.entityToken]
  for body in entities:
   if entity==body:return labels[body.entityToken]
  matches=[r['name']for r in inventory if r['part_number']==entity.parentComponent.partNumber and r['body_name']==entity.name]
  if len(matches)==1:return matches[0]
  raise AssertionError(('Unknown interference entity',entity.objectType))
 inputs=d.createInterferenceInput(entities);inputs.areCoincidentFacesIncluded=False;results=d.analyzeInterference(inputs);assert results is not None;rows=[]
 for result in results:
  body=result.interferenceBody;preview_volume=abs(body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume)*1000;bb=body.boundingBox;pair=sorted([label(result.entityOne),label(result.entityTwo)]);target=tm.copy(placed[pair[0]]);before=target.volume*1000;success=tm.booleanOperation(target,placed[pair[1]],fusion.BooleanTypes.DifferenceBooleanType);after=target.volume*1000 if success else None;volume=max(0,before-after)if success else None;rows.append({'pair':pair,'volume_mm3':volume,'temporary_boolean_succeeded':success,'target_volume_before_mm3':before,'target_volume_after_mm3':after,'interference_preview_property_mm3':preview_volume,'interference_bounds_mm':[v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]],'classification':'Unclassified detection; exact transformed-body Boolean volume recorded separately from the unreliable transient preview property.'})
 print(json.dumps({'checker':'Fusion Design.analyzeInterference over all121 visible root-context body proxies, then TemporaryBRep Boolean difference on independently transformed actual input solids. Transient preview physical properties are retained only as diagnostics. No model bodies authored.','saved_version':doc.dataFile.versionNumber,'working_modified':doc.isModified,'body_count':121,'potential_pairs':121*120//2,'inventory':inventory,'intersections':rows,'intersection_count':len(rows),'elapsed_seconds':time.monotonic()-tick,'assembly_release_ready':False,'pending':'Explicit classification of each real intersection, independent STEP pair screen, and saved publication gates.'}))
'''
compile(s,'native_bench_all_pairs.py','exec');r=rpc(s,'native-bench-all-pairs',timeout=600,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/native-bench-all-pairs.json').write_text(json.dumps(record,indent=2));print({'body_count':121,'intersections':record['intersection_count'],'seconds':record['elapsed_seconds']})
