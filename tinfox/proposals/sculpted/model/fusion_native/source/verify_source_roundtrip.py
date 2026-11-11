"""Check a STEP-reference anomaly against the exact, frozen source mesh identity.

The BRep archive is an independent audit reference only. It is never sent to
Fusion to author geometry. The original STEP and its audit results are retained.
"""
import json,hashlib,sys
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))
import service_design
from audit_part import volume
key=sys.argv[1] if len(sys.argv)>1 else 'shin_outer'
assert key in ['shin_outer','shin_outer_right']
manifest=json.loads((ROOT/'manifests/parts.json').read_text());record=next(p for p in manifest['parts'] if p['id']==key)
original=service_design.shin(True).translate((0,-16,0))
if key.endswith('_right'):original=original.mirror('XZ')
vertices,faces=original.tessellate(.12,.12)
mesh={'vertices':[[round(c,6) for c in p.toTuple()] for p in vertices],'faces':[list(f) for f in faces]}
mesh_sha=hashlib.sha256(json.dumps(mesh,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert mesh_sha==record['source_mesh_sha256'],('Source mesh identity differs',mesh_sha,record['source_mesh_sha256'])
path=ROOT/'snapshots/brep'/f'{key}.brep';path.parent.mkdir(exist_ok=True);original.exportBrep(str(path));restored=cq.Shape.importBrep(str(path));step=cq.importers.importStep(str(ROOT/record['source_step'])).val()
point=[14.456977652729044,69.16885682435795,-55.34324266650307]
if key.endswith('_right'):point[1]*=-1
vertex=cq.Vertex.makeVertex(*point)
rows={name:{'adaptive_volume_mm3':volume(shape)[0],'anomaly_point_distance_mm':shape.distance(vertex),'valid':shape.isValid()} for name,shape in [('original',original),('brep_roundtrip',restored),('step_roundtrip',step)]}
assert abs(rows['original']['adaptive_volume_mm3']-rows['brep_roundtrip']['adaptive_volume_mm3'])<.001
assert rows['brep_roundtrip']['anomaly_point_distance_mm']<1e-6
result={'part':key,'source_model_sha256':record['source_model_sha256'],'source_mesh_sha256':mesh_sha,'mesh_identity_exact':True,'probe_point_mm':point,'comparisons':rows,'source_brep':str(path.relative_to(ROOT)),'source_brep_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'scope':'Source regeneration matches every frozen quantized mesh coordinate and triangle exactly. Lossless BRep reference is for audits only; native custom-part authoring never imports it. STEP source remains preserved; its round-trip distance discrepancy is recorded.'}
(ROOT/'audits'/('source-roundtrip-anomaly.json' if key=='shin_outer' else key+'-source-roundtrip-anomaly.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
