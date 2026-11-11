"""Check native shin hardware interfaces, bearing extraction and shell removal."""
import json,math,sys
from pathlib import Path
from functools import cache
import cadquery as cq
from audit_part import volume
ROOT=Path(__file__).resolve().parents[1];MODEL=ROOT.parent;sys.path.insert(0,str(MODEL));import build as b
REF=ROOT/'snapshots/cohesive-limb';refs={}
@cache
def solid(key):
 if key in ['shin_inner','shin_outer']:
  path=ROOT/'exports'/('cohesive-'+key.replace('_','-')+'-final.step')
  if not path.exists():path=ROOT/'exports'/('cohesive-'+key.replace('_','-')+'.step')
 elif key.startswith('rod_bush_output_'):
  angle=math.radians(-78);return b.rod_bush(-170,key.endswith('_1')).translate((28*math.cos(angle),-16,-28*math.sin(angle)+170))
 else:
  paths=[REF/'step'/f'{key}.step']+[MODEL/f'output/{folder}/step/{key}.step' for folder in ['integrated-candidate','v0-rounded-body','service-design']]+[MODEL/'output/step-parts'/f'{key}.step'];path=next(p for p in paths if p.exists())
 import hashlib
 refs[key]={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()};shape=cq.importers.importStep(str(path)).val();assert shape.isValid() and len(shape.Solids())==1;return shape
rows=[]
def fit(label,a,c):
 error=max(0,volume(a.intersect(c))[0]);rows.append({'check':label,'overlap_mm3':error,'passed':error<.001})
fit('Two structural halves',solid('shin_inner'),solid('shin_outer'))
for side in ['inner','outer']:
 shin=solid('shin_'+side);direction=-1 if side=='inner' else 1
 for key in ['bearing_inner','bearing_outer','shin_clamp_bolt_37','shin_clamp_bolt_105','shin_clamp_nut_37','shin_clamp_nut_105','shin_clamp_sleeve_37','shin_clamp_sleeve_105','output_pin','output_pivot_nut','rod_bush_output_0','rod_bush_output_1']:fit(side+' / '+key,shin,solid(key))
 for travel in [0,.1,.5,1,2,4,8,12,20,35]:fit(side+' bearing extraction '+str(travel),shin,solid('bearing_'+side).translate((0,direction*travel,0)))
 for x in [-12.7,12.7]:fit(side+' extraction punch '+str(x),shin,b.cyl(1,16,(x,61,0)))
 for travel in [.1,1,5,15,40,70]:fit(side+' shell separation '+str(travel),shin.translate((0,direction*travel,0)),solid('shin_outer' if side=='inner' else 'shin_inner'))
record={'checks':rows,'passed':all(r['passed'] for r in rows),'references':refs,'source_snapshot':'snapshots/cohesive-limb/reference.json','scope':'Native shin halves and unchanged exact hardware. Nominal fits and sampled bearing/shell withdrawal only; does not qualify material strength, interference-fit tolerances or loaded motion.'};(ROOT/'audits/cohesive-shin-service.json').write_text(json.dumps(record,indent=2));print(json.dumps({'passed':record['passed'],'checks':len(rows),'failed':[r for r in rows if not r['passed']]}))
