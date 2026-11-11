"""Align the loft's eight functional tangent seams with the frozen V0 bridge."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
script=(ROOT/'source/intent_geometry.py').read_text()+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);occ=next(o for o in d.rootComponent.occurrences if o.component.partNumber=='CANDIDATE_body_nose_surround');c=occ.component;g=IntentGeometry(d,c);feature=next(f for f in c.features if f.name=='Continuous mounting bridge');assert feature.centerLineOrRails.count==4
 feature.timelineObject.rollTo(True)
 while feature.centerLineOrRails.count:assert feature.centerLineOrRails.item(0).deleteMe()
 names=['Roof','Floor','Right flank','Left flank']
 for sketch in list(c.sketches):
  if sketch.name in [name+' shape guide' for name in names]:assert sketch.deleteMe()
 for plane in list(c.constructionPlanes):
  if plane.name in [name+' guide plane' for name in names]:assert plane.deleteMe()
 rails=[]
 for side,label in [(1,'Right'),(-1,'Left')]:
  for title,shrink,zrole,zoffset in [('roof tangent',2,'roof',0),('upper side tangent',0,'roof',-2),('lower side tangent',0,'floor',2),('floor tangent',2,'floor',0)]:
   coordinates=[]
   for i in range(6):
    suffix=str(i+1);y='nose_bridge_guide_half_width_'+suffix+(' - 2 mm' if shrink else '');y=y if side>0 else '-('+y+')';z='nose_bridge_guide_'+zrole+'_'+suffix+(' + '+str(zoffset)+' mm' if zoffset else '');coordinates.append(['nose_bridge_guide_x_'+suffix,y,z])
   rails.append(g.control_spline_3d(coordinates,label+' '+title+' guide'))
 feature.timelineObject.rollTo(True);feature.isTangentEdgesMerged=False
 for rail in rails:assert feature.centerLineOrRails.addRail(rail)
 d.timeline.moveToEnd();assert d.computeAll();issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues;assert c.bRepBodies.count==1
 body=c.bRepBodies.item(0);occ.isLightBulbOn=True;body.isLightBulbOn=True;folder=os.path.join(tempfile.gettempdir(),'tinfox-native');step=os.path.join(folder,'body_nose_surround-tangent.step');stl=os.path.join(folder,'body_nose_surround-tangent.stl');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(step,c));opt=d.exportManager.createSTLExportOptions(c,stl);opt.unitType=fusion.DistanceUnits.MillimeterDistanceUnits;opt.meshRefinement=fusion.MeshRefinementSettings.MeshRefinementHigh;assert d.exportManager.execute(opt);occ.isLightBulbOn=False
 print(json.dumps({'features':c.features.count,'sketches':c.sketches.count,'rails':feature.centerLineOrRails.count,'guide_control_points':48,'faces':body.faces.count,'edges':body.edges.count,'volume_mm3':body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000,'paths':[step,stl],'saved':False}))
'''
r=rpc(script,'nose-bridge-tangent-guides',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/nose-bridge-tangent-guides.json').write_text(json.dumps(record,indent=2))
for path in record['paths']:fetch(path,Path(path).name)
print(json.dumps(record,indent=2))
