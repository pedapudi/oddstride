"""Constrain cavity flank flatness and the shallow upper corner transition."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'snapshots/latest-leg/rounded-shin-guide-interpolation.json').read_text())['inner']
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py','native_nonuniform_spline.py'])+'''
def run(_context: str):
 import json,time,tempfile,os
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_round_shin_master');g=IntentGeometry(d,c);f=next(f for f in c.features.loftFeatures if f.name=='Five-section rounded shin cavity');assert f.centerLineOrRails.count==12;f.timelineObject.rollTo(True);tick=time.monotonic();guides=[]
 for kind,sx,sy in [('flank',-1,0),('flank',1,0),('corner',-1,-1),('corner',-1,1),('corner',1,-1),('corner',1,1)]:
  stations=[]
  for i,t in enumerate([0,14/102,49/102,79/102,1]):
   z=f'rs_inner_start_z+({t:.16g})*(rs_inner_end_z-rs_inner_start_z)';cx=f'lc_shin_curve_amplitude*(-({z})/lc_shank_foot_center)*(1+({z})/lc_shank_foot_center)';w=f'rs_inner_width_{i}-2*rs_wall';r='rs_inner_top_radius'if i==0 else f'rs_inner_radius_{i}-rs_wall'
   x=f'({cx})+({sx})*(({w})/2)';y='rs_center_y'
   if kind=='corner':x=f'({cx})+({sx})*(({w})/2-({r})+(cos(67.5 deg))*({r}))';y=f'rs_center_y+({sy})*((lc_shin_width-2*rs_wall)/2-({r})+(sin(67.5 deg))*({r}))'
   stations.append([x,y,z])
  coords=[[' + '.join(f'({v:.17g})*({stations[k][axis]})'for k,v in enumerate(row)if abs(v)>1e-14)for axis in range(3)]for row in WEIGHTS];guides.append(g.control_spline_3d(coords,f'Cavity {kind} guide {sx} {sy}',degree=3,internal_knots=KNOTS))
 f.timelineObject.rollTo(True)
 for guide in guides:assert f.centerLineOrRails.addRail(guide)
 d.timeline.moveToEnd();assert d.computeAll();parts={x.partNumber:x for x in d.allComponents if x.partNumber.startswith('CANDIDATE_round_shin_')};assert len(parts)==5;paths=[];rows=[]
 for key,comp in parts.items():
  assert comp.bRepBodies.count==1;assert all(ft.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for ft in comp.features);o=next(o for o in root.occurrences if o.component==comp);light=o.isLightBulbOn;o.isLightBulbOn=True;comp.bRepBodies.item(0).isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native',key.replace('CANDIDATE_round_','rounded-native-')+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,comp));o.isLightBulbOn=light;assert os.path.getsize(path)>5000;paths.append(path);rows.append({'part':key,'features':comp.features.count,'sketches':comp.sketches.count,'faces':comp.bRepBodies.item(0).faces.count})
 print(json.dumps({'saved':False,'paths':paths,'parts':rows,'new_native_guides':6,'control_points_per_guide':5,'cavity_rails':f.centerLineOrRails.count,'elapsed_seconds':time.monotonic()-tick,'scope':'Cavity contour correction; original shape and section thresholds remain unchanged.'}))
'''.replace('WEIGHTS',repr(data['station_to_control_pole_coefficients'])).replace('KNOTS',repr(data['internal_normalized_knots']))
r=rpc(s,'shin-cavity-contour-guides',timeout=900);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/shin-cavity-contour-guides.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
for path in record['paths']:fetch(path,Path(path).name)
