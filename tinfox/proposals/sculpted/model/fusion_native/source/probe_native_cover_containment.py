"""Compare direct Fusion solid classification with the frozen exact source."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];data=json.loads((ROOT/'snapshots/current-targets/cover-containment-probe.json').read_text())
s='''import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:R7U8KNNBSA6o3YwVNF2ZQQ';d=fusion.Design.cast(app.activeProduct);c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_current_body_center_0');b=c.bRepBodies.item(0);tick=time.monotonic();mismatches=[];inside=0;on=0;points=POINTS
 for row in points:
  state=int(b.pointContainment(core.Point3D.create(*[v*.1 for v in row['point_mm']])));inside+=state==0;on+=state==1
  if (state==0)!=row['source_inside']:mismatches.append(row|{'native_state':state})
 print(json.dumps({'samples':len(points),'native_inside':inside,'native_on':on,'source_inside':SOURCE_INSIDE,'mismatches':mismatches,'elapsed_seconds':time.monotonic()-tick,'is_solid':b.isSolid,'scope':'Direct native BRep volume classification; standard finite random-point validation, not a mathematical proof.'}))
'''
results=[]
for offset in range(0,len(data['points']),4000):
 points=data['points'][offset:offset+4000];script=s.replace('POINTS',repr(points)).replace('SOURCE_INSIDE',repr(sum(p['source_inside'] for p in points)));r=rpc(script,'current-cover-native-containment-'+str(offset//4000),timeout=180,read_only=True);assert r[0]['success'],r;results.append(json.loads(r[0]['message']))
record={'source_sha256':data['source_sha256'],'samples':sum(r['samples'] for r in results),'source_inside':data['inside_count'],'native_inside':sum(r['native_inside'] for r in results),'mismatches':[p for r in results for p in r['mismatches']],'elapsed_seconds':sum(r['elapsed_seconds'] for r in results),'is_solid':all(r['is_solid'] for r in results),'scope':results[0]['scope']}
(ROOT/'audits/current-cover-native-containment.json').write_text(json.dumps(record,indent=2));print(record)
