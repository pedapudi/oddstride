"""Check the disputed section directly in Fusion, without STEP translation."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
script='''import adsk.core as core,adsk.fusion as fusion,json

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);c=next(o.component for o in d.rootComponent.occurrences if o.component.partNumber=='CANDIDATE_body_nose_surround');before=(c.features.count,c.sketches.count,c.constructionPlanes.count)
 offset=40.321092140007075;inp=c.constructionPlanes.createInput();inp.setByOffset(c.xYConstructionPlane,core.ValueInput.createByReal(offset/10));plane=c.constructionPlanes.add(inp);plane.name='TEMP section metrology';sketch=c.sketches.add(plane);sketch.name='TEMP section metrology';curves=sketch.projectCutEdges(c.bRepBodies.item(0));rows=[]
 for curve in curves:
  geo=curve.worldGeometry;e=geo.evaluator;ok,a,b=e.getParameterExtents();assert ok;ok,points=e.getStrokes(a,b,.0001);assert ok;ok,length=e.getLengthAtParameter(a,b);assert ok
  rows.append({'type':curve.objectType,'length_mm':length*10,'points_mm':[[p.x*10,p.y*10,p.z*10] for p in points]})
 assert sketch.deleteMe();assert plane.deleteMe();assert (c.features.count,c.sketches.count,c.constructionPlanes.count)==before
 print(json.dumps({'offset_mm':offset,'axis':'Z','curves':rows,'stroke_tolerance_mm':.001,'temporary_metrology_removed':True,'saved':False}))
'''
r=rpc(script,'nose-direct-native-section',timeout=90);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/nose-direct-native-section.json').write_text(json.dumps(record,indent=2));print({'curves':len(record['curves']),'perimeter':sum(c['length_mm'] for c in record['curves'])})
