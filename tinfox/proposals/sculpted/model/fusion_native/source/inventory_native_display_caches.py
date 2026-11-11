"""Compare cached native meshes in authoring documents with their saved linked review."""
import gzip,json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];mapping=json.loads((ROOT/'manifests/whole-native-component-map-candidate.json').read_text())['parts'];model=json.loads(gzip.decompress((ROOT/'exports/whole-native-master-63/native-whole-display-candidate.json.gz').read_bytes()));wanted={p['native_definition_id']for p in model['parts']if p['native_definition_id']in {v['component_part_number']for v in mapping.values()}}
script=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json
def run(_context:str):
 app=core.Application.get();rows=[]
 for role in ['leg','chassis','head']:
  doc=authoring_document(app,role);assert doc.dataFile.isComplete and not doc.isModified;d=fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
  for c in d.allComponents:
   if c.partNumber not in WANTED:continue
   for i,body in enumerate(c.bRepBodies):
    display=body.meshManager.displayMeshes;cache=[]
    for k in range(display.count):
     mesh=display.item(k);cache.append({'index':k,'tolerance_mm':mesh.surfaceTolerance*10,'triangles':len(mesh.nodeIndices)//3})
    rows.append({'role':role,'saved_version':doc.dataFile.versionNumber,'part_number':c.partNumber,'body_index':i,'body_name':body.name,'meshes':cache})
 print(json.dumps({'passed':True,'rows':rows,'scope':'Existing native authoring caches only; no mesh calculation, document edits or geometry changes.'}))
'''.replace('WANTED',repr(wanted))
r=rpc(script,'native-display-cache-inventory',timeout=120,read_only=True);assert r[0]['success'],r;data=json.loads(r[0]['message']);(ROOT/'audits/native-display-cache-inventory.json').write_text(json.dumps(data,indent=2));print({'bodies':len(data['rows']),'within_005':sum(any(c['tolerance_mm']<=.05 for c in r['meshes'])for r in data['rows'])})
