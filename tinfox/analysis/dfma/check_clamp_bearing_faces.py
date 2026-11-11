"""Measure material beneath the modeled clamp head/nut footprints."""
from pathlib import Path
import sys,json,hashlib,math
import cadquery as cq
ROOT=Path(__file__).resolve().parents[2]/'proposals/sculpted/model';sys.path.insert(0,str(ROOT));import build as b
OUT=ROOT/'output/closed-thigh-work';inventory=json.loads((Path(__file__).resolve().parent/'inventory.json').read_text());rows=[]
def read(k):
 for folder in [Path(__file__).resolve().parent/'input-step',OUT/'step',ROOT/'output/limb-refinement/step',ROOT/'output/integrated-candidate/step',ROOT/'output/service-design/step',ROOT/'output/step-parts']:
  p=folder/(k+'.step')
  if p.exists():return cq.importers.importStep(str(p)).val()
 raise FileNotFoundError(k)
def volume(s):return sum(x.Volume() for x in s.Solids())
clamps=[('thigh',0,-36,-66,'bolt_0','thigh_clamp_nut_0','sleeve_0'),('thigh',1,5,-70,'bolt_1','thigh_clamp_nut_1','sleeve_1'),
 ('shin',37,2,-30,'shin_clamp_bolt_37','shin_clamp_nut_37','shin_clamp_sleeve_37'),('shin',105,2,-105,'shin_clamp_bolt_105','shin_clamp_nut_105','shin_clamp_sleeve_105')]
for family,i,x,z,bolt_key,nut_key,sleeve_key in clamps:
 inner,outer=read(family+'_inner'),read(family+'_outer');bolt=read(bolt_key);nut=read(nut_key);sleeve=read(sleeve_key)
 for label,s in [('bolt',bolt),('nut',nut),('sleeve',sleeve)]:
  bb=s.BoundingBox();print(i,label,[bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.zmin,bb.zmax])
 # Move bearing faces 0.1 mm into the receiving structural shell. A real
 # seat would intercept a positive footprint volume immediately.
 head=bolt.intersect(b.box(30,8,30,(x,55,z)))
 head_probe=head.translate((0,.1,0));nut_probe=nut.translate((0,-.1,0))
 rows.append({'family':family,'clamp':i,'center_xz_mm':[x,z],
  'head_inner_shell_overlap_after_0_1mm_inward_mm3':volume(inner.intersect(head_probe)),
  'nut_outer_shell_overlap_after_0_1mm_inward_mm3':volume(outer.intersect(nut_probe)),
  'nominal_head_diameter_mm':7.6,'sleeve_od_mm':8,'seat_clearance_bore_mm':8.2,
  'nut_across_flats_mm':7,'nut_maximum_diameter_mm':7/math.cos(math.pi/6)})
report={'model_sha256':inventory['model_sha256'],'checks':rows,'scope':'Exact-solid footprint/intersection check only, using frozen input STEP files. Does not simulate preload or material deformation. Zero engagement with a receiving face means this nominal stack does not demonstrate axial clamping of the shells.'}
p=Path(__file__).resolve().parent/'clamp-bearing-faces.json';p.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
