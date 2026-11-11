"""Edit shared frame width, thickness and clearance, then restore both parts."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,time

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');assert doc==app.activeDocument;d=fusion.Design.cast(app.activeProduct);parts={key:next(c for c in d.allComponents if c.partNumber=='CANDIDATE_'+key) for key in ['chassis_lower_brace','electronics_shelf']};tick=time.monotonic()
 def dimensions():
  out={}
  for key,c in parts.items():
   b=c.bRepBodies.item(0);box=b.boundingBox;cyl=[]
   for f in b.faces:
    surface=core.Cylinder.cast(f.geometry)
    if surface and abs(surface.axis.z)>.999999:cyl.append({'x':surface.origin.x*10,'y':surface.origin.y*10,'radius':surface.radius*10})
   out[key]={'bounds':[v*10 for v in [box.minPoint.x,box.minPoint.y,box.minPoint.z,box.maxPoint.x,box.maxPoint.y,box.maxPoint.z]],'volume_mm3':b.volume*1000,'cylinders':cyl,'unhealthy':[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]}
   assert not out[key]['unhealthy'],out[key]
  return out
 def near(a,b):assert abs(a-b)<1e-5,(a,b)
 def hole(record,x,y,r):assert any(abs(c['x']-x)<1e-5 and abs(c['y']-y)<1e-5 and abs(c['radius']-r)<1e-5 for c in record['cylinders']),(x,y,r,record['cylinders'])
 baseline=dimensions();rows=[]
 cases=[('frame_half_y','107 mm','Paired rail and deck width'),('frame_brace_thickness','4 mm','Brace thickness and supported deck height'),('robot_fastener_diametral_allowance','.6 mm','Shared M3 clearance with unchanged tapped holes')]
 for name,expression,title in cases:
  p=d.userParameters.itemByName(name);original=p.expression
  try:
   p.expression=expression;assert d.computeAll();edited=dimensions();brace=edited['chassis_lower_brace'];deck=edited['electronics_shelf'];half=d.userParameters.itemByName('frame_half_y').value*10;thick=d.userParameters.itemByName('frame_brace_thickness').value*10;clear=d.userParameters.itemByName('frame_m3_clearance').value*10
   near(brace['bounds'][1],-(half-1));near(brace['bounds'][4],half-1);near(deck['bounds'][1],-(half-9));near(deck['bounds'][4],half-9);near(brace['bounds'][5],2+thick/2);near(deck['bounds'][2],brace['bounds'][5]);near(deck['bounds'][5],brace['bounds'][5]+4)
   for sx in [-1,1]:
    for sy in [-1,1]:hole(brace,sx*63,sy*(half-5),clear/2);hole(brace,sx*52,sy*(half-14),1.25);hole(deck,sx*52,sy*(half-14),clear/2)
   rows.append({'parameter':name,'edited_expression':expression,'purpose':title,'edited':edited,'passed':True})
  finally:
   p.expression=original;assert d.computeAll()
  restored=dimensions();maximum=max(abs(a-b) for key in parts for a,b in zip(baseline[key]['bounds'],restored[key]['bounds']));assert maximum<1e-5;assert all(abs(restored[key]['volume_mm3']-baseline[key]['volume_mm3'])<1e-4 for key in parts);rows[-1]['restore_max_bounds_error_mm']=maximum
 paths=[]
 for key,c in parts.items():
  occurrence=next(o for o in d.rootComponent.occurrences if o.component==c);visible=occurrence.isLightBulbOn;occurrence.isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','frame-intent-'+key+'-restored.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));occurrence.isLightBulbOn=visible;assert os.path.getsize(path)>10000;paths.append(path)
 print(json.dumps({'passed':True,'baseline':baseline,'edits':rows,'paths':paths,'elapsed_seconds':time.monotonic()-tick,'scope':'Both candidate custom parts share mounting coordinates and clearance expressions. This does not yet propagate the dimensions into the existing rails, cassette or hardware occurrences.'}))
'''
r=rpc(s,'frame-deck-family-edit-restore',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/frame-deck-family-edit-restore.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'cases':len(record['edits']),'seconds':record['elapsed_seconds']},flush=True)
for p in record['paths']:fetch(p,Path(p).name)
