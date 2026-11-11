"""Identify the functional solids needed for an equivalent V0 nose construction."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];MODEL=ROOT.parent
sys.path.insert(0,str(MODEL))
import cadquery as cq
import build as b
from body_caps import shoulder_sweep
source=cq.importers.importStep(str(ROOT/'snapshots/step/body_nose_surround.step')).val()
old=cq.importers.importStep(str(b.OUT/'step-parts/body_nose_surround.step')).val()
outer=b.torso();end_region=b.box(70,280,150,(276,0,0));lap_region=b.box(26,50,20,(127,0,45))
end=outer.cut(b.torso(4.2)).intersect(end_region)
wires=[]
for x,w,h,zc in [(126,48,10,44),(142,44,30,49),(165,44,38,49),(195,44,38,49),(220,44,32,47),(242,80,12,43)]:
 q=cq.Workplane('YZ',origin=(x,0,zc)).rect(w,h).val();wires.append(q.fillet2D(2,q.Vertices()))
bridge=cq.Solid.makeLoft(wires,ruled=False).cut(b.box(20,100,100,(118,0,-7.2)))
chin=b.box(12,220,12,(247,0,-39)).intersect(outer)
base=end.fuse(bridge,chin)
old_end=old.intersect(end_region);old_lap=old.intersect(lap_region)
extra_end=old_end.cut(base);extra_lap=old_lap.cut(base)
for key,shape in [('base',base),('old_end_extra',extra_end),('old_lap_extra',extra_lap)]:
 cq.exporters.export(shape,str(ROOT/f'exports/nose-analysis-{key}.step'))
 print(key,shape.Volume(),len(shape.Solids()),flush=True)
# These source solids are only diagnostic references, not native authoring inputs.
record={'base_volume':base.Volume(),'old_end_additional_volume':extra_end.Volume(),'old_lap_additional_volume':extra_lap.Volume(),'note':'Local analysis only. No neutral geometry may be imported to author the native part.'}
(ROOT/'audits/nose-functional-decomposition.json').write_text(json.dumps(record,indent=2))
# Reconstruct retained V0 features without the obsolete parent cap history.
roof=b.box(6,50,2.8,(129,0,48.1));lap=b.box(26,48,3.5,(127,0,44.55),.5)
s=base.fuse(roof,lap)
# An exact face-equation sweep in Fusion replaces this local reference loft.
wires=[]
for z in __import__('numpy').linspace(-53,57,19):
 points=[(b.face_x(float(y),float(z))-2.1,float(y)) for y in __import__('numpy').linspace(-110,110,13)]
 wires.append(cq.Workplane('XY',origin=(0,0,float(z))).moveTo(230,-110).lineTo(*points[0]).spline(points[1:],includeCurrent=True).lineTo(230,110).close().val())
face=cq.Solid.makeLoft(wires,ruled=False)
for y in [-89,89]:
 for z in [-27,27]:
  tab=b.box(3.8,17,3.2,(240.8,94 if y>0 else -94,z),.6).intersect(outer).intersect(end_region)
  post=b.cyl(3.5,30,(239,y,z),(1,0,0)).intersect(face).intersect(end_region)
  s=s.fuse(tab,post)
for side in [-1,1]:s=s.cut(shoulder_sweep(1,side))
s=s.cut(cq.Workplane('YZ',origin=(226,0,4)).rect(168,44).extrude(36).edges('|X').fillet(8).val())
for y in [-18,18]:s=s.cut(b.cyl(1.7,16,(121,y,35),(0,0,1))).cut(cq.Solid.makeCone(1.7,3,1.3,cq.Vector(121,y,45),cq.Vector(0,0,1)))
for y in [-89,89]:
 for z in [-27,27]:s=s.cut(b.cyl(1.25,30,(238.5,y,z),(1,0,0)))
fascia=cq.importers.importStep(str(ROOT/'snapshots/step/front_fascia.step')).val();s=s.cut(fascia).cut(fascia.translate((-.35,0,0))).clean()
cq.exporters.export(s,str(ROOT/'exports/nose-functional-reconstruction.step'))
removed=source.cut(s);added=s.cut(source)
record.update(reconstructed_volume=s.Volume(),source_volume=source.Volume(),removed_volume=removed.Volume(),added_volume=added.Volume(),source_faces=len(source.Faces()),reconstructed_faces=len(s.Faces()))
(ROOT/'audits/nose-functional-decomposition.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)
