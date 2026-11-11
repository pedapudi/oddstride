"""Measure disputed native section points against trimmed native faces."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,math

def run(_context: str):
 app=core.Application.get();d=fusion.Design.cast(app.activeProduct);body=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_current_front_face_master').bRepBodies.item(0);path=os.path.join(tempfile.gettempdir(),'tinfox-native','current-face-native-sections.json');raw=json.load(open(path));faces=list(body.faces);temporary=fusion.TemporaryBRepManager.get();sheets=[temporary.copy(face) for face in faces];rows=[]
 for record in raw['sections']:
  for xyz in record['boundary_failed']:
   point=core.Point3D.create(*[v/10 for v in xyz]);candidates=[]
   for face in faces:
    box=face.boundingBox;coords=point.asArray();lower=box.minPoint.asArray();upper=box.maxPoint.asArray();bound=math.sqrt(sum(max(lo-x,0,x-hi)**2 for x,lo,hi in zip(coords,lower,upper)))
    if bound<.005:candidates.append(face)
   assert candidates;measures=[(app.measureManager.measureMinimumDistance(point,sheets[faces.index(f)]),f) for f in candidates];result,face=min(measures,key=lambda pair:pair[0].value);rows.append({'point_mm':xyz,'distance_to_native_trimmed_face_mm':result.value*10,'closest_point_mm':[v*10 for v in result.positionTwo.asArray()],'face_index':faces.index(face),'candidate_faces':len(candidates)})
 print(json.dumps({'points':rows,'maximum_distance_mm':max(r['distance_to_native_trimmed_face_mm'] for r in rows),'scope':'Distance to trimmed native faces, never distance to a containing solid.'}))
'''
r=rpc(s,'current-face-section-trimmed-distances',timeout=120,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-face-section-trimmed-distances.json').write_text(json.dumps(record,indent=2));print(record)
