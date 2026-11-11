"""Inspect native offset topology and remove the diagnostic sketch afterward."""
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json

def run(_context: str):
 app=core.Application.get();d=fusion.Design.cast(app.activeProduct);c=next(o.component for o in d.rootComponent.occurrences if o.component.partNumber=='CANDIDATE_cohesive_thigh_master');assert c.features.count==3;source=c.sketches.item(0);pin=c.constructionPlanes.createInput();pin.setByOffset(c.xZConstructionPlane,core.ValueInput.createByString('lc_thigh_inner_y+lc_shell_wall'));plane=c.constructionPlanes.add(pin);sk=c.sketches.add(plane);curves=[]
 for original in source.findConnectedCurves(source.sketchCurves.sketchArcs.item(0)):curves.extend(sk.project2([original],True))
 before=sk.profiles.count;inp=sk.geometricConstraints.createOffsetInput(curves,core.ValueInput.createByString('-lc_shell_wall'));offset=sk.geometricConstraints.addOffset2(inp);after=sk.profiles.count
 for curve in curves:curve.isConstruction=True
 rows=[{'type':a.objectType,'construction':a.isConstruction,'linked':a.isReference,'start':a.startSketchPoint.geometry.asArray(),'end':a.endSketchPoint.geometry.asArray()} for a in sk.sketchCurves]
 result={'before_profiles':before,'after_offset_profiles':after,'after_construction_profiles':sk.profiles.count,'curves':rows,'offset_type':offset.objectType,'offset_props':[a for a in dir(offset) if not a.startswith('_')]};assert sk.deleteMe();assert plane.deleteMe();print(json.dumps(result))
'''
r=rpc(s,'cohesive-thigh-offset-inspection',timeout=60);print(r)
