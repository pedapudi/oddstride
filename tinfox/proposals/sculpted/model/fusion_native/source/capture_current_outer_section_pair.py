"""Capture the unresolved outer-thigh section directly in native Fusion.

The native MCP owner runs this read-only metrology at a safe boundary. No
document features, construction planes or physical geometry are created.
"""
import json
from pathlib import Path
from fetch_exports import fetch
from run_native import rpc

ROOT = Path(__file__).resolve().parents[1]
mapping = json.loads((ROOT/'manifests/whole-native-component-map-candidate.json').read_text())['parts']
parts = {key: mapping[key] for key in ['thigh_outer','thigh_outer_right']}
script = (ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,hashlib,math
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);components={}
 for c in d.allComponents:components.setdefault(c.partNumber,[]).append(c)
 result=[];tm=fusion.TemporaryBRepManager.get();inside=int(fusion.PointContainment.PointInsidePointContainment);outside=int(fusion.PointContainment.PointOutsidePointContainment);boundary=int(fusion.PointContainment.PointOnPointContainment);modified=doc.isModified
 for key,row in PARTS.items():
  choices=components[row['component_part_number']];assert len(choices)==1;c=choices[0];assert c.bRepBodies.count==1;body=c.bRepBodies.item(0);before=(c.features.count,c.sketches.count,c.constructionPlanes.count);offset=-75 if key.endswith('_right')else 75;plane=core.Plane.create(core.Point3D.create(0,offset/10,0),core.Vector3D.create(0,1,0));wire=tm.planeIntersection(body,plane);assert wire;curves=[];classification={};brackets=[];sheets=None
  for edge in wire.edges:
   evaluator=edge.evaluator;ok,a,b=evaluator.getParameterExtents();assert ok;ok,points=evaluator.getStrokes(a,b,.0001);assert ok;ok,length=evaluator.getLengthAtParameter(a,b);assert ok
   for point in points:
    state=int(body.pointContainment(point));classification[str(state)]=classification.get(str(state),0)+1
    if state!=boundary:
     trials=[]
     for axis in range(3):
      states=[]
      for direction in [-1,1]:
       xyz=point.asArray();xyz[axis]+=direction*.0049/10;states.append(int(body.pointContainment(core.Point3D.create(*xyz))))
      trials.append({'axis':'XYZ'[axis],'states':states})
     bracket_passed=any(inside in t['states']and outside in t['states']for t in trials);distance=None
     if not bracket_passed:
      if sheets is None:
       faces=list(body.faces);sheets=[tm.copy(face)for face in faces];bounds=[(face.boundingBox.minPoint.asArray(),face.boundingBox.maxPoint.asArray())for face in faces]
      v=point.asArray();lower=[math.sqrt(sum(max(lo-x,0,x-hi)**2 for x,lo,hi in zip(v,a,b)))for a,b in bounds];minimum=min(lower);candidates=[i for i,value in enumerate(lower)if value<=minimum+.01];distance=min(app.measureManager.measureMinimumDistance(point,sheets[i]).value for i in candidates)*10
     brackets.append({'point_mm':[v*10 for v in point.asArray()],'reported_state':state,'trials':trials,'bracket_passed':bracket_passed,'native_trimmed_face_distance_mm':distance,'passed':bracket_passed or distance is not None and distance<.005})
   curves.append({'length_mm':length*10,'points_mm':[[v*10 for v in p.asArray()]for p in points]})
  assert before==(c.features.count,c.sketches.count,c.constructionPlanes.count);bb=body.boundingBox;result.append({'part':key,'component_part_number':c.partNumber,'reference_native_step_sha256':row['native_step_sha256'],'axis':'Y','offset_mm':offset,'curves':curves,'native_point_containment_counts':classification,'nonboundary_brackets':brackets,'native_boundary_check_passed':all(p['passed']for p in brackets),'native_fingerprint':{'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'bounds_mm':[v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]]}})
 assert doc.isModified==modified;record={'document':doc.name,'saved_version':doc.dataFile.versionNumber,'working_modified':modified,'parts':result,'checker':'Native TemporaryBRepManager.planeIntersection and actual native point containment. Ambiguous tangent samples retain their solid brackets and may use direct native trimmed-face-sheet distance with the established0.005mm limit. No source geometry mutation.','stroke_tolerance_mm':.001,'boundary_bracket_mm':.0049,'native_trimmed_face_distance_limit_mm':.005,'scope':'Only the current Y=+75mm outer-thigh plane and mirrored Y=-75mm counterpart. Export hash fields identify the comparison inputs; actual current native fingerprints and saved-state binding remain separate.','enum':{'inside':inside,'outside':outside,'boundary':boundary}};path=os.path.join(tempfile.gettempdir(),'tinfox-native','current-outer-native-section-pair.json');raw=json.dumps(record).encode();open(path,'wb').write(raw);print(json.dumps({'path':path,'sha256':hashlib.sha256(raw).hexdigest(),'parts':len(result),'passed':all(r['native_boundary_check_passed']for r in result)}))
'''.replace('PARTS',repr(parts))
compile(script, 'current_outer_section_pair_native.py', 'exec')

if __name__ == '__main__':
    response = rpc(script, 'current-outer-native-section-pair', timeout=300, read_only=True)
    assert response[0]['success'], response
    result = json.loads(response[0]['message'])
    fetch(result['path'],'current-outer-native-section-pair.json')
    import hashlib
    assert hashlib.sha256((ROOT/'exports/current-outer-native-section-pair.json').read_bytes()).hexdigest() == result['sha256']
    print(json.dumps(result))
