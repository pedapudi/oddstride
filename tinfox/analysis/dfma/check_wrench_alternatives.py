"""Tool-only sensitivity study; virtual reliefs do not change published CAD."""
from pathlib import Path
import json, math, sys
import cadquery as cq
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]/'proposals/sculpted/model'
sys.path.insert(0,str(ROOT));import build as b
stamp='f265baac6868b9cede365abce32450c75e580291a0346ad451c05706031cd374'
F=HERE/'paired-prototype-input'/stamp
def read(k):return cq.importers.importStep(str(F/(k+'.step'))).val()
def vol(s):return max(0,sum(x.Volume() for x in s.Solids()))
rows=[]
for front in (1,-1):
 cup=read(f'motor_carrier_{front}');housing=read(f'roll_cartridge_{front}');retainer=read(f'roll_outer_retainer_{front}')
 relieved=cup
 for a in (90,215,325):
  cut=b.box(50,5.5,18,(64.7,-14.65,0)).rotate((0,0,0),(0,1,0),-a).translate((front*5,0,0))
  relieved=relieved.cut(cut)
 for handle_angle in (-15,15):
  head=b.cyl(8,3.8,(0,-15.8,0))
  handle=b.box(100,3.8,8,(55,-13.9,0)).rotate((0,0,0),(0,1,0),-handle_angle)
  mouth=b.box(20,6,7.1,(-5.8,-13.9,0))
  wrench=head.fuse(handle).cut(mouth)
  for a in (90,215,325):
   x,z=47*math.cos(math.radians(a)),47*math.sin(math.radians(a))
   tool=wrench.rotate((0,0,0),(0,1,0),-a).translate((front*5+x,0,z))
   for travel in (0,3,8,15,25):
    moved=tool.translate((travel*math.cos(math.radians(a)),0,travel*math.sin(math.radians(a))))
    checks={name:vol(moved.intersect(body)) for name,body in [('published_cup',cup),('virtual_relieved_cup',relieved),('housing',housing),('retainer',retainer)]}
    rows.append(dict(front=front,lug=a,handle_angle_deg=handle_angle,travel_mm=travel,overlap_mm3=checks))
out=dict(model_sha256=stamp,scope='Sensitivity only. Hypothetical radial slot begins39.7mm instead42.7mm; no CAD publication changed. Generic16mm head,7.1mm mouth,3.8mm thickness,100mm handle,±15degree handle angle. Results do not establish actual purchased tool or loaded strength.',rows=rows)
(HERE/'wrench-alternatives.json').write_text(json.dumps(out,indent=2)+'\n')
for front in (1,-1):
 for a in (90,215,325):
  for h in (-15,15):
   rr=[r for r in rows if r['front']==front and r['lug']==a and r['handle_angle_deg']==h]
   print(front,a,h,{k:round(max(r['overlap_mm3'][k] for r in rr),6) for k in rr[0]['overlap_mm3']},flush=True)
