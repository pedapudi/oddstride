"""Derive the native nose's service-face clearance from the native fascia."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
assert json.loads((ROOT/'audits/front_fascia-intent-geometry.json').read_text())['geometric_gate_passed']
script=(ROOT/'source/intent_geometry.py').read_text()+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent
 occ=next(o for o in root.occurrences if o.component.partNumber=='CANDIDATE_body_nose_surround');c=occ.component;g=IntentGeometry(d,c);assert c.features.count==34 and c.bRepBodies.count==1
 fascia=next(o.component for o in root.occurrences if o.component.partNumber=='CANDIDATE_front_fascia');assert fascia.bRepBodies.count==1
 g.parameter('nose_fascia_fit_gap',.35,comment='Axial assembly clearance behind the removable native service face')
 body=c.bRepBodies.item(0)
 def copy_face(name):
  objects=core.ObjectCollection.create();objects.add(fascia.bRepBodies.item(0));feature=c.features.copyPasteBodies.add(objects);feature.name=name;assert feature.isParametric;assert feature.bodies.count==1;return feature.bodies.item(0)
 face=copy_face('Linked service face');body=g.combine(body,[face],fusion.FeatureOperations.CutFeatureOperation,'Match service-face mating surface')
 face=copy_face('Linked service clearance tool');objects=core.ObjectCollection.create();objects.add(face);inp=c.features.moveFeatures.createInput2(objects);assert inp.defineAsTranslateXYZ(g.value('-nose_fascia_fit_gap'),g.value('0 mm'),g.value('0 mm'),True);move=c.features.moveFeatures.add(inp);move.name='Axial service-face clearance';assert move.bodies.count==1
 body=g.combine(body,[move.bodies.item(0)],fusion.FeatureOperations.CutFeatureOperation,'Provide service assembly clearance');assert d.computeAll();assert c.bRepBodies.count==1;body=c.bRepBodies.item(0);body.name='Nose surround'
 issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues
 occ.isLightBulbOn=True;body.isLightBulbOn=True
 folder=os.path.join(tempfile.gettempdir(),'tinfox-native');step=os.path.join(folder,'body_nose_surround-intent.step');stl=os.path.join(folder,'body_nose_surround-intent.stl');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(step,c));options=d.exportManager.createSTLExportOptions(c,stl);options.unitType=fusion.DistanceUnits.MillimeterDistanceUnits;options.meshRefinement=fusion.MeshRefinementSettings.MeshRefinementHigh;assert d.exportManager.execute(options);occ.isLightBulbOn=False
 print(json.dumps({'part':'body_nose_surround','features':c.features.count,'feature_names':[f.name for f in c.features],'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'fitted_splines':sum(s.sketchCurves.sketchFittedSplines.count for s in c.sketches),'control_splines':sum(s.sketchCurves.sketchControlPointSplines.count for s in c.sketches),'volume_mm3':body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000,'paths':[step,stl],'saved':False,'source_of_truth_changed':False}))
'''
r=rpc(script,'nose-intent-finish',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/nose-intent-build.json').write_text(json.dumps(record,indent=2))
for path in record['paths']:fetch(path,Path(path).name)
print(json.dumps(record,indent=2))
