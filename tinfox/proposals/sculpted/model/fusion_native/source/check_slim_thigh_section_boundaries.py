"""Bracket native section stroke points within the 0.005 mm boundary tolerance."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,hashlib

def run(_context: str):
 app=core.Application.get();d=fusion.Design.cast(app.activeProduct);path=os.path.join(tempfile.gettempdir(),'tinfox-native','slim-thigh-direct-native-sections.json');raw=open(path,'rb').read();data=json.loads(raw);inside=int(fusion.PointContainment.PointInsidePointContainment);outside=int(fusion.PointContainment.PointOutsidePointContainment);on=int(fusion.PointContainment.PointOnPointContainment);rows=[]
 for record in data['sections']:
  body=next(o.component.bRepBodies.item(0) for o in d.rootComponent.occurrences if o.component.partNumber=='CANDIDATE_sl_'+record['side']);failed=[];on_count=0;bracketed=0
  for curve in record['curves']:
   for xyz in curve['points_mm']:
    p=core.Point3D.create(*[v/10 for v in xyz]);state=int(body.pointContainment(p))
    if state==on:on_count+=1;continue
    opposite=outside if state==inside else inside;found=False
    for axis in range(3):
     for sign in [-1,1]:
      q=[v/10 for v in xyz];q[axis]+=sign*.0049/10;other=int(body.pointContainment(core.Point3D.create(*q)))
      if other in [on,opposite]:found=True;break
     if found:break
    if found:bracketed+=1
    else:failed.append({'point_mm':xyz,'containment':state})
  rows.append({'side':record['side'],'axis':record['axis'],'offset_mm':record['offset_mm'],'exact_boundary_points':on_count,'boundary_bracketed_points':bracketed,'failed':failed,'passed':not failed})
 print(json.dumps({'native_section_sha256':hashlib.sha256(raw).hexdigest(),'boundary_bracket_radius_mm':.0049,'checks':rows,'passed':all(r['passed'] for r in rows),'method':'Exact native boundary classification or an inside/outside transition within a 0.0049 mm axial segment. Interior containment alone never counts as boundary proximity.'}))
'''
r=rpc(s,'slim-thigh-native-section-boundaries',timeout=300,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/slim-thigh-native-section-boundaries.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'sections':len(record['checks']),'failed':sum(len(row['failed']) for row in record['checks'])})
