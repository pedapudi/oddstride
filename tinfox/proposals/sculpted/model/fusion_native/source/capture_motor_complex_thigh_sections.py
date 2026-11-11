"""Measure actual native thigh cuts independently of STEP section reconstruction."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
# Offsets are the same nine planes used by the immutable source STEP audit.
planes={}
for key in ['thigh_outer']:
 row=json.loads((ROOT/'audits'/('motor-complex-native-'+key+'-sections.json')).read_text());planes[key]=[{k:r[k]for k in ['axis','offset_mm']}for r in row['sections']]
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
 app=core.Application.get();d=fusion.Design.cast(app.activeProduct);results=[]
 for side,planes in PLANES.items():
  c=next(o.component for o in d.rootComponent.occurrences if o.component.partNumber=='CANDIDATE_mc_'+side);before=(c.features.count,c.sketches.count,c.constructionPlanes.count);body=c.bRepBodies.item(0)
  for sample in planes:
   axis=sample['axis'];offset=sample['offset_mm'];coordinate=[0.,0.,0.];normal=[0.,0.,0.];coordinate['XYZ'.index(axis)]=offset/10;normal['XYZ'.index(axis)]=1.;plane=core.Plane.create(core.Point3D.create(*coordinate),core.Vector3D.create(*normal));wire=fusion.TemporaryBRepManager.get().planeIntersection(body,plane);assert wire;curves=list(wire.edges);rows=[];classification={}
   for curve in curves:
    e=curve.evaluator;ok,a,b=e.getParameterExtents();assert ok;ok,points=e.getStrokes(a,b,.0001);assert ok;ok,length=e.getLengthAtParameter(a,b);assert ok
    for p in points:
     state=int(body.pointContainment(p));classification[state]=classification.get(state,0)+1
    rows.append({'type':curve.objectType,'length_mm':length*10,'points_mm':[[p.x*10,p.y*10,p.z*10] for p in points]})
   assert (c.features.count,c.sketches.count,c.constructionPlanes.count)==before;results.append({'side':side,'axis':axis,'offset_mm':offset,'curves':rows,'native_point_containment_counts':classification})
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','motor-complex-thigh-temporary-native-sections.json');open(path,'w').write(json.dumps({'document':d.parentDocument.name,'saved_version':d.parentDocument.dataFile.versionNumber,'sections':results,'stroke_tolerance_mm':.001,'temporary_metrology_removed':True,'checker':'TemporaryBRepManager.planeIntersection; no document features created','enum':{'inside':int(fusion.PointContainment.PointInsidePointContainment),'outside':int(fusion.PointContainment.PointOutsidePointContainment),'boundary':int(fusion.PointContainment.PointOnPointContainment)}}));print(json.dumps({'path':path,'sections':len(results),'temporary_metrology_removed':True,'checker':'TemporaryBRepManager.planeIntersection; no document features created'}))
'''.replace('PLANES',repr(planes))
r=rpc(s,'motor-complex-thigh-temporary-native-sections',timeout=300,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);fetch(record['path'],'motor-complex-thigh-temporary-native-sections.json');print(record)
