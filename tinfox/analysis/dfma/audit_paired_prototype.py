"""Independent, read-only contact and service review of the frozen paired roll CAD."""
from pathlib import Path
import gzip
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

EXPECTED = "f265baac6868b9cede365abce32450c75e580291a0346ad451c05706031cd374"
TARGET = ROOT / "fusion_native/snapshots/paired-bearing-target" / EXPECTED
raw = (TARGET / "model.json").read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED
model = json.loads(raw)
b.P.update(model["parameters"])
FROZEN = HERE / "paired-prototype-input" / EXPECTED
FROZEN.mkdir(parents=True, exist_ok=True)
(FROZEN / "model.json.gz").write_bytes(gzip.compress(raw))
source = TARGET / "source/paired_roll.py"
shutil.copy2(source, FROZEN / source.name)
hashes = {}
for part in model["parts"]:
    key = part["mesh"]
    if part.get("leg") not in ("FL", "RL"):
        continue
    if not any(x in part["name"] for x in ("roll_", "motor_carrier", "carrier_", "stator_", "knee_axle", "axle_", "thigh_inner", "thigh_outer")):
        continue
    p = TARGET / "step" / (key + ".step")
    if not p.exists():
        published = ROOT / "output/paired-roll-work"
        assert hashlib.sha256((published / "model.json").read_bytes()).hexdigest() == EXPECTED
        p = published / "step" / (key + ".step")
    if p.exists():
        shutil.copy2(p, FROZEN / p.name)
        hashes[key] = hashlib.sha256(p.read_bytes()).hexdigest()
assert hashlib.sha256((TARGET / "model.json").read_bytes()).hexdigest() == EXPECTED
(FROZEN / "manifest.json").write_text(json.dumps(hashes, indent=2))
solids = {}
def read(key):
    if key not in solids:
        solids[key] = cq.importers.importStep(str(FROZEN / (key + ".step"))).val()
    return solids[key]

def volume(s):
    v = sum(z.Volume() for z in s.Solids())
    return max(0.0, v)

checks = []
def contact(name, moving, receiving, direction, depth=.02):
    v = volume(moving.translate(tuple(depth*x for x in direction)).intersect(receiving))
    checks.append({"check": name, "kind": "axial_contact", "footprint_mm2": v/depth,
                   "passed": v > 1e-6})

def clearance(name, a, c):
    v = volume(a.intersect(c))
    plausible = v <= min(volume(a), volume(c)) + 1e-4
    checks.append({"check": name, "kind": "rigid_clearance", "overlap_mm3": v if plausible else None,
                   "passed": plausible and v < 1e-4})

for front in (1, -1):
    print("Checking canonical carrier", front, flush=True)
    cup = read(f"motor_carrier_{front}")
    housing = read(f"roll_cartridge_{front}")
    retainer = read(f"roll_outer_retainer_{front}")
    closure = read(f"hip_stator_closure_{front}")
    backplate = read(f"roll_inner_backplate_{front}")
    inner = read(f"roll_inner_spacer_{front}")
    outer = read(f"roll_outer_spacer_{front}")
    rear_bearing = read(f"roll_bearing_6810_{front}_0")
    front_bearing = read(f"roll_bearing_6810_{front}_1")
    contact(f"{front} rear outer race shoulder", rear_bearing, housing, (-front,0,0))
    contact(f"{front} front outer race retainer", front_bearing, retainer, (front,0,0))
    contact(f"{front} rear inner race backplate", rear_bearing, backplate, (-front,0,0))
    contact(f"{front} front inner race shoulder", front_bearing, cup, (front,0,0))
    contact(f"{front} rear outer spacer", outer, rear_bearing, (-front,0,0))
    contact(f"{front} front outer spacer", outer, front_bearing, (front,0,0))
    contact(f"{front} rear inner spacer", inner, rear_bearing, (-front,0,0))
    contact(f"{front} front inner spacer", inner, front_bearing, (front,0,0))
    for a in (20,140,260):
        bolt = read(f"roll_retainer_bolt_{a}_front{front}")
        nut = read(f"roll_retainer_nut_{a}_front{front}")
        contact(f"{front} retainer head {a}", bolt, retainer, (-front,0,0))
        contact(f"{front} retainer nut {a}", nut, housing, (front,0,0))
        for travel in (0,2,5,10):
            clearance(f"{front} rear nut axial insertion {a} {travel}", nut.translate((-front*travel,0,0)), housing)
    for a in (90,215,325):
        nut = read(f"carrier_closure_nut_{a}_front{front}")
        washer = read(f"carrier_closure_washer_{a}_front{front}")
        bolt = read(f"carrier_closure_bolt_{a}_front{front}")
        contact(f"{front} closure washer {a}", washer, closure, (0,-1,0))
        contact(f"{front} closure head {a}", bolt, washer, (0,-1,0))
        contact(f"{front} closure nut {a}", nut, cup, (0,1,0))
    print("Contact failures", [c for c in checks if not c["passed"]], flush=True)
    motor = b.motor_envelope((front*5,0,0))
    for travel in (0,1,5,10,20,35,50,65):
        clearance(f"{front} motor axial insertion {travel}", motor.translate((0,travel,0)),cup)
    for travel in (0,.1,1,3,10,20):
        clearance(f"{front} stator closure axial removal {travel}",closure.translate((0,travel,0)),cup)

    # Generic open-ended holding wrench: circular head with a7.1mm opening,
    # 100mm radial handle, and3.6mm thickness. Two head widths bracket common
    # compact and larger7mm wrenches; this is not a particular vendor CAD model.
    for width in (16.0,17.5):
        head = b.cyl(width/2,3.6,(0,-15.6,0))
        handle = b.box(100,3.6,8,(55,-13.8,0))
        mouth = b.box(20,6,7.1,(-5.8,-13.8,0))
        wrench = head.fuse(handle).cut(mouth)
        for a in (90,215,325):
            x,z = 47*math.cos(math.radians(a)),47*math.sin(math.radians(a))
            wrench_a = wrench.rotate((0,0,0),(0,1,0),-a).translate((front*5+x,0,z))
            for travel in (0,3,8,15,25):
                delta=(travel*math.cos(math.radians(a)),0,travel*math.sin(math.radians(a)))
                tool=wrench_a.translate(delta)
                for label,body in [("cup",cup),("closure",closure),("housing",housing),("retainer",retainer),("motor",motor)]:
                    clearance(f"{front} wrench W{width} lug{a} travel{travel} {label}",tool,body)
    (HERE / "paired-prototype-partial.json").write_text(json.dumps(checks,indent=2)+"\n")
    print("Finished",front,"checks",len(checks),"failures",[c for c in checks if not c["passed"]],flush=True)

summary={"model_sha256":EXPECTED,"checker":"Independent exact exported STEP contacts, axial service paths and generic open-end wrench probes.",
         "conditions":"Front/rear canonical left-side assemblies. Bare motor proxy reproduces the modeled dimensions/offset. Nut/washer seating uses0.02mm inward probes. Wrench opening7.1mm, thickness3.6mm, head widths16/17.5mm, 100mm handle. Nut held stationary while bolt turns.",
         "limitations":"No whole-body tool clearance, particular purchased wrench, ring-internal/seal surfaces, fits, preload, deformation, manufacturing tolerances, strength or full CAM access qualification. Existing model interference checks remain separate.",
         "checks":checks,"failed_checks":[x for x in checks if not x["passed"]]}
(HERE / "paired-prototype-review.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps({"checks":len(checks),"failures":summary["failed_checks"]},indent=2))
