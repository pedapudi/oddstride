"""Constrain roof loft interpolation with exact four-station cubic guides."""
import json,hashlib,shutil
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1];weights=json.loads((ROOT/'snapshots/current-targets/roof-loft-interpolation.json').read_text())['station_to_bezier_coefficients'];archive=ROOT/'exports/retired';archive.mkdir(exist_ok=True);old=ROOT/'exports/current-body-cover-native.step'
if not (archive/'current-body-cover-unconstrained-loft.step').exists():shutil.copyfile(old,archive/'current-body-cover-unconstrained-loft.step')
s=(ROOT/'source/intent_geometry.py').read_text()+'''
def run(_context: str):
 import json,os,tempfile,time
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:R7U8KNNBSA6o3YwVNF2ZQQ';d=fusion.Design.cast(app.activeProduct);c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_current_body_center_0');g=IntentGeometry(d,c);outer=next(f for f in c.features.loftFeatures if f.name=='Four-station curved roof');inner=next(f for f in c.features.loftFeatures if f.name=='Four-station inner roof');assert outer.centerLineOrRails.count==0 and inner.centerLineOrRails.count==0;tick=time.monotonic();outer.timelineObject.rollTo(True);rails={};guide_rows=[]
 sections=[('cover_roof_z-2.7 mm','2*cover_half_length-1.3 mm','2*cover_half_width-21.4 mm','19 mm'),('cover_roof_z+.5 mm','2*cover_half_length-4.8 mm','2*cover_half_width-27.4 mm','23 mm'),('cover_roof_z+4.5 mm','2*cover_half_length-20.8 mm','2*cover_half_width-48.4 mm','32 mm'),('cover_roof_z+6 mm','2*cover_half_length-38.8 mm','2*cover_half_width-77.4 mm','36 mm')]
 for is_inner,label in [(False,'Outer'),(True,'Inner')]:
  rails[label]=[]
  for kind in ['side','end']:
   for sx,sy in [(1,1),(-1,1),(-1,-1),(1,-1)]:
    stations=[]
    for z,w,depth,radius in sections:
     x='('+w+')/2'+('-('+radius+')' if kind=='end' else '')+('-3 mm' if is_inner and kind=='side' else '');y='('+depth+')/2'+('-('+radius+')' if kind=='side' else '')+('-3 mm' if is_inner and kind=='end' else '');stations.append([str(sx)+'*('+x+')',str(sy)+'*('+y+')','('+z+')'+('-3 mm' if is_inner else '')])
    coords=[[' + '.join('('+str(value)+')*('+stations[j][axis]+')' for j,value in enumerate(row) if abs(value)>1e-14) for axis in range(3)] for row in WEIGHTS];curve=g.control_spline_3d(coords,label+' roof '+kind+' rail '+str(sx)+' '+str(sy),degree=3);error=max(point.geometry.distanceTo(core.Point3D.create(*[g.mm(expr)/10 for expr in row]))*10 for point,row in zip(curve.controlPoints,coords));assert error<1e-6,error;rails[label].append(curve);guide_rows.append({'name':curve.parentSketch.name,'degree':3,'control_points':4,'control_coordinate_error_mm':error})
  
 creation_seconds=time.monotonic()-tick
 for feature,label in [(outer,'Outer'),(inner,'Inner')]:
  feature.timelineObject.rollTo(True)
  for curve in rails[label]:assert feature.centerLineOrRails.addRail(curve)
 d.timeline.moveToEnd();assert d.computeAll();assert c.bRepBodies.count==1;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];body=c.bRepBodies.item(0);path=os.path.join(tempfile.gettempdir(),'tinfox-native','current-body-cover-native.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));print(json.dumps({'saved':False,'native_guides':guide_rows,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'guide_creation_seconds':creation_seconds,'elapsed_seconds':time.monotonic()-tick,'path':path,'gate':'Roof guide candidate awaiting the original full-surface and section thresholds.'}))
'''.replace('WEIGHTS',repr(weights))
r=rpc(s,'current-cover-roof-guides',timeout=900);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-cover-roof-guides.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k!='native_guides'});fetch(record['path'],Path(record['path']).name)
