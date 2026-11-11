"""Check straight motor withdrawal against the current one-piece carrier only."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import cadquery as cq
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "proposals/sculpted/model"
sys.path.insert(0, str(ROOT))
import build as b
import printed_carrier

MODEL = ROOT / "output/clamp-seat-work/model.json"
raw = MODEL.read_bytes(); data = json.loads(raw); b.P.update(data["parameters"])
stamp = hashlib.sha256(raw).hexdigest()
FROZEN = HERE / "hip-motor-service-input" / stamp
FROZEN.mkdir(parents=True, exist_ok=True)

def volume(s): return sum(x.Volume() for x in s.Solids())
rows = []
printed = None
for front in (1, -1):
    key = "motor_carrier_" + str(front)
    source = ROOT / "output/clamp-seat-work/step" / (key + ".step")
    frozen = FROZEN / source.name
    shutil.copy2(source, frozen)
    carrier = cq.importers.importStep(str(frozen)).val()
    motor = b.motor_envelope()
    paths = []
    for axis, vector in [("+X",(1,0,0)),("-X",(-1,0,0)),("+Y",(0,1,0)),("-Y",(0,-1,0)),("+Z",(0,0,1)),("-Z",(0,0,-1))]:
        samples=[]
        for travel in (0,.1,.25,.5,1,1.1,1.25,2,2.25,2.5,3,5,10,20,40,60,80):
            overlap=volume(carrier.intersect(motor.translate(tuple(travel*v for v in vector))))
            plausible = -1e-4 <= overlap <= min(volume(carrier), volume(motor)) + 1e-4
            samples.append({"travel_mm":travel,"intersection_mm3":overlap if plausible else None,
                            "boolean_volume_plausible":plausible})
        paths.append({"direction":axis,"samples":samples,
                      "clear_straight_path":all(s["intersection_mm3"] is not None and s["intersection_mm3"]<1e-4 for s in samples)})
    rows.append({"carrier":key,"step_sha256":hashlib.sha256(frozen.read_bytes()).hexdigest(),
                 "closed_solids":len(carrier.Solids()),"valid":carrier.isValid(),"paths":paths})
    if front == 1:
        split, hardware = printed_carrier.split_carrier(carrier, front)
        flange = split["flange"]
        cq.exporters.export(flange, str(FROZEN / "optional_printed_flange.step"))
        printed = {"source_sha256": hashlib.sha256(Path(printed_carrier.__file__).read_bytes()).hexdigest(),
                   "valid": flange.isValid(), "closed_solids": len(flange.Solids()),
                   "samples": [{"translation_mm": list(v), "intersection_mm3": volume(flange.intersect(motor.translate(v)))}
                               for v in [(0,.5,0),(0,-2,0),(3,0,0),(-3,0,0),(0,0,3),(0,0,-3)]]}
out={"model_sha256":stamp,"checker":"Exact current STEP carrier against generator's motor reference solid; front and rear canonical carriers; six straight translations.",
     "scope":"Carrier only, all removable hardware and surrounding parts absent. No tilted multi-axis removal search. Vendor motor details, wires, tools and print deformation omitted. The optional existing printed split is generated separately from its unmodified source. Implausible boolean volumes at exact tangency are marked null and do not supply a penetration measurement.",
     "carriers":rows,"existing_optional_printed_split":printed}
(HERE/"hip-motor-service.json").write_text(json.dumps(out,indent=2)+"\n")
for row in rows:
 print(row["carrier"],"valid",row["valid"],"solids",row["closed_solids"],flush=True)
 for p in row["paths"]:
  print(p["direction"],next((s for s in p["samples"] if s["intersection_mm3"] is not None and s["intersection_mm3"]>1e-4),None),"clear",p["clear_straight_path"],flush=True)
