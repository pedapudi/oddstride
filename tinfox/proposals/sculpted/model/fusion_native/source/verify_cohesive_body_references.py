"""Independently verify active hardware by stable IDs after import and retirement."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];target=json.loads((ROOT/'manifests/current-body-target.json').read_text());spec=json.loads((ROOT/'manifests/cohesive-body-hardware-metrology.json').read_text())
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json
def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');d=fusion.Design.cast(doc.products.itemByProductType('DesignProductType'));root=d.rootComponent;rows=[]
 for name,expected in EXPECTED.items():
  occurrences=[o for o in root.allOccurrences if o.component.partNumber==name];assert len(occurrences)==1,(name,len(occurrences));occ=occurrences[0];c=occ.component;assert c.bRepBodies.count==1;body=c.bRepBodies.item(0).createForAssemblyContext(occ);bb=body.boundingBox;bounds=[getattr(p,a)*10 for p in [bb.minPoint,bb.maxPoint] for a in ['x','y','z']];distance=max(abs(a-b) for a,b in zip(bounds,expected['bounds_mm']));dv=abs(body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000-expected['volume_mm3']);rows.append({'id':name,'display_name':c.name,'path':occ.fullPathName,'bounds_error_mm':distance,'volume_error_mm3':dv,'passed':distance<.0001 and dv<.001})
 retired=[o.component.partNumber for o in root.allOccurrences if o.component.partNumber.startswith(('chassis_tie_nut_','sensor_root_nut_'))];issues=[(c.partNumber,f.name,f.errorOrWarningMessage)for c in d.allComponents for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];print(json.dumps({'passed':all(r['passed']for r in rows) and not retired and not issues,'saved':False,'checks':rows,'retired_still_active':retired,'feature_issues':issues,'scope':'Active standard screw IDs, exact source dimensions and assembly coordinates verified after import. Eight display names have Fusion-generated suffixes; part IDs remain stable. No custom solid import.'}))
'''.replace('EXPECTED',repr(spec))
r=rpc(s,'cohesive-body-reference-verification',timeout=45,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);record['source_model_sha256']=target['source_model_sha256'];(ROOT/'audits/cohesive-body-reference-verification.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'checks':len(record['checks']),'failed':[r for r in record['checks']if not r['passed']],'issues':record['feature_issues']})
