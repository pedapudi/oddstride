"""Remove duplicate lid motion exposed by the full body placement edit test."""
import json
from pathlib import Path
from run_native import rpc
from body_reference_plan import plan
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'\n'+(ROOT/'source/body_reference_coordinates.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;c=next(c for c in d.allComponents if c.partNumber=='lidar_lid');b=c.bRepBodies.item(0);before=list(b.boundingBox.minPoint.asArray())+list(b.boundingBox.maxPoint.asArray());rows=bind_lidar_reference_coordinates(d);joint=next(j for j in root.joints if j.name=='Body datum lidar')
 for parameter,key in [(joint.offsetX,'x'),(joint.offsetY,'y'),(joint.offset,'z')]:parameter.expression=RULE[key]
 joint.attributes.add('Tinfox','PlacementRule',json.dumps(RULE));assert d.computeAll();b=c.bRepBodies.item(0);after=list(b.boundingBox.minPoint.asArray())+list(b.boundingBox.maxPoint.asArray());assert max(abs(a-b) for a,b in zip(before,after))<1e-8;assert joint.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState;print(json.dumps({'passed':True,'saved':False,'bindings':rows,'frame_rule':RULE,'baseline_bounds_unchanged':True,'scope':'The placement frame now owns live family motion for the native lidar cover and its vendor references. Its previous internal Move feature retains only the frozen source-coordinate offset.'}))
'''.replace('RULE',repr(plan()['groups']['lidar']))
r=rpc(s,'lidar-reference-driver-repair',timeout=120);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/lidar-reference-driver-repair.json').write_text(json.dumps(record,indent=2));print(record)
