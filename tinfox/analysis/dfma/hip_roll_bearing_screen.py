"""Read-only bearing packaging and reaction screening; no CAD mutation."""
from pathlib import Path
import gzip
import hashlib
import json
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
MODEL = HERE / "review-model.json.gz"
raw = gzip.decompress(MODEL.read_bytes())
model = json.loads(raw)
sys.path.insert(0, str(HERE.parents[1] / "proposals/sculpted/model"))
import kinematics as k
k.P.update(model["parameters"])

bearings = {
    "Koyo 6808 2RS": {"d_mm": 40, "D_mm": 52, "B_mm": 7, "Cr_N": 6150, "C0r_N": 4200, "mass_kg": .033},
    "Koyo 6809 2RS": {"d_mm": 45, "D_mm": 58, "B_mm": 7, "Cr_N": 7750, "C0r_N": 5400, "mass_kg": .040},
    "Koyo 6810 2RS": {"d_mm": 50, "D_mm": 65, "B_mm": 7, "Cr_N": 8200, "C0r_N": 6100, "mass_kg": .052},
}
cases = []
for pose in ("stand", "raised", "reach", "crouch"):
    for loading, mass, factor, supports in (
        ("loaded_two_foot", 14.3, 1, 2),
        ("loaded_one_foot", 14.3, 1, 1),
        ("unloaded_3g_two_foot", 13.3, 3, 2),
    ):
        foot, origins, axes = k.contacts("FL", model["poses"][pose]["FL"])
        center = np.array([k.P["hip_x"] - 60, k.P["roll_y"], 0])
        r = (foot - center) / 1000
        F = mass * 9.81 * factor / supports
        moment = np.cross(r, [0, 0, F])
        M = float(np.linalg.norm(moment[1:]))
        reactions = []
        for spacing in (14, 20):
            # Conservative scalar sum of shared radial force and moment couple.
            R = F / 2 + M / (spacing / 1000)
            reactions.append({
                "center_spacing_mm": spacing,
                "maximum_radial_reaction_screen_N": R,
                "C0r_over_reaction": {name: b["C0r_N"] / R for name, b in bearings.items()},
            })
        cases.append({"pose": pose, "loading": loading, "force_per_foot_N": F,
                      "foot_relative_pair_midpoint_mm": (r * 1000).tolist(),
                      "roll_axis_moment_Nm": float(moment[0]),
                      "transverse_overturning_moment_Nm": M, "reactions": reactions})

out = {
    "model_sha256": hashlib.sha256(raw).hexdigest(),
    "source": "Frozen generated geometry; left front leg; bearing pair centered at existing roll bearing midpoint.",
    "limitations": [
        "Proposed architecture only; no changed CAD or Fusion model is validated.",
        "Vertical point force only; omits horizontal/axial contact force, limb inertia, bearing stiffness and motor-bearing load sharing.",
        "3g and one-foot cases are force screens, not physically feasible gaits or qualified jumps.",
        "C0r/reaction is a catalog static-rating ratio, not a structural safety factor or service-life prediction.",
        "Pair spacing, finish fits, shoulders, retention and preload remain to be designed.",
    ],
    "bearings": bearings,
    "packaging": [{"spacing_mm": s, "bearing_pack_length_mm": s + 7,
                   "housing_length_assuming_2mm_each_end_mm": s + 11,
                   "growth_over_current_16_3mm_barrel_mm": s + 11 - 16.3,
                   "journal_growth_over_current_13_3mm_mm": s + 7 - 13.3}
                  for s in (14, 20)],
    "cases": cases,
}
(HERE / "hip-roll-bearing-screen.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps({"model_sha256": out["model_sha256"], "cases": len(cases), "packaging": out["packaging"]}, indent=2))
