"""Independently measure optional native stock-sleeve meshes; never export CAD."""
from pathlib import Path
import hashlib, json, math, sys, zipfile
from xml.etree import ElementTree as ET
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]/'proposals/sculpted/model'
sys.path.insert(0,str(ROOT))
from prepare_native_motor_complex import read_3mf
manifest=HERE/'candidate-manifest.json'
raw=manifest.read_bytes();data=json.loads(raw)
native=ROOT/'fusion_native';rows=[]
assert data['native_source_of_truth'] is False
stock=data['stock_references']
assert len(stock)==3 and sum(x['quantity'] for x in stock)==8
CORE='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
for r in stock:
 path=native/r['native_3mf'];stamp=hashlib.sha256(path.read_bytes()).hexdigest()
 assert stamp==r['native_3mf_sha256']
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  names=[n for n in z.namelist() if n.lower().endswith('.model')]
  assert len(names)==1;xml=ET.fromstring(z.read(names[0]))
 mesh=read_3mf(path)
 od,inside,length=r['nominal_od_id_length_mm']
 nominal=math.pi*(od*od-inside*inside)*length/4
 center=(mesh.bounds[0]+mesh.bounds[1])/2
 radius=np.linalg.norm(mesh.vertices[:,[0,2]]-center[[0,2]],axis=1)
 degenerate=int(np.count_nonzero(mesh.area_faces<1e-10))
 unique=int(np.count_nonzero(mesh.unique_faces()))
 components=len(mesh.split(only_watertight=False))
 checks={
  'sha256_matches':True,'zip_integrity':True,
  'units_declared_millimeter':xml.attrib.get('unit','millimeter')=='millimeter',
  'one_connected_surface':components==1,'closed':bool(mesh.is_watertight),
  'winding_consistent':bool(mesh.is_winding_consistent),'positive_volume':bool(mesh.volume>0),
  'no_degenerate_faces':degenerate==0,'no_duplicate_faces':unique==len(mesh.faces),
  'annular_topology':mesh.euler_number==0,
  'extents_match_nominal':bool(np.allclose(mesh.extents,[od,length,od],atol=.05)),
  'bounds_match_native_manifest':bool(np.allclose(mesh.bounds,np.array(r['native_bounds_mm']).reshape(2,3),atol=.05)),
  'inner_radius_matches':bool(abs(float(radius.min())-inside/2)<.025),
  'outer_radius_matches':bool(abs(float(radius.max())-od/2)<.025),
  'volume_matches_annular_stock':bool(abs(mesh.volume-nominal)/nominal<.005),
 }
 rows.append(dict(part=r['part'],quantity=r['quantity'],saved_version=r['saved_version'],
  native_3mf=str(path),sha256=stamp,bytes=path.stat().st_size,
  units=xml.attrib.get('unit','millimeter'),nominal_od_id_length_mm=r['nominal_od_id_length_mm'],
  measured_bounds_mm=mesh.bounds.tolist(),measured_inner_outer_radius_mm=[float(radius.min()),float(radius.max())],
  measured_volume_mm3=float(mesh.volume),analytic_volume_mm3=nominal,
  relative_volume_error=float(abs(mesh.volume-nominal)/nominal),vertices=len(mesh.vertices),triangles=len(mesh.faces),
  connected_components=components,euler_number=int(mesh.euler_number),checks=checks,passed=all(checks.values())))
out=dict(manifest_sha256=hashlib.sha256(raw).hexdigest(),saved_leg_version=19,
 scope='Read-only direct native 3MF stock reference validation. Three unique types, eight optional printed copies. No release preparation or authority change.',
 overall_passed=all(r['passed'] for r in rows),quantity_total=sum(r['quantity'] for r in rows),parts=rows,
 note='The native thigh-clamp sleeve is4.3mmID; the earlier generated bench hardware table specified4.4mmID. Both clear a nominalM4 shank, but the intended stock specification must be reconciled before publishing a single BOM. Printed sleeves are finger-tight surrogates, not load-qualified metal stock.')
(HERE/'stock-sleeve-validation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
