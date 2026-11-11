"""Capture the complete native right shin mesh without an intermediate STEP import."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,gzip,os,tempfile,time

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc.dataFile.versionNumber==13 and not doc.isModified;d=fusion.Design.cast(doc.products.itemByProductType('DesignProductType'));matches=[c for c in d.allComponents if c.partNumber=='shin_outer_right' and c.bRepBodies.count];assert len(matches)==1;body=matches[0].bRepBodies.item(0);tick=time.monotonic();calc=body.meshManager.createMeshCalculator();calc.surfaceTolerance=.002;calc.maxNormalDeviation=.04;mesh=calc.calculate();vertices=[[p.x*10,p.y*10,p.z*10] for p in mesh.nodeCoordinates];indices=list(mesh.nodeIndices);assert len(indices)>0 and len(indices)%3==0;faces=[indices[i:i+3] for i in range(0,len(indices),3)];record={'part':'shin_outer_right','source':'Native Fusion BRep meshManager','source_file_id':doc.dataFile.id,'version':doc.dataFile.versionNumber,'vertices':vertices,'faces':faces,'surface_tolerance_mm':.02,'max_normal_deviation_rad':.04,'features':matches[0].features.count,'native_faces':body.faces.count,'elapsed_seconds':time.monotonic()-tick};path=os.path.join(tempfile.gettempdir(),'tinfox-native','native-shin-outer-right-mesh.json.gz');open(path,'wb').write(gzip.compress(json.dumps(record).encode()));print(json.dumps({'path':path,'vertices':len(vertices),'triangles':len(faces),'seconds':record['elapsed_seconds'],'modified':doc.isModified}))
'''
r=rpc(s,'native-right-shin-direct-mesh',timeout=120,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/native-right-shin-direct-mesh.json').write_text(json.dumps(record,indent=2));print(record);fetch(record['path'],Path(record['path']).name)
