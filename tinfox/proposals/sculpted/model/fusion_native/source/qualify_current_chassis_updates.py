"""Exercise the new sensor interfaces and verify body reference placements."""
import json,gzip
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'manifests/current-exact-hardware-references.json').read_text());model=json.loads(gzip.decompress((ROOT/'snapshots/current-hardware'/ref['source_model_sha256']/'reference-geometry.json.gz').read_bytes()));names=[p['name'] for p in model['parts'] if not p.get('leg')]
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,time

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:R7U8KNNBSA6o3YwVNF2ZQQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;beam=next(c for c in d.allComponents if c.partNumber=='chassis_crossmember_121');lid=next(c for c in d.allComponents if c.partNumber=='lidar_lid');tick=time.monotonic();identity=core.Matrix3D.create().asArray();placements=[]
 def visit(o):
  if o.component.name in NAMES:
   error=max(abs(a-b) for a,b in zip(o.transform2.asArray(),identity));assert error<1e-8,(o.name,error);placements.append({'part':o.component.name,'matrix_error':error})
   if o.component.name=='electronics_clearance':o.isLightBulbOn=False;o.component.attributes.add('Tinfox','GeometryRole','Nonphysical electronics clearance envelope; exclude from mass and manufacturing exports')
  for child in o.childOccurrences:visit(child)
 for o in root.occurrences:
  if o.component.partNumber=='REFERENCE_Body_body':visit(o)
 assert len(placements)==82
 def state():
  b=lid.bRepBodies.item(0);return {'lid_bounds_mm':[v*10 for v in b.boundingBox.minPoint.asArray()+b.boundingBox.maxPoint.asArray()],'beam_volume_mm3':beam.bRepBodies.item(0).volume*1000,'beam_clearance_probe':int(beam.bRepBodies.item(0).pointContainment(core.Point3D.create(12.325,2.4,4.1)))}
 baseline=state();rows=[]
 for name,value in [('saddle_fastener_diametral_clearance','.6 mm'),('saddle_sensor_seat_z','85 mm')]:
  p=d.userParameters.itemByName(name);old=p.expression;p.expression=value;assert d.computeAll();edited=state()
  if name=='saddle_fastener_diametral_clearance':assert baseline['beam_clearance_probe']==0 and edited['beam_clearance_probe']==2,(baseline,edited)
  else:assert max(abs((b-a)-(5 if i in [2,5] else 0)) for i,(a,b) in enumerate(zip(baseline['lid_bounds_mm'],edited['lid_bounds_mm'])))<1e-5
  p.expression=old;assert d.computeAll();restored=state();assert abs(restored['beam_volume_mm3']-baseline['beam_volume_mm3'])<.001;assert max(abs(a-b) for a,b in zip(restored['lid_bounds_mm'],baseline['lid_bounds_mm']))<1e-5;rows.append({'parameter':name,'value':value,'edited':edited,'restored':True})
 for c in d.allComponents:assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),c.name
 paths=[]
 for c,label in [(beam,'current-front-crossmember-native'),(lid,'current-lidar-lid-native')]:
  path=os.path.join(tempfile.gettempdir(),'tinfox-native',label+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));paths.append(path)
 print(json.dumps({'passed':True,'saved':False,'placements':placements,'parameter_tests':rows,'paths':paths,'elapsed_seconds':time.monotonic()-tick,'scope':'Sensor fastener diameter and lidar lid height edits/restores; body references at frozen origin. Whole chassis resizing, external-document parameter synchronization and reference mass are separate gates.'}))
'''.replace('NAMES',repr(names))
r=rpc(s,'current-chassis-update-qualification',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-chassis-update-qualification.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'references':len(record['placements']),'edits':len(record['parameter_tests']),'seconds':record['elapsed_seconds']})
for path in record['paths']:fetch(path,Path(path).name)
