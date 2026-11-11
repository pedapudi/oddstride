"""Check the candidate halves and actual purchased bearing references in Fusion."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
def run(_context: str):
 import adsk.core as core,adsk.fusion as fusion,json,time
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;before=root.occurrences.count;parts={key:next(o for o in root.occurrences if o.component.partNumber=='CANDIDATE_round_shin_'+key)for key in['inner','outer']};temp=[];tick=time.monotonic()
 for key in['bearing_inner','bearing_outer']:
  source=next(o.component for o in root.allOccurrences if o.component.partNumber=='FL_'+key);o=root.occurrences.addExistingComponent(source,core.Matrix3D.create());o.isLightBulbOn=False;parts[key]=o;temp.append(o)
 rows=[]
 for a,b in [('inner','outer')]+[(half,bearing)for half in['inner','outer']for bearing in['bearing_inner','bearing_outer']]:
  objects=core.ObjectCollection.create()
  for key in[a,b]:
   o=parts[key];assert o.component.bRepBodies.count==1;objects.add(o.component.bRepBodies.item(0).createForAssemblyContext(o))
  inp=d.createInterferenceInput(objects);inp.areCoincidentFacesIncluded=False;result=d.analyzeInterference(inp);assert result is not None;volume=sum(abs(x.interferenceBody.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume)*1000 for x in result);rows.append({'pair':[a,b],'overlap_mm3':volume,'passed':volume<1e-6})
 for o in temp:assert o.deleteMe()
 assert root.occurrences.count==before;print(json.dumps({'passed':all(r['passed']for r in rows),'checks':rows,'saved_leg_base_version':doc.dataFile.versionNumber,'working_candidates_unsaved':doc.isModified,'temporary_instances_removed':True,'elapsed_seconds':time.monotonic()-tick,'checker':'Fusion native interference on actual candidate bodies and purchased bearing references in a common local frame','scope':'Two half interfaces and four nominal bearing fits. Local source-hashed service audit covers washers, screws and extraction paths. No strength or process-fit qualification.'}))
'''
r=rpc(s,'rounded-shin-native-interfaces',timeout=90);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/rounded-shin-native-interfaces.json').write_text(json.dumps(record,indent=2));print(record)
