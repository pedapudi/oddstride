"""Calculate geometry and contact-force joint moments; Python standard library only.

This is not inverse dynamics. Link gravity, inertial moments, friction, real
transmission kinematics, contact feasibility and motor thermal dynamics are absent.
Masses and force shares are scenario inputs, not estimates from a finished design.
"""

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JOINTS = ("hip_roll", "hip_pitch", "knee_pitch")


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0])


def rx(angle, v):
    c, s = math.cos(angle), math.sin(angle)
    return (v[0], c*v[1] - s*v[2], s*v[1] + c*v[2])


def ry(angle, v):
    c, s = math.cos(angle), math.sin(angle)
    return (c*v[0] + s*v[2], v[1], -s*v[0] + c*v[2])


def geometry(q, thigh, shank, offset):
    """Return foot, origins and axes for a left leg in a level body frame.

    x is forward, y is left, z is up. q is roll, hip pitch, knee pitch in
    radians. The thigh points down at zero pitch. Positive knee pitch bends
    the shank toward negative x. The shank ends at the ideal foot contact.
    """
    roll, hip, knee = q
    hip_origin = rx(roll, (0, offset, 0))
    knee_origin = add(hip_origin, rx(roll, ry(hip, (0, 0, -thigh))))
    foot = add(knee_origin, rx(roll, ry(hip + knee, (0, 0, -shank))))
    origins = ((0, 0, 0), hip_origin, knee_origin)
    pitch_axis = rx(roll, (0, 1, 0))
    return foot, origins, ((1, 0, 0), pitch_axis, pitch_axis)


def jacobian_columns(q, thigh, shank, offset):
    foot, origins, axes = geometry(q, thigh, shank, offset)
    return tuple(cross(axis, sub(foot, origin)) for axis, origin in zip(axes, origins))


def contact_moments(q, force, thigh, shank, offset):
    """Signed external joint moments J^T F, in N m, from foot force only.

    The actuator's balancing contribution has opposite sign. Absolute values
    are used for sizing. This contribution is not a conservative total bound.
    """
    return tuple(dot(column, force) for column in jacobian_columns(q, thigh, shank, offset))


def motor_demands(moments, ratios, efficiencies):
    """Approximate magnitudes for a motoring transmission at one posture.

    Ratio is actuator-output speed / joint speed. A constant efficiency is
    a screening approximation, not a static friction or regenerative model.
    """
    if any(r <= 0 for r in ratios) or any(not 0 < e <= 1 for e in efficiencies):
        raise ValueError("Ratios must be positive and efficiencies in (0, 1].")
    return tuple(abs(t) / (r * e) for t, r, e in zip(moments, ratios, efficiencies))


def clearance(thigh, shank, angle_deg, skid_drop):
    """Level-body, zero-roll height with equal/opposite link inclinations."""
    hip_height = (thigh + shank) * math.cos(math.radians(angle_deg))
    return hip_height, hip_height - skid_drop


def calculate(config):
    clearances, loads = [], []
    thigh, shank = config["thigh_m"], config["shank_to_contact_m"]
    for angle in config["stance_link_angles_deg"]:
        for drop in config["hip_to_skid_offsets_m"]:
            hip, belly = clearance(thigh, shank, angle, drop)
            clearances.append({"link_angle_deg": angle, "skid_drop_mm": drop*1000,
                               "hip_height_mm": hip*1000, "belly_clearance_mm": belly*1000,
                               "belly_clearance_in": belly/0.0254})
    for mass in config["total_mass_cases_kg"]:
        for case in config["cases"]:
            q = tuple(math.radians(a) for a in case["q_deg"])
            fz = mass * config["gravity_m_s2"] * case["load_share"] * case["vertical_load_factor"]
            force = (fz*case["fx_over_fz"], fz*case["fy_over_fz"], fz)
            moments = contact_moments(q, force, thigh, shank, config["hip_lateral_offset_m"])
            foot, _, _ = geometry(q, thigh, shank, config["hip_lateral_offset_m"])
            for transmission in config["transmission_comparisons"]:
                demands = motor_demands(moments, transmission["ratios"], transmission["efficiencies"])
                row = {"mass_kg": mass, "case": case["name"], "transmission": transmission["name"]}
                row.update({f"q_{name}_deg": val for name, val in zip(JOINTS, case["q_deg"])})
                row.update({f"foot_{axis}_mm": val*1000 for axis, val in zip("xyz", foot)})
                row.update({f"force_{axis}_N": val for axis, val in zip("xyz", force)})
                row.update({f"joint_{name}_Nm": val for name, val in zip(JOINTS, moments)})
                row.update({f"motor_{name}_Nm": val for name, val in zip(JOINTS, demands)})
                loads.append(row)
    return clearances, loads


def write_csv(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: round(val, 6) if isinstance(val, float) else val for key, val in row.items()})


def main():
    config = json.loads((ROOT / "assumptions.json").read_text())
    clearances, loads = calculate(config)
    write_csv(ROOT / "clearance.csv", clearances)
    write_csv(ROOT / "contact_loads.csv", loads)
    print("PRELIMINARY: foot-force moments only; no capability certification.")
    print("Clearance with a 70 mm hip-to-skid offset:")
    for row in clearances:
        if math.isclose(row["skid_drop_mm"], 70):
            print(f"  {row['link_angle_deg']:2} deg: {row['belly_clearance_mm']:.1f} mm / {row['belly_clearance_in']:.2f} in")
    print("15 kg total mass, direct joint reference: roll / hip pitch / knee in N m")
    for row in loads:
        if row["mass_kg"] == 15 and row["transmission"] == "Direct joint reference":
            values = " / ".join(f"{row[f'motor_{name}_Nm']:.2f}" for name in JOINTS)
            print(f"  {row['case']}: {values}")


if __name__ == "__main__":
    main()
