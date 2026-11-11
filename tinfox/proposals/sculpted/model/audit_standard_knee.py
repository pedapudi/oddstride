"""Check M5-retained axle fit, washer contacts and straight service paths."""
import hashlib,json,math
import cadquery as cq
from kinematics import ROOT
import build as b
OUT=ROOT/'output/paired-roll-work';rows=[]
def load(k):return cq.importers.importStep(str(OUT/'step'/(k+'.step'))).val()
def overlap(a,c):return max(0,sum(s.Volume() for s in a.intersect(c).Solids()))
def fit(label,a,c):
    v=overlap(a,c);rows.append(dict(check=label,overlap_mm3=v,passed=v<.005))
def contact(label,a,c,dy):
    v=overlap(a,c.translate((0,dy,0)))
    rows.append(dict(check=label,probe_travel_mm=abs(dy),contact_area_mm2=v/abs(dy),passed=v>.05))
inner,outer=load('thigh_inner'),load('thigh_outer')
p={k:load(k) for k in ['knee_axle','axle_bolt','axle_nut','axle_washer_inner','axle_washer_outer']}
for key,s in p.items():
    fit(key+' / inner shell',s,inner);fit(key+' / outer shell',s,outer)
contact('Inner washer / structural floor',inner,p['axle_washer_inner'],.05)
contact('Outer washer / structural floor',outer,p['axle_washer_outer'],-.05)
contact('Inner washer / axle end',p['knee_axle'],p['axle_washer_inner'],.05)
contact('Outer washer / axle end',p['knee_axle'],p['axle_washer_outer'],-.05)
contact('Bolt head / inner washer',p['axle_washer_inner'],p['axle_bolt'],.05)
contact('Nut / outer washer',p['axle_washer_outer'],p['axle_nut'],-.05)
host=cq.Compound.makeCompound([inner,outer,p['knee_axle']])
for travel in [0,.1,.5,1,2,5,10,20,40,70]:
    fit('Bolt inward removal '+str(travel),host,p['axle_bolt'].translate((0,-travel,0)))
    fit('Inner washer removal '+str(travel),inner,p['axle_washer_inner'].translate((0,-travel,0)))
    fit('Outer washer removal '+str(travel),outer,p['axle_washer_outer'].translate((0,travel,0)))
fit('Inner hex driver',inner,b.cyl(2.5,26,(0,19.45,-170)))
fit('Outer nut socket envelope',outer,b.cyl(6.5,25,(0,95.2,-170)))
report=dict(model_sha256=hashlib.sha256((OUT/'model.json').read_bytes()).hexdigest(),checks=rows,
    passed=all(r['passed'] for r in rows),
    axle_bending_inertia_ratio=(12**4-5.5**4)/(12**4-8.4**4),
    nominal_nut_thread_engagement_mm=4,nominal_thread_projection_mm=4.0,
    scope='Nominal solid fit, washer bearing areas and sampled removal paths. M5 retains the 12 mm steel axle. A thicker axle section does not qualify the bolt preload, printed bearing stress, tolerance stack, fatigue or loaded operation.')
(OUT/'knee-retention.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'checks':len(rows),'passed':report['passed'],'failed':[r for r in rows if not r['passed']]}),flush=True)
