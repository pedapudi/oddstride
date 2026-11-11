"""Refresh the broad-face bed orientation of non-leg printed parts."""
import json
import cadquery as cq
import trimesh
from kinematics import ROOT
for name in ['nose_panel','power_button','battery_cassette']:
 s=cq.importers.importStep(str(ROOT/'output/step-parts'/f'{name}.step')).val()
 if name=='nose_panel':s=s.rotate((0,0,0),(0,1,0),90)
 b=s.BoundingBox();s=s.translate((-(b.xmin+b.xmax)/2,-(b.ymin+b.ymax)/2,-b.zmin))
 path=ROOT/'output/print-stl'/f'{name}.stl';cq.exporters.export(s,str(path),tolerance=.15,angularTolerance=.15)
 m=trimesh.load_mesh(path);m.merge_vertices(digits_vertex=4);m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices();m.apply_translation([0,0,-m.bounds[0,2]]);m.export(path)
 print(name,m.extents.tolist(),flush=True)
f=ROOT/'output/print-manifest.json';rows=json.loads(f.read_text())
for row in rows:
 if row['part']=='nose_panel':row['orientation']='Broad YZ fascia face rotated around Y onto the XY bed; nominal thickness is 1.2 mm.'
 if row['part']=='power_button':row['orientation']='Button underside on XY bed; axis remains vertical.'
 if row['part']=='battery_cassette':row['orientation']='Cassette floor on XY bed, open pack cavity upward; slicer bridge/support review required.'
f.write_text(json.dumps(rows,indent=2))
