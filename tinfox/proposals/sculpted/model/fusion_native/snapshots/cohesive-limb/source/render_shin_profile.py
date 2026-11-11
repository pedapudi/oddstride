"""Project the actual previous and revised shin solids onto the sagittal plane."""
from pathlib import Path
import importlib.util,sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'.cache/profile-deps'))
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parent
old_path=ROOT.parent/'design/iterations/build-pass06.py'
spec=importlib.util.spec_from_file_location('previous_shin',old_path)
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
new_spec=importlib.util.spec_from_file_location('historical_shin',ROOT.parent/'design/iterations/build-pass07.py')
build=importlib.util.module_from_spec(new_spec);new_spec.loader.exec_module(build)

def silhouette(shape,color,opacity):
    verts,tris=shape.tessellate(.12,.08)
    triangles=[]
    for tri in tris:
        polygon=Polygon([(verts[i].x,verts[i].z) for i in tri])
        if polygon.area>1e-8:triangles.append(polygon)
    outline=unary_union(triangles).simplify(.03,preserve_topology=True)
    polygons=list(outline.geoms) if outline.geom_type=='MultiPolygon' else [outline]
    paths=[]
    for polygon in polygons:
        for ring in [polygon.exterior,*polygon.interiors]:
            coords=list(ring.coords)
            paths.append('M'+' L'.join(f'{280+x*3.6:.2f},{125-z*3.6:.2f}' for x,z in coords)+' Z')
    return f'<path d="{" ".join(paths)}" fill="{color}" fill-rule="evenodd" opacity="{opacity}"/>'

def line(stations,color):
    pts=' '.join(f'{280+x*3.6:.2f},{125-z*3.6:.2f}' for z,x in stations)
    return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.5" stroke-dasharray="6 4"/>'

svg=['<svg xmlns="http://www.w3.org/2000/svg" width="700" height="850" viewBox="0 0 700 850">',
'<rect width="700" height="850" fill="#f5f4ed"/>',
'<g font-family="sans-serif" fill="#28392f"><text x="30" y="38" font-size="24">Shin curvature / sagittal CAD projection</text>',
'<text x="30" y="67" font-size="15">Knee and foot centers retained. Positive X points toward the nose.</text></g>',
'<g transform="translate(0 40)">',
silhouette(old.shin_half().fuse(old.shin_half(True)),'#b5a99b',1),
silhouette(build.shin_half().fuse(build.shin_half(True)),'#38584e',.78),
'<path d="M280 125 V658" stroke="#dd6a31" stroke-width="1.5" stroke-dasharray="3 5"/>',
line([(-18,-1),(-34,-4),(-60,-8),(-92,-9),(-122,-5),(-148,0),(-159,0)],'#8c6d52'),
line([(-18,-1),(-34,4),(-60,12),(-89,13),(-112,6),(-130,1.5),(-136,0)],'#143e30'),
'<g stroke="#dd6a31" fill="#f5f4ed" stroke-width="2"><circle cx="280" cy="125" r="5"/><circle cx="280" cy="657.8" r="5"/></g>',
'<g font-family="sans-serif" font-size="16" fill="#28392f"><text x="380" y="130">Knee axis</text><text x="380" y="662">Foot center / 148 mm</text>',
'<text x="35" y="732" fill="#8c6d52">Previous: −9 mm middle offset</text><text x="35" y="758" fill="#143e30">Revised: +13 mm middle offset, shorter ankle overlap</text>',
'<text x="35" y="788" font-size="12">Filled paths: projected CAD triangle union, 0.03 mm simplification. Dashes: loft stations.</text></g></g></svg>']
(ROOT.parent/'design/13-shin-profile.svg').write_text('\n'.join(svg))
print(ROOT.parent/'design/13-shin-profile.svg')
