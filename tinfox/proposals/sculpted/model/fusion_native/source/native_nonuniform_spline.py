"""Native nonuniform cubic control splines driven by a dimensional skeleton.

Fusion's supported knot insertion creates the editable control frame. No curve,
mesh or solid is imported. The coefficients supplied by callers express the
original design stations and endpoint tangents, not a sampled outline.
"""
def native_nonuniform_cubic(sketch, drivers, internal_knots):
 assert len(drivers)==4+len(internal_knots)
 seed=[core.Point3D.create(p.geometry.x+.123,p.geometry.y+.456,p.geometry.z+.789)for p in drivers[:4]]
 curve=sketch.sketchCurves.sketchControlPointSplines.add(seed,fusion.SplineDegrees.SplineDegreeThree)
 assert curve.isControlFrameDisplayed
 for knot in internal_knots:
  ok,lo,hi=curve.evaluator.getParameterExtents();assert ok
  assert 0<float(knot)<1
  assert curve.addControlPoint(lo+float(knot)*(hi-lo))
 assert len(curve.controlPoints)==len(drivers)
 for control,driver in zip(curve.controlPoints,drivers):
  delta=control.geometry.vectorTo(driver.geometry)
  if delta.length>1e-10:assert control.move(delta)
  sketch.geometricConstraints.addCoincident(control,driver)
 return curve
