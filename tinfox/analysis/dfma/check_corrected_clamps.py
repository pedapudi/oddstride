"""Independently check nominal washer footprints on the corrected shell target."""
from pathlib import Path
import hashlib
import json
import math
import shutil
import sys
import cadquery as cq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "proposals/sculpted/model"
sys.path.insert(0, str(ROOT))
import build as b

TARGET = ROOT / "output/clamp-seat-work"
raw = (TARGET / "model.json").read_bytes()
stamp = hashlib.sha256(raw).hexdigest()
frozen = HERE / "corrected-clamp-input" / stamp
frozen.mkdir(parents=True, exist_ok=True)
copies = {}
def read(key):
    src = TARGET / "step" / (key + ".step")
    dst = frozen / src.name
    if dst.exists():
        assert dst.read_bytes() == src.read_bytes(), "Target changed during review"
    else:
        shutil.copy2(src, dst)
    copies[key] = hashlib.sha256(dst.read_bytes()).hexdigest()
    return cq.importers.importStep(str(dst)).val()

def volume(s):
    return sum(z.Volume() for z in s.Solids())

rows = []
for family, index, x, z, bolt, nut in [
    ("thigh", 0, -36, -66, "bolt_0", "thigh_clamp_nut_0"),
    ("thigh", 1, 5, -70, "bolt_1", "thigh_clamp_nut_1"),
    ("shin", 37, 2, -30, "shin_clamp_bolt_37", "shin_clamp_nut_37"),
    ("shin", 105, 2, -105, "shin_clamp_bolt_105", "shin_clamp_nut_105"),
]:
    for outer in [False, True]:
        half = "outer" if outer else "inner"
        shell = read(family + "_" + half)
        washer = read(f"{family}_clamp_washer_{index}_{half}")
        hardware = read(nut if outer else bolt)
        direction = -1 if outer else 1
        depth = .05
        # Move the flat washer into its receiving floor. Area comes from
        # overlap volume/depth; no strain or clamp-pressure model is implied.
        contact = volume(washer.translate((0, direction * depth, 0)).intersect(shell)) / depth
        hw_contact = volume(hardware.translate((0, direction * depth, 0)).intersect(washer)) / depth
        y = 77.5 if outer else 56.5
        rings = {
            str(radius): [degree for degree in range(0, 360, 5)
                          if not shell.isInside((x + radius * math.cos(math.radians(degree)),
                                                 y, z + radius * math.sin(math.radians(degree))), 1e-5)]
            for radius in (6.3, 7.5, 8.7)
        }
        rows.append({"family": family, "index": index, "half": half,
                     "washer_shell_footprint_mm2": contact,
                     "hardware_washer_footprint_mm2": hw_contact,
                     "missing_6_3mm_radius_wall_samples_deg": rings["6.3"],
                     "missing_material_wall_ring_samples_deg": rings})

report = {
    "model_sha256": stamp,
    "checker": "Exact STEP solids; 0.05 mm inward contact probes and 5-degree wall samples at radii 6.3, 7.5 and 8.7 mm, at inner Y56.5/outer Y77.5.",
    "scope": "Nominal seated geometry only. Does not qualify contact pressure, sleeve/washer thickness intervals, preload, creep, slip, driver reach or loaded strength.",
    "source_step_sha256": copies,
    "rows": rows,
}
assert hashlib.sha256((TARGET / "model.json").read_bytes()).hexdigest() == stamp
(HERE / "corrected-clamp-contact.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
