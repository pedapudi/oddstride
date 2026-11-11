"""Verify a compact native control spline against the exact thigh design curve."""
import json
from pathlib import Path
import numpy as np
from scipy.interpolate import BSpline
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
row=json.loads((ROOT/'snapshots/latest-leg/slim-thigh-spline-skeleton.json').read_text())['sides'][0]
knots=row['internal_normalized_knots'];poles=row['source_control_poles_mm'];ts=np.linspace(0,1,101)
expected=BSpline([0]*4+knots+[1]*4,np.array(poles),3)(ts).tolist()
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py','native_nonuniform_spline.py'])+'''
def run(_context: str):
 import json,time
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert d.activateRootComponent();before=root.occurrences.count;assert not d.userParameters.itemByName('test_nurbs_scale');o=root.occurrences.addNewComponent(core.Matrix3D.create());c=o.component;c.name='Temporary native spline verification';c.partNumber='CANDIDATE_spline_verification';g=IntentGeometry(d,c);g.parameter('test_nurbs_scale',1,'');sk=c.sketches.add(c.xYConstructionPlane);sk.name='Ten native control poles driven by one test scale';sk.isComputeDeferred=True;drivers=[];xdrivers={};tick=time.monotonic()
 for x,z in POLES:
  xe=f'({x:.17g} mm)*test_nurbs_scale';ye=f'({-z:.17g} mm)*test_nurbs_scale';p=g.skeleton_point(sk,xe,ye);key=round(x,10);g.point_dimensions(sk,p,None if key in xdrivers else xe,ye)
  if key in xdrivers:sk.geometricConstraints.addVerticalPoints(xdrivers[key],p)
  xdrivers[key]=p;drivers.append(p)
 curve=native_nonuniform_cubic(sk,drivers,KNOTS);sk.isComputeDeferred=False
 def check(scale):
  ok,lo,hi=curve.evaluator.getParameterExtents();assert ok;errors=[]
  for t,(x,z)in zip(TS,EXPECTED):
   ok,p=curve.evaluator.getPointAtParameter(lo+t*(hi-lo));assert ok;errors.append(p.distanceTo(core.Point3D.create(x*scale/10,-z*scale/10,0))*10)
  assert max(errors)<1e-6,max(errors);return max(errors)
 baseline=check(1);param=d.userParameters.itemByName('test_nurbs_scale');param.expression='1.01';assert d.computeAll();edited=check(1.01);param.expression='1';assert d.computeAll();restored=check(1);count=len(curve.controlPoints);degree=int(curve.degree);assert count==10 and curve.isControlFrameDisplayed;assert o.deleteMe();assert root.occurrences.count==before;assert param.isDeletable;assert param.deleteMe();print(json.dumps({'passed':True,'control_points':count,'source_degree':3,'native_degree_enum':degree,'baseline_max_error_mm':baseline,'edited_max_error_mm':edited,'restored_max_error_mm':restored,'temporary_component_removed':True,'elapsed_seconds':time.monotonic()-tick,'method':'Native cubic plus six supported control-point insertions; dimensional constraints, no imported curve.'}))
'''.replace('POLES',repr(poles)).replace('KNOTS',repr(knots)).replace('EXPECTED',repr(expected)).replace('TS',repr(ts.tolist()))
r=rpc(s,'native-nonuniform-spline-proof',timeout=300);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/native-nonuniform-spline-proof.json').write_text(json.dumps(record,indent=2));print(record)
