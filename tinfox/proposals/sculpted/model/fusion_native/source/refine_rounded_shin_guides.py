"""Add exact two-span guides to the existing five-section shin loft."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
weights=json.loads((ROOT/'snapshots/latest-leg/rounded-shin-guide-interpolation.json').read_text())['outer']['span_station_coefficients']
s=(ROOT/'source/intent_geometry.py').read_text()+'''
def run(_context: str):
 import json,time,tempfile,os
 app=core.Application.get();d=fusion.Design.cast(app.activeProduct);assert app.activeDocument.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_round_shin_master');g=IntentGeometry(d,c);f=c.features.loftFeatures.item(0);assert f.centerLineOrRails.count==0;f.timelineObject.rollTo(True);tick=time.monotonic();paths=[];records=[]
 for kind in ['side','end','corner']:
  for sx,sy in [(1,1),(-1,1),(-1,-1),(1,-1)]:
   stations=[]
   for i,t in enumerate([0,22/118,57/118,87/118,1]):
    z=f'rs_outer_start_z+({t:.16g})*(rs_outer_end_z-rs_outer_start_z)';cx=f'lc_shin_curve_amplitude*(-({z})/lc_shank_foot_center)*(1+({z})/lc_shank_foot_center)';w=f'rs_outer_width_{i}';r=f'rs_outer_radius_{i}';x=f'({w})/2';y='lc_shin_width/2'
    if kind=='end':x+=f'-({r})'
    if kind=='side':y+=f'-({r})'
    if kind=='corner':x+=f'-(1-1/sqrt(2))*({r})';y+=f'-(1-1/sqrt(2))*({r})'
    stations.append([f'({cx})+({sx})*({x})',f'rs_center_y+({sy})*({y})',z])
   curves=core.ObjectCollection.create()
   for j,matrix in enumerate(WEIGHTS):
    coords=[[' + '.join(f'({value:.17g})*({stations[k][axis]})'for k,value in enumerate(row)if abs(value)>1e-14)for axis in range(3)]for row in matrix];curve=g.control_spline_3d(coords,f'Shin {kind} guide {sx} {sy} span {j+1}',degree=3);curves.add(curve)
   path=c.features.createPath(curves,False);assert path;paths.append(path);records.append({'kind':kind,'x_sign':sx,'y_sign':sy,'cubic_spans':2})
 f.timelineObject.rollTo(True)
 for path in paths:assert f.centerLineOrRails.addRail(path)
 d.timeline.moveToEnd();assert d.computeAll();assert c.bRepBodies.count==1;issues=[(x.name,x.errorOrWarningMessage)for x in c.features if x.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues;body=c.bRepBodies.item(0);path=os.path.join(tempfile.gettempdir(),'tinfox-native','rounded-shin-outer-loft-guided.step');occ=next(o for o in d.rootComponent.occurrences if o.component==c);previous_visibility=occ.isLightBulbOn;occ.isLightBulbOn=True;body.isLightBulbOn=True;assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));occ.isLightBulbOn=previous_visibility;assert os.path.getsize(path)>10000;print(json.dumps({'saved':False,'path':path,'guides':records,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'elapsed_seconds':time.monotonic()-tick,'scope':'Exact source station interpolation; geometry comparison still required.'}))
'''.replace('WEIGHTS',repr(weights))
r=rpc(s,'rounded-shin-guides-native',timeout=900);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/rounded-shin-guides-native.json').write_text(json.dumps(record,indent=2));print(record,flush=True);fetch(record['path'],Path(record['path']).name)
