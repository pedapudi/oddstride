"""Current sensor hood geometry, sections and absolute-mesh silhouette comparisons."""
import json,hashlib,sys
from pathlib import Path
import numpy as np
import cadquery as cq
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import union_all
from audit_part import audit
from audit_sections import audit as sections
from metrology_mesh import absolute_tessellate
ROOT=Path(__file__).resolve().parents[1]
target=next(p for p in json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low']['custom_parts'] if p['key']=='front_fascia');reference={'id':'current_front_fascia','source_step':target['files']['step']['path'],'source_reference_note':'Frozen current low-profile robot target 929c06ab624ed80192157e99ce43165c1416db414902cb0a36c19d6d2ad50da6; native hood uses eight guided profiles and the shared compound face.'};label=sys.argv[1] if len(sys.argv)>1 else 'current-sensor-hood-native';prefix='current-sensor-hood' if label=='current-sensor-hood-native' else label
audit('current_front_fascia',label,reference);sections('current_front_fascia',label,reference)
paths=[ROOT/reference['source_step'],ROOT/'exports'/f'{label}.step'];meshes=[]
for path in paths:
 s=cq.importers.importStep(str(path)).val();v,f=absolute_tessellate(s,.01,.04);meshes.append((np.asarray([p.toTuple() for p in v]),np.asarray(f)))
views={'side':np.array([[1,0,0],[0,0,1]]),'front':np.array([[0,1,0],[0,0,1]]),'top':np.array([[1,0,0],[0,1,0]]),'isometric':np.array([[.7071067811865475,-.7071067811865475,0],[.408248290463863,.408248290463863,.816496580927726]])};rows=[];svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800"><rect width="1200" height="800" fill="#faf9f5"/><text x="20" y="28" font-family="sans-serif" font-size="18">Current sensor hood: frozen source teal / native Fusion orange</text>']
for index,(name,projection) in enumerate(views.items()):
 silhouettes=[];healing=[]
 for vertices,faces in meshes:
  uv=vertices@projection.T;polygons=[]
  for tri in faces:
   points=uv[tri];area=abs((points[1,0]-points[0,0])*(points[2,1]-points[0,1])-(points[1,1]-points[0,1])*(points[2,0]-points[0,0]))
   if area>1e-8:polygons.append(Polygon(points))
  shape=union_all(polygons,grid_size=1e-6);closed=shape.buffer(1e-5,join_style=2).buffer(-1e-5,join_style=2);healing_area=shape.symmetric_difference(closed).area;assert healing_area<1e-3,healing_area;healing.append({'pre_close_components':len(shape.geoms) if shape.geom_type=='MultiPolygon' else 1,'post_close_components':len(closed.geoms) if closed.geom_type=='MultiPolygon' else 1,'changed_area_mm2':healing_area});components=list(closed.geoms) if closed.geom_type=='MultiPolygon' else [closed];silhouettes.append(unary_union([Polygon(p.exterior) for p in components if p.area>1e-5]))
 a,b=silhouettes;delta=a.symmetric_difference(b).area/a.area;distance=a.boundary.hausdorff_distance(b.boundary);rows.append({'view':name,'boundary_hausdorff_mm':distance,'relative_symmetric_difference_area':delta,'mesh_seam_healing':healing,'passed':distance<.05 and delta<.001});xmin,ymin,xmax,ymax=a.bounds;scale=min(540/(xmax-xmin),300/(ymax-ymin));ox=(index%2)*600+25;oy=(index//2)*380+360;svg.append(f'<text x="{ox}" y="{oy-300}" font-family="sans-serif" font-size="15">{name}: {distance:.5f} mm</text>')
 for shape,color in zip(silhouettes,['#007f87','#e65a27']):
  polys=list(shape.geoms) if shape.geom_type=='MultiPolygon' else [shape]
  for poly in polys:
   coords=[(ox+(x-xmin)*scale,oy-(y-ymin)*scale) for x,y in poly.exterior.coords];svg.append('<polyline fill="none" stroke="'+color+'" stroke-width=".65" points="'+' '.join(f'{x:.4f},{y:.4f}' for x,y in coords)+'"/>')
svg.append('</svg>');(ROOT/'audits'/f'{prefix}-silhouettes.svg').write_text(''.join(svg));record={'passed':all(r['passed'] for r in rows),'views':rows,'source_sha256':hashlib.sha256(paths[0].read_bytes()).hexdigest(),'native_sha256':hashlib.sha256(paths[1].read_bytes()).hexdigest(),'mesh_seam_close_radius_mm':1e-5,'projection_union_precision_mm':1e-6,'absolute_deflection_mm':.01,'angular_deflection_rad':.04,'scope':'External projected boundaries from absolute-deflection meshes; internal openings are checked by sections and exact surfaces.'};(ROOT/'audits'/f'{prefix}-silhouettes.json').write_text(json.dumps(record,indent=2));print(record)
