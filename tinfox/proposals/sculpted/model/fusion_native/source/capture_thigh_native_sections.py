"""Measure actual native thigh cuts independently of STEP section reconstruction."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
# Offsets are the same nine planes used by the immutable source STEP audit.
planes=json.loads((ROOT/'snapshots/cohesive-limb/intent/thigh-section-planes.json').read_text())
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
 app=core.Application.get();d=fusion.Design.cast(app.activeProduct);results=[]
 for side,planes in PLANES.items():
  c=next(o.component for o in d.rootComponent.occurrences if o.component.partNumber=='CANDIDATE_cohesive_thigh_'+side);before=(c.features.count,c.sketches.count,c.constructionPlanes.count);body=c.bRepBodies.item(0)
  for sample in planes:
   axis=sample['axis'];offset=sample['offset_mm'];base={'X':c.yZConstructionPlane,'Y':c.xZConstructionPlane,'Z':c.xYConstructionPlane}[axis];inp=c.constructionPlanes.createInput();inp.setByOffset(base,core.ValueInput.createByReal(offset/10));plane=c.constructionPlanes.add(inp);sk=c.sketches.add(plane);sk.name='TEMP native section metrology';curves=sk.projectCutEdges(body);rows=[];classification={}
   for curve in curves:
    geo=curve.worldGeometry;e=geo.evaluator;ok,a,b=e.getParameterExtents();assert ok;ok,points=e.getStrokes(a,b,.0001);assert ok;ok,length=e.getLengthAtParameter(a,b);assert ok
    for p in points:
     state=int(body.pointContainment(p));classification[state]=classification.get(state,0)+1
    rows.append({'type':curve.objectType,'length_mm':length*10,'points_mm':[[p.x*10,p.y*10,p.z*10] for p in points]})
   assert sk.deleteMe();assert plane.deleteMe();assert (c.features.count,c.sketches.count,c.constructionPlanes.count)==before;results.append({'side':side,'axis':axis,'offset_mm':offset,'curves':rows,'native_point_containment_counts':classification})
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-thigh-direct-native-sections.json');open(path,'w').write(json.dumps({'sections':results,'stroke_tolerance_mm':.001,'temporary_metrology_removed':True,'enum':{'inside':int(fusion.PointContainment.PointInsidePointContainment),'outside':int(fusion.PointContainment.PointOutsidePointContainment),'boundary':int(fusion.PointContainment.PointOnPointContainment)}}));print(json.dumps({'path':path,'sections':len(results),'temporary_metrology_removed':True}))
'''.replace('PLANES',repr(planes))
r=rpc(s,'cohesive-thigh-direct-native-sections',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);fetch(record['path'],'cohesive-thigh-direct-native-sections.json');print(record)
