"""Measure temporary section strokes against live trimmed faces, including tangent probes."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,hashlib,math

def run(_context:str):
 app=core.Application.get();d=fusion.Design.cast(app.activeProduct);path=os.path.join(tempfile.gettempdir(),'tinfox-native','slim-thigh-temporary-native-sections.json');raw=open(path,'rb').read();data=json.loads(raw);temporary=fusion.TemporaryBRepManager.get();cache={};rows=[]
 for record in data['sections']:
  key=record['side']
  if key not in cache:
   body=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_sl_'+key).bRepBodies.item(0);faces=list(body.faces);cache[key]=(body,[temporary.copy(f)for f in faces],[(f.boundingBox.minPoint.asArray(),f.boundingBox.maxPoint.asArray())for f in faces])
  body,sheets,bounds=cache[key];errors=[];failed=[];exact=0
  for curve in record['curves']:
   for xyz in curve['points_mm']:
    v=[x/10 for x in xyz];point=core.Point3D.create(*v)
    if body.pointContainment(point)==fusion.PointContainment.PointOnPointContainment:exact+=1;continue
    lower=[math.sqrt(sum(max(lo-x,0,x-hi)**2 for x,lo,hi in zip(v,a,b)))for a,b in bounds];minimum=min(lower);candidates=[i for i,b in enumerate(lower)if b<=minimum+.01];error=min(app.measureManager.measureMinimumDistance(point,sheets[i]).value for i in candidates)*10;errors.append(error)
    if error>.005:failed.append({'point_mm':xyz,'distance_mm':error})
  rows.append({'side':key,'axis':record['axis'],'offset_mm':record['offset_mm'],'exact_boundary_points':exact,'measured_nonboundary_points':len(errors),'maximum_boundary_error_mm':max(errors,default=0),'failed':failed,'passed':not failed})
 probes=[]
 for side,sign in [('thigh_inner',1),('thigh_inner_right',-1)]:
  body=cache[side][0];x=-9.77648641175923;y=sign*53.001;lo=-111.2;hi=-110.8
  def inside(z):return body.pointContainment(core.Point3D.create(x/10,y/10,z/10))==fusion.PointContainment.PointInsidePointContainment
  lower=inside(lo);assert lower!=inside(hi)
  for _ in range(36):
   mid=(lo+hi)/2
   if inside(mid)==lower:lo=mid
   else:hi=mid
  probes.append({'part':side,'x_mm':x,'y_mm':y,'z_transition_mm':(lo+hi)/2,'bracket_width_mm':hi-lo})
 print(json.dumps({'native_section_sha256':hashlib.sha256(raw).hexdigest(),'checks':rows,'passed':all(r['passed']for r in rows),'tangent_witnesses':probes,'method':'Exact live native boundary classification or distance to trimmed face sheets. Tangent witness uses a bracketed live solid transition.'}))
'''
r=rpc(s,'slim-thigh-temporary-section-boundaries',timeout=300,read_only=True);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/slim-thigh-temporary-section-boundaries.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'failed':sum(len(r['failed'])for r in record['checks']),'max_error_mm':max(r['maximum_boundary_error_mm']for r in record['checks']),'tangent_witnesses':record['tangent_witnesses']})
