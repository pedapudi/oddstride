"""Overlay projected frozen and native Head silhouettes without altering geometry."""
import json
from pathlib import Path
import numpy as np
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1];labels={'body_nose_surround':'body_nose_surround-tangent','front_fascia':'front_fascia-intent','sensor_bezel':'sensor_bezel-intent'}
mesh={}
for native in [False,True]:
 for key,label in labels.items():
  p=ROOT/'exports'/f'{label}.step' if native else ROOT/'snapshots/step'/f'{key}.step';s=cq.importers.importStep(str(p)).val();v,f=s.tessellate(.01,.04);mesh[native,key]=(np.array([p.toTuple() for p in v]),np.array(f))
views={'side':np.array([[1,0,0],[0,0,1]]),'front':np.array([[0,1,0],[0,0,1]]),'isometric':np.array([[.70710678,-.70710678,0],[.40824829,.40824829,.81649658]])};rows=[];figure,axes=plt.subplots(1,3,figsize=(15,4));svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 340"><rect width="1200" height="340" fill="#faf9f5"/><text x="15" y="22" font-family="sans-serif" font-size="16">Head native fidelity — frozen V0 teal, native orange</text>']
for index,(view,projection) in enumerate(views.items()):
 shapes=[]
 for native in [False,True]:
  polygons=[]
  for key in labels:
   v,f=mesh[native,key];uv=v@projection.T
   polygons.extend(Polygon(uv[tri]) for tri in f if abs(np.linalg.det(np.array([uv[tri[1]]-uv[tri[0]],uv[tri[2]]-uv[tri[0]]])))>1e-9)
  projected=unary_union(polygons);components=list(projected.geoms) if projected.geom_type=='MultiPolygon' else [projected]
  shapes.append(unary_union([Polygon(poly.exterior) for poly in components if poly.area>1e-5]))
 a,b=shapes;diff=a.symmetric_difference(b);haus=a.boundary.hausdorff_distance(b.boundary);row={'view':view,'source_area_mm2':a.area,'native_area_mm2':b.area,'symmetric_difference_area_mm2':diff.area,'relative_difference_area':diff.area/a.area,'boundary_hausdorff_mm':haus,'pass':haus<.05 and diff.area/a.area<.001};rows.append(row)
 lo=np.array(a.bounds[:2]);hi=np.array(a.bounds[2:]);scale=min(350/(hi[0]-lo[0]),230/(hi[1]-lo[1]));svg.append(f'<text x="{index*400+15}" y="52" font-family="sans-serif" font-size="13">{view}: {haus:.4f} mm</text>')
 for shape,color in zip(shapes,['#007f87','#e65a27']):
  polygons=list(shape.geoms) if shape.geom_type=='MultiPolygon' else [shape]
  for poly in polygons:
   for ring in [poly.exterior,*poly.interiors]:
    axes[index].plot(*ring.xy,color=color,lw=.5)
    xy=[(index*400+20+(x-lo[0])*scale,300-(y-lo[1])*scale) for x,y in ring.coords];svg.append('<polyline fill="none" stroke="'+color+'" stroke-width="0.65" points="'+' '.join(f'{x:.3f},{y:.3f}' for x,y in xy)+'"/>')
for ax,title in zip(axes,views):ax.set_aspect('equal');ax.set_title(title);ax.axis('off')
figure.suptitle('Head external silhouettes: frozen V0 teal / native orange');figure.tight_layout();figure.savefig(ROOT/'audits/head-silhouettes.png',dpi=150);plt.close(figure)
svg.append('</svg>');(ROOT/'audits/head-silhouettes.svg').write_text(''.join(svg));record={'views':rows,'passed':all(r['pass'] for r in rows),'scope':'External projected silhouettes at 0.01 mm source/native tessellation; excludes projected internal holes and disconnected triangulation fragments smaller than 0.00001 mm2. Internal features are audited by exact BRep surfaces and sections.'};(ROOT/'audits/head-silhouettes.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
try:
 import cairosvg
 cairosvg.svg2png(url=str(ROOT/'audits/head-silhouettes.svg'),write_to=str(ROOT/'audits/head-silhouettes.png'),output_width=1800)
except ImportError:pass
