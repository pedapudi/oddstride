"""Recover the five design sections as two exact cubic guide spans."""
import json, sys
from pathlib import Path
import numpy as np
from scipy.interpolate import BSpline
from scipy.optimize import brentq
from OCP.BRep import BRep_Tool

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
import seamless_limb as source

records = {}
for inner, label in [(False, 'outer'), (True, 'inner')]:
    rows = [(-26,40,34,4),(-40,35,34,9),(-75,32,34,11),(-105,29,34,11),(-128,26,34,10)] if inner else source.SHIN_ROWS
    shape = source.smooth_loft([source.shin_wire(*row, inset=4 if inner else 0) for row in rows])
    surfaces = [BRep_Tool.Surface_s(f.wrapped) for f in shape.Faces()]
    surfaces = [s for s in surfaces if hasattr(s, 'NbVPoles')]
    s = surfaces[0]
    knots = [s.VKnot(i) for i in range(1, s.NbVKnots()+1)]
    full = [s.VKnot(i) for i in range(1, s.NbVKnots()+1) for _ in range(s.VMultiplicity(i))]
    basis = BSpline(full, np.eye(s.NbVPoles()), s.VDegree())
    zp = np.array([s.Pole(1,i).Z() for i in range(1,s.NbVPoles()+1)])
    ts = [knots[0]] + [brentq(lambda t: float(basis(t) @ zp)-z, knots[0], knots[-1]) for z,*_ in rows[1:-1]] + [knots[-1]]
    inverse = np.linalg.inv(basis(ts))
    spans = []
    for lo, hi in zip(knots, knots[1:]):
        weights = np.vstack([basis(lo), basis(lo)+(hi-lo)/3*basis.derivative()(lo), basis(hi)-(hi-lo)/3*basis.derivative()(hi), basis(hi)]) @ inverse
        spans.append(weights.tolist())
    assert s.VDegree() == 3 and len(spans) == 2
    records[label] = {'degree':3, 'station_parameters':ts, 'knots':knots, 'span_station_coefficients':spans,
                      'internal_normalized_knots':[(x-knots[0])/(knots[-1]-knots[0]) for x in knots[1:-1]],
                      'station_to_control_pole_coefficients':inverse.tolist(),
                      'description':'Two C2-continuous cubic spans derived from the five original station dimensions; no sampled facets.'}
path = ROOT/'snapshots/latest-leg/rounded-shin-guide-interpolation.json'
path.write_text(json.dumps(records,indent=2))
print(path)
