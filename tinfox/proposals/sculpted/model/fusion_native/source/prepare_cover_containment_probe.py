"""Prepare an independent inside/outside check for native physical-property errors."""
import json,hashlib,random
from pathlib import Path
import cadquery as cq
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN,TopAbs_OUT
ROOT=Path(__file__).resolve().parents[1];target=next(p for p in json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low']['custom_parts'] if p['key']=='body_center_0');path=ROOT/target['files']['step']['path'];s=cq.importers.importStep(str(path)).val();classifier=BRepClass3d_SolidClassifier(s.wrapped);rng=random.Random(971);rows=[]
for i in range(16000):
 point=[rng.uniform(-135,135),rng.uniform(-116,116),rng.uniform(-10,56)];classifier.Perform(gp_Pnt(*point),1e-7);state=classifier.State()
 if state not in [TopAbs_IN,TopAbs_OUT]:continue
 rows.append({'point_mm':point,'source_inside':state==TopAbs_IN})
r={'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'points':rows,'inside_count':sum(p['source_inside'] for p in rows),'scope':'Deterministic volume-distributed point containment probe; statistical check, not a volume integration proof.'};(ROOT/'snapshots/current-targets/cover-containment-probe.json').write_text(json.dumps(r));print({'points':len(rows),'inside':r['inside_count']})
