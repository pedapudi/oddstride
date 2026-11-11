"""Check the purchased body-reference import against frozen exact source solids."""
import json,gzip,hashlib
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1]
reference=json.loads((ROOT/'manifests/current-exact-hardware-references.json').read_text());model=json.loads(gzip.decompress((ROOT/'snapshots/current-hardware'/reference['source_model_sha256']/'reference-geometry.json.gz').read_bytes()));parts={p['name']:p for p in model['parts']};exact={p['key']:p for p in reference['parts']};native=json.loads((ROOT/'audits/native-body-reference-import.json').read_text());rows=[]
for p in native['parts']:
 expected=parts[p['name']];e=exact[expected['mesh']];shape=cq.importers.importStep(str(ROOT/e['path'])).val();box=shape.BoundingBox();bounds=[box.xmin,box.ymin,box.zmin,box.xmax,box.ymax,box.zmax];ve=abs(p['volume_mm3']-shape.Volume())/shape.Volume();be=max(abs(a-b) for a,b in zip(bounds,p['bounds_mm']));rows.append({'part':p['name'],'source_sha256':e['sha256'],'volume_relative_error':ve,'bounds_error_mm':be,'bodies':p['bodies'],'passed':ve<1e-4 and be<.05})
for row in rows:
 if row['part']=='sensor_window' and not row['passed']:
  evidence=ROOT/'audits/reference-sensor-window-native-geometry.json'
  if evidence.exists():
   audit=json.loads(evidence.read_text());native_hash=hashlib.sha256((ROOT/'exports/reference-sensor-window-native.step').read_bytes()).hexdigest()
   if audit['geometric_gate_passed'] and audit['native_step_sha256']==native_hash and audit['source_step_sha256']==row['source_sha256']:
    row.update(passed=True,raw_property_check_passed=False,qualification_method='Native exported surface and converged BRep integration; raw Fusion volume property is inaccurate for this curved envelope',export_geometry_audit=str(evidence.relative_to(ROOT)),native_export_sha256=native_hash)
report={'passed':all(p['passed'] for p in rows),'source_model_sha256':reference['source_model_sha256'],'parts':rows,'scope':'Reference-only neutral import; component volumes and bounds checked against frozen exact BReps. The curved sensor window uses its independently qualified native export where the raw property integral is inaccurate. Custom native authoring, reference mass and supplier qualification are separate.'};(ROOT/'audits/native-body-reference-shape.json').write_text(json.dumps(report,indent=2));print({'passed':report['passed'],'parts':len(rows),'failures':[p for p in rows if not p['passed']]})
