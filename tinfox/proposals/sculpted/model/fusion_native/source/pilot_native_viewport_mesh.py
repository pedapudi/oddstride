"""Inspect existing viewport meshes and native quality presets without authoring mesh bodies."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
script=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'head');assert doc.dataFile.versionNumber==22 and not doc.isModified;d=fusion.Design.cast(doc.products.itemByProductType('DesignProductType'));c=[c for c in d.allComponents if c.partNumber=='front_fascia'][0];body=c.bRepBodies.item(0);rows=[];display=body.meshManager.displayMeshes
 def data(mesh):
  row={'vertices':len(mesh.nodeCoordinates),'triangles':len(mesh.nodeIndices)//3}
  try:row['surface_tolerance_cm']=mesh.surfaceTolerance
  except RuntimeError as error:row['surface_tolerance_getter_error']=str(error)
  return row
 for i in range(display.count):rows.append({'kind':'existing_display','index':i,**data(display.item(i))})
 best=data(display.bestMesh)if display.bestMesh else None
 for name,value in [('Low',fusion.TriangleMeshQualityOptions.LowQualityTriangleMesh),('Normal',fusion.TriangleMeshQualityOptions.NormalQualityTriangleMesh)]:
  calc=body.meshManager.createMeshCalculator();assert calc.setQuality(value);settings={n:getattr(calc,n)for n in ['surfaceTolerance','maxNormalDeviation','maxSideLength','maxAspectRatio']};tick=time.monotonic();mesh=calc.calculate();rows.append({'kind':'native_quality_preset','quality':name,'settings':settings,'elapsed_seconds':time.monotonic()-tick,**data(mesh)})
 assert not doc.isModified;print(json.dumps({'passed':True,'part':'front_fascia','saved_head_version':22,'best_display_mesh':best,'rows':rows,'new_documents':0,'new_mesh_bodies':0,'cad_changed':False}))
'''
r=rpc(script,'native-viewport-mesh-pilot',timeout=180,read_only=True);assert r[0]['success'],r;d=json.loads(r[0]['message']);(ROOT/'audits/native-viewport-mesh-pilot.json').write_text(json.dumps(d,indent=2));print(d)
