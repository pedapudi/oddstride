"""Anchor shared family references to an explicit native hip datum plane."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');assert doc==app.activeDocument and not doc.isModified;d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;assert root.constructionPlanes.itemByName('Front hip family datum') is None;assert abs(d.userParameters.itemByName('robot_hip_x').value-18.5)<1e-8;capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);inp=root.constructionPlanes.createInput();assert inp.setByOffset(root.yZConstructionPlane,core.ValueInput.createByString('robot_hip_x'));plane=root.constructionPlanes.add(inp);plane.name='Front hip family datum';plane.isLightBulbOn=False;assert d.computeAll();assert doc.save('Add a native front-hip construction datum for shared family references; all part geometry remains at the frozen baseline.');print(json.dumps({'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'plane':plane.name,'plane_offset_mm':plane.geometry.origin.x*10,'capacity':capacity}))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'shared-family-plane-publication',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/shared-family-plane-publication.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k!='capacity'})
