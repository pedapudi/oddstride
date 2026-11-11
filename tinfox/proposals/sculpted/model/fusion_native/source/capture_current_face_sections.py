"""Check compound-face sections directly in Fusion, avoiding STEP trim artifacts."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1];planes=[{'axis':s['axis'],'offset_mm':s['offset_mm']} for s in json.loads((ROOT/'audits/current-face-master-native-sections.json').read_text())['sections']]
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
 app=core.Application.get();d=fusion.Design.cast(app.activeProduct);c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_current_front_face_master');before=(c.features.count,c.sketches.count,c.constructionPlanes.count);body=c.bRepBodies.item(0);results=[]
 for sample in PLANES:
  axis=sample['axis'];offset=sample['offset_mm'];base={'X':c.yZConstructionPlane,'Y':c.xZConstructionPlane,'Z':c.xYConstructionPlane}[axis];inp=c.constructionPlanes.createInput();inp.setByOffset(base,core.ValueInput.createByReal(offset/10));plane=c.constructionPlanes.add(inp);sk=c.sketches.add(plane);sk.name='TEMP native face section metrology';curves=sk.projectCutEdges(body);rows=[];classification={};failed=[];bracketed=0
  for curve in curves:
   e=curve.worldGeometry.evaluator;ok,a,b=e.getParameterExtents();assert ok;ok,points=e.getStrokes(a,b,.0001);assert ok;ok,length=e.getLengthAtParameter(a,b);assert ok
   for p in points:
    state=int(body.pointContainment(p));classification[state]=classification.get(state,0)+1
    if state==1:continue
    found=False
    for dim in range(3):
     for sign in [-1,1]:
      q=list(p.asArray());q[dim]+=sign*.0049/10;other=int(body.pointContainment(core.Point3D.create(*q)))
      if other in [1,2 if state==0 else 0]:found=True;break
     if found:break
    if found:bracketed+=1
    else:failed.append([v*10 for v in p.asArray()])
   rows.append({'type':curve.objectType,'length_mm':length*10,'points_mm':[[v*10 for v in p.asArray()] for p in points]})
  assert sk.deleteMe();assert plane.deleteMe();assert (c.features.count,c.sketches.count,c.constructionPlanes.count)==before;results.append(sample|{'curves':rows,'classification':classification,'boundary_bracketed':bracketed,'boundary_failed':failed})
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','current-face-native-sections.json');open(path,'w').write(json.dumps({'sections':results,'stroke_tolerance_mm':.001,'boundary_bracket_mm':.0049,'temporary_metrology_removed':True}));print(json.dumps({'path':path,'sections':len(results),'boundary_failures':sum(len(r['boundary_failed']) for r in results),'temporary_metrology_removed':True}))
'''.replace('PLANES',repr(planes))
r=rpc(s,'current-face-direct-native-sections',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);print(record);fetch(record['path'],Path(record['path']).name)
