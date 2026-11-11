"""Resolve a coincident-shell external-kernel diagnostic on saved native bodies."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();assert doc.dataFile.versionNumber==24 and doc.dataFile.isComplete and not doc.isModified;d=fusion.Design.cast(app.activeProduct);bench=next(o for o in d.rootComponent.occurrences if o.component.partNumber=='BENCH_MOTOR_COMPLEX');entities=core.ObjectCollection.create();tm=fusion.TemporaryBRepManager.get();placed={};rows=[]
 for o in bench.component.occurrences:
  a=o.attributes.itemByName('Tinfox','BenchPart')
  if a and a.value in ['thigh_inner','thigh_outer']:
   context=o.createForAssemblyContext(bench);b=o.component.bRepBodies.item(0);proxy=b.createForAssemblyContext(context);assert proxy.isVisible;entities.add(proxy);copy=tm.copy(b);assert tm.transform(copy,context.transform2);placed[a.value]=copy
 assert entities.count==2
 inp=d.createInterferenceInput(entities);inp.areCoincidentFacesIncluded=False;results=d.analyzeInterference(inp);assert results is not None;assert results.count==0,results.count
 for first,second in [('thigh_inner','thigh_outer'),('thigh_outer','thigh_inner')]:
  copy=tm.copy(placed[first]);before=copy.volume*1000;assert before>1000;faces=copy.faces.count;edges=copy.edges.count;ok=tm.booleanOperation(copy,tm.copy(placed[second]),fusion.BooleanTypes.DifferenceBooleanType);assert ok;after=copy.volume*1000;assert abs(before-after)<.002;rows.append({'target':first,'tool':second,'native_difference_succeeded':ok,'before_volume_mm3':before,'after_volume_mm3':after,'difference_mm3':before-after,'faces_before':faces,'faces_after':copy.faces.count,'edges_before':edges,'edges_after':copy.edges.count})
 assert not doc.isModified;print(json.dumps({'passed':True,'saved_version':24,'complete':doc.dataFile.isComplete,'working_modified':doc.isModified,'checker':'Fusion exact native placed solids; analyzeInterference excludes coincident faces, followed by bidirectional temporary Boolean differences. No geometry mutation.','positive_interference_count':results.count,'coincident_faces_included':False,'rows':rows,'scope':'Inner/outer structural thigh nominal split only; resolves external invalid coincident Common diagnostic, not a manufacturing fit or strength test.'}))
'''
r=rpc(s,'corrected-thigh-split-native',timeout=120,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/corrected-thigh-split-native.json').write_text(json.dumps(record,indent=2));print(record)
