"""Measure native display tessellation without changing CAD or manufacturing tolerances."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
script=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'head');assert doc.dataFile.versionNumber==22 and not doc.isModified;d=fusion.Design.cast(doc.products.itemByProductType('DesignProductType'));parts=[c for c in d.allComponents if c.partNumber=='front_fascia'];assert len(parts)==1;c=parts[0];assert c.bRepBodies.count==1;body=c.bRepBodies.item(0);calc=body.meshManager.createMeshCalculator();names=['surfaceTolerance','maxNormalDeviation','maxSideLength','maxAspectRatio'];defaults={n:getattr(calc,n)for n in names};calc.surfaceTolerance=.005;calc.maxNormalDeviation=.12;settings={n:getattr(calc,n)for n in names};tick=time.monotonic();mesh=calc.calculate();count=len(mesh.nodeIndices)//3;assert count>0;assert not doc.isModified;print(json.dumps({'passed':True,'part':'front_fascia','head_version':22,'default_settings':defaults,'display_settings':settings,'vertices':len(mesh.nodeCoordinates),'triangles':count,'elapsed_seconds':time.monotonic()-tick,'scope':'Native direct display tessellation only. Original exact CAD and manufacturing exports remain unchanged.'}))
'''
r=rpc(script,'native-display-mesh-pilot',timeout=180,read_only=True);assert r[0]['success'],r;d=json.loads(r[0]['message']);(ROOT/'audits/native-display-mesh-pilot.json').write_text(json.dumps(d,indent=2));print(d)
