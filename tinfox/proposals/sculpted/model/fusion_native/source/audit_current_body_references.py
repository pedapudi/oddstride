"""Reuse the existing parametric body-reference placement after exact current-target binding."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];manifest=json.loads((ROOT/'manifests/whole-purchased-reference-groups.json').read_text());parts={p['name']:p for p in manifest['parts']if p['group']=='Body_body'};assert len(parts)==72
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'chassis');d=fusion.Design.cast(doc.products.itemByProductType('DesignProductType'));rows=[];tick=time.monotonic()
 for name,p in PARTS.items():
  matches=[o for o in d.rootComponent.allOccurrences if o.component.partNumber==name or o.attributes.itemByName('Tinfox','SourceInstance')and o.attributes.itemByName('Tinfox','SourceInstance').value==name];assert len(matches)==1,(name,len(matches));occ=matches[0];c=occ.component;boxes=[]
  for body in c.bRepBodies:
   bb=body.createForAssemblyContext(occ).boundingBox;boxes.append([v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]])
  assert len(boxes)==p['geometry_comparison']['valid_solid_count'],(name,len(boxes));bounds=[min(box[i]for box in boxes)for i in range(3)]+[max(box[i]for box in boxes)for i in range(3,6)];error=max(abs(a-b)for a,b in zip(bounds,p['bounds_mm']));assert error<.05,(name,error,bounds,p['bounds_mm']);rows.append({'name':name,'native_path':occ.fullPathName,'body_count':len(boxes),'bounds_mm':bounds,'bounds_error_mm':error,'matrix_cm':list(occ.transform2.asArray()),'reference_role':'nonmanufacturing_display_reference'if name in ['body_serial','body_wordmark']else p['reference_role']})
 print(json.dumps({'passed':True,'chassis_saved_version':doc.dataFile.versionNumber,'working_modified':doc.isModified,'source_model_sha256':TARGET,'reference_items':len(rows),'reference_solids':sum(r['body_count']for r in rows),'parts':rows,'elapsed_seconds':time.monotonic()-tick,'scope':'Existing body reference instances bound to current exact source placements; no new reference import or custom geometry mutation.'}))
'''.replace('PARTS',repr(parts)).replace('TARGET',repr(manifest['source_model_sha256']))
r=rpc(s,'current-body-reference-binding',timeout=120,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-body-reference-binding.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k!='parts'})
