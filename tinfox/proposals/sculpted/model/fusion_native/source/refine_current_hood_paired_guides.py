"""Constrain the low hood with exact native eight-pole section guide curves."""
import sys,json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1];weights={k:v['station_to_bezier_coefficients'] for k,v in json.loads((ROOT/'snapshots/current-targets/hood-loft-interpolation.json').read_text()).items()}
s=(ROOT/'source/intent_geometry.py').read_text()+'''
def run(_context: str):
 import json,os,tempfile,time
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_current_front_fascia');g=IntentGeometry(d,c);features={label:next(f for f in c.features.loftFeatures if f.name==name) for label,name in [('Outer','Eight-section sensor hood envelope'),('Inner','Eight-section hollow interior')]};assert all(f.centerLineOrRails.count==0 for f in features.values());features['Outer'].timelineObject.rollTo(True);tick=time.monotonic();allrails={};rows=[]
 for skin in ['Outer','Inner']:
  rails=[];allrails[skin]=rails
  for edge in ['horizontal','vertical','corner']:
   for sign in [-1,1]:
    for top in [False,True]:
     stations=[]
     for i in range(1,9):
      prefix='hood_station_'+str(i)+'_';x=prefix+'x';w=prefix+'width';lo=prefix+'lower_z';hi=prefix+'upper_z';radius='3.8 mm' if i==1 else '4 mm'
      if skin=='Inner':w='('+w+')-2*hood_wall';lo='('+lo+')-hood_lower_opening_overlap';hi='('+hi+')-hood_wall';radius='2 mm'
      if edge=='horizontal':y='('+w+')/2-('+radius+')';z=hi if top else lo
      elif edge=='vertical':y='('+w+')/2';z='('+hi+')-('+radius+')' if top else '('+lo+')+('+radius+')'
      else:y='('+w+')/2-('+radius+')+('+radius+')/sqrt(2)';z='('+hi+')-('+radius+')+('+radius+')/sqrt(2)' if top else '('+lo+')+('+radius+')-('+radius+')/sqrt(2)'
      stations.append([x,str(sign)+'*('+y+')',z])
     coords=[[' + '.join('('+str(value)+')*('+stations[j][axis]+')' for j,value in enumerate(row) if abs(value)>1e-14) for axis in range(3)] for row in WEIGHTS[skin]];name=skin+' hood '+('top' if top else 'bottom')+' '+edge+' rail '+str(sign);curve=g.control_spline_3d(coords,name,degree=7);error=max(point.geometry.distanceTo(core.Point3D.create(*[g.mm(expr)/10 for expr in row]))*10 for point,row in zip(curve.controlPoints,coords));assert error<1e-5,(name,error);rails.append(curve);rows.append({'name':name,'degree':int(curve.degree),'control_points':len(curve.controlPoints),'coordinate_error_mm':error})
 creation=time.monotonic()-tick
 for skin,feature in features.items():
  feature.timelineObject.rollTo(True)
  for curve in allrails[skin]:assert feature.centerLineOrRails.addRail(curve)
 d.timeline.moveToEnd();computed=d.computeAll();issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert computed and c.bRepBodies.count==1 and not issues,{'computed':computed,'bodies':c.bRepBodies.count,'issues':issues};body=c.bRepBodies.item(0);path=os.path.join(tempfile.gettempdir(),'tinfox-native','current-sensor-hood-native.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));print(json.dumps({'saved':False,'skins':['Outer','Inner'],'guides':rows,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'guide_creation_seconds':creation,'elapsed_seconds':time.monotonic()-tick,'path':path,'gate':'Native guided hood candidate awaiting original full geometry and assembly thresholds.'}))
'''.replace('WEIGHTS',repr(weights))
r=rpc(s,'current-hood-paired-guides',timeout=900);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-hood-paired-guides.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k!='guides'});fetch(record['path'],Path(record['path']).name)
