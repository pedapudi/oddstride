"""Save compact native Head work without promoting unresolved migration gates."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
script='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent
 assert len(app.data.personalUseLimits.editableFiles)==4
 lib=app.materialLibraries.itemById('BA5EE55E-9982-449B-9D66-9F036540E140');template=lib.appearances.itemByName('Plastic - Matte (White)');appearances={}
 for role,rgb in [('ivory',(231,223,208)),('glass',(25,60,59))]:
  name='Tinfox '+role;appearance=d.appearances.itemByName(name) or d.appearances.addByCopy(template,name)
  for propid in ['opaque_albedo','surface_albedo']:
   prop=core.ColorProperty.cast(appearance.appearanceProperties.itemById(propid))
   if prop:prop.value=core.Color.create(*rgb,255)
  appearances[role]=appearance
 rows=[]
 for occ in root.occurrences:
  c=occ.component;assert c.bRepBodies.count==1
  assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features)
  c.appearance=appearances['glass' if c.partNumber=='sensor_bezel' else 'ivory'];occ.isLightBulbOn=True;c.bRepBodies.item(0).isLightBulbOn=True
  for sketch in c.sketches:sketch.isLightBulbOn=False
  for plane in c.constructionPlanes:plane.isLightBulbOn=False
  if c.partNumber.startswith('CANDIDATE_'):c.attributes.add('Tinfox','Qualification','Surface and family edit tests pass; section/export validation remains pending. Not manufacturing released.')
  counts={'fitted_splines':0,'control_splines':0,'control_points':0,'sketch_entities':0}
  for s in c.sketches:
   counts['fitted_splines']+=s.sketchCurves.sketchFittedSplines.count;counts['control_splines']+=s.sketchCurves.sketchControlPointSplines.count;counts['sketch_entities']+=s.sketchCurves.count
   for curve in s.sketchCurves.sketchControlPointSplines:counts['control_points']+=len(curve.controlPoints)
  rows.append({'part':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'faces':c.bRepBodies.item(0).faces.count,'edges':c.bRepBodies.item(0).edges.count,**counts,'feature_names':[(f.name,f.objectType) for f in c.features]})
 root.attributes.add('Tinfox','SourceOfTruth','False: compact V0 native Head checkpoint; whole robot remains generated CAD authority.')
 folder=os.path.join(tempfile.gettempdir(),'tinfox-native');f3d=os.path.join(folder,'Tinfox-Head-native-checkpoint.f3d');assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(f3d))
 camera=app.activeViewport.camera;camera.eye=core.Point3D.create(48,-35,24);camera.target=core.Point3D.create(19,0,1);camera.upVector=core.Vector3D.create(0,0,1);camera.isFitView=True;camera.isSmoothTransition=False;app.activeViewport.camera=camera;app.activeViewport.refresh()
 png=os.path.join(folder,'Tinfox-Head-native-checkpoint.png');assert app.activeViewport.saveAsImageFile(png,1800,1100)
 before=doc.dataFile.versionNumber;assert doc.save('Checkpoint compact native Head with five verified family edits and restored geometry. Source overlap and STEP section anomaly remain explicitly unqualified.')
 print(json.dumps({'saved_request_accepted':True,'previous_version':before,'version_at_return':doc.dataFile.versionNumber,'editable_count':len(app.data.personalUseLimits.editableFiles),'parts':rows,'paths':[f3d,png],'source_of_truth_changed':False,'remaining':'Nose section validation, assembly migration, source fascia/bezel interference; no manufacturing release.'}))
'''
r=rpc(script,'head-native-checkpoint',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/head-native-checkpoint.json').write_text(json.dumps(record,indent=2))
for path in record['paths']:fetch(path,Path(path).name)
print(json.dumps({k:v for k,v in record.items() if k!='parts'}))
