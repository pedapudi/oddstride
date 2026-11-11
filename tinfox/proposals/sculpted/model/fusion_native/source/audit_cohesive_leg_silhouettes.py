"""Overlay projected frozen and native limb silhouettes without altering geometry."""
import json
from pathlib import Path
import numpy as np
import cadquery as cq
from metrology_mesh import absolute_tessellate
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely.ops import unary_union,nearest_points
from shapely import union_all
from shapely.geometry import Point
ROOT=Path(__file__).resolve().parents[1];labels={kind+'_'+side:'cohesive-'+kind+'-'+side+'-final' for kind in ['thigh','shin'] for side in ['inner','outer']}
mesh={}
for native in [False,True]:
 for key,label in labels.items():
  p=ROOT/'exports'/f'{label}.step' if native else ROOT/'snapshots/cohesive-limb/step'/f'{key}.step';s=cq.importers.importStep(str(p)).val();v,f=absolute_tessellate(s,.005,.025);vertices=np.array([p.toTuple() for p in v])
  if key.startswith('shin_'):
   angle=np.deg2rad(-100);rotation=np.array([[np.cos(angle),0,np.sin(angle)],[0,1,0],[-np.sin(angle),0,np.cos(angle)]]);vertices=vertices@rotation.T+np.array([0,0,-170])
  mesh[native,key]=(vertices,np.array(f))
views={'side':np.array([[1,0,0],[0,0,1]]),'front':np.array([[0,1,0],[0,0,1]]),'isometric':np.array([[.70710678,-.70710678,0],[.40824829,.40824829,.81649658]])};rows=[];figure,axes=plt.subplots(1,3,figsize=(15,4));svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 340"><rect width="1200" height="340" fill="#faf9f5"/><text x="15" y="22" font-family="sans-serif" font-size="16">shin native fidelity — frozen cohesive reference teal, native orange</text>']
for index,(view,projection) in enumerate(views.items()):
 shapes=[]
 for native in [False,True]:
  polygons=[]
  for key in labels:
   v,f=mesh[native,key];uv=v@projection.T
   polygons.extend(Polygon(uv[tri]) for tri in f if abs(np.linalg.det(np.array([uv[tri[1]]-uv[tri[0]],uv[tri[2]]-uv[tri[0]]])))>1e-9)
  projected=union_all(polygons,grid_size=0.000001);components=list(projected.geoms) if projected.geom_type=='MultiPolygon' else [projected]
  shapes.append(unary_union([Polygon(poly.exterior) for poly in components if poly.area>1e-5]))
 a,b=shapes;diff=a.symmetric_difference(b);haus=a.boundary.hausdorff_distance(b.boundary);worst=[]
 for direction,one,two in [('source_to_native',a,b),('native_to_source',b,a)]:
  lines=list(one.boundary.geoms) if hasattr(one.boundary,'geoms') else [one.boundary];points=[Point(p) for line in lines for p in line.coords];q=max(points,key=lambda p:two.boundary.distance(p));near=nearest_points(q,two.boundary)[1];worst.append({'direction':direction,'point':list(q.coords)[0],'nearest':list(near.coords)[0],'distance_mm':q.distance(near)})
 row={'worst_vertices':worst,'view':view,'source_area_mm2':a.area,'native_area_mm2':b.area,'symmetric_difference_area_mm2':diff.area,'relative_difference_area':diff.area/a.area,'boundary_hausdorff_mm':haus,'pass':haus<.05 and diff.area/a.area<.001};rows.append(row)
 lo=np.array(a.bounds[:2]);hi=np.array(a.bounds[2:]);scale=min(350/(hi[0]-lo[0]),230/(hi[1]-lo[1]));svg.append(f'<text x="{index*400+15}" y="52" font-family="sans-serif" font-size="13">{view}: {haus:.4f} mm</text>')
 for shape,color in zip(shapes,['#007f87','#e65a27']):
  polygons=list(shape.geoms) if shape.geom_type=='MultiPolygon' else [shape]
  for poly in polygons:
   for ring in [poly.exterior,*poly.interiors]:
    axes[index].plot(*ring.xy,color=color,lw=.5)
    xy=[(index*400+20+(x-lo[0])*scale,300-(y-lo[1])*scale) for x,y in ring.coords];svg.append('<polyline fill="none" stroke="'+color+'" stroke-width="0.65" points="'+' '.join(f'{x:.3f},{y:.3f}' for x,y in xy)+'"/>')
for ax,title in zip(axes,views):ax.set_aspect('equal');ax.set_title(title);ax.axis('off')
figure.suptitle('Native limb external silhouettes: frozen cohesive reference teal / native orange');figure.tight_layout();figure.savefig(ROOT/'audits/cohesive-leg-silhouettes.png',dpi=150);plt.close(figure)
svg.append('</svg>');(ROOT/'audits/cohesive-leg-silhouettes.svg').write_text(''.join(svg));record={'views':rows,'passed':all(r['pass'] for r in rows),'projection_union_grid_mm':0.000001,'scope':'External projected silhouettes at 0.005 mm absolute source/native tessellation; excludes projected internal holes and disconnected triangulation fragments smaller than 0.00001 mm2. Internal features are audited by exact BRep surfaces and sections.'};(ROOT/'audits/cohesive-leg-silhouettes.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
try:
 import cairosvg
 cairosvg.svg2png(url=str(ROOT/'audits/cohesive-leg-silhouettes.svg'),write_to=str(ROOT/'audits/cohesive-leg-silhouettes.png'),output_width=1800)
except ImportError:pass
