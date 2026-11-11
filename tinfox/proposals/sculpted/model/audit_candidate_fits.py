"""Exact nominal service and hardware fits for the closed-thigh candidate."""
import json,hashlib
import cadquery as cq
from integrated_candidate import OUT,source,ring,cyl

def solid(k):
 p=OUT/'step'/f'{k}.step'
 return cq.importers.importStep(str(p)).val() if p.exists() else source(k)
rows=[]
def overlap(name,a,b):
 v=max(0,a.intersect(b).Volume());rows.append({'name':name,'overlap_mm3':v,'passed':v<1e-4})
inner,outer=[solid('shin_'+k) for k in ['inner','outer']]
for label,s,direction in [('inner',inner,-1),('outer',outer,1)]:
 bearing=solid('bearing_'+label)
 probe=ring(14.8,14.2,1,77.5 if label=='outer' else 57.5)
 coverage=s.intersect(probe).Volume()/probe.Volume()
 rows.append({'name':label+' bearing seat continuity','wall_fraction':coverage,'passed':coverage>.999})
 for dist in [0,.1,.5,1,2,4,8,12,20,35]:
  overlap(label+' bearing extraction '+str(dist),bearing.translate((0,direction*dist,0)),s)
 for xx in [-12.7,12.7]:overlap(label+' extraction pin '+str(xx),cyl(1,3,(xx,71 if label=='outer' else 62,0)),s)
 for kind in ['bolt','nut','sleeve']:
  for tag in ['37','105']:overlap(label+' shin clamp '+kind+' '+tag,solid('shin_clamp_'+kind+'_'+tag),s)
 for name in ['output_pin','output_pivot_nut']:overlap(label+' '+name,solid(name),s)
 t=solid('thigh_'+label).translate((0,0,170))
 rows.append({'name':label+' bearing backup stop','gap_mm':t.distance(bearing),'passed':t.distance(bearing)>.25})
 for name in ['bolt_0','sleeve_0','thigh_clamp_nut_0']:overlap(label+' thigh rear clamp '+name,solid(name),solid('thigh_'+label))
for name in ['input_pin','input_pivot_nut']:
 overlap('input crank / '+name,solid('input_crank'),solid(name))
hood,cradle=solid('front_fascia'),solid('body_nose_surround')
overlap('camera hood / cradle',hood,cradle)
for component in ['body_center_0','chassis_crossmember_121','chassis_beam_102','chassis_beam_-102']:
 try:q=solid(component)
 except FileNotFoundError:continue
 for label,s in [('hood',hood),('cradle',cradle)]:overlap('camera '+label+' / '+component,s,q)
for y in [-16,16]:
 for kind in ['screw','nut']:
  for label,s in [('hood',hood),('cradle',cradle)]:overlap('camera '+label+' / '+kind+str(y),s,solid(f'camera_hood_{kind}_{y}'))
report={'model_sha256':hashlib.sha256((OUT/'model.json').read_bytes()).hexdigest(),'checks':rows,
 'scope':'Exact nominal solid intersections and sampled bearing extraction. Does not certify press-fit tolerance, fastener strength, thermal creep or tool access.'}
(OUT/'fit-audit.json').write_text(json.dumps(report,indent=2))
print('FIT CHECKS',len(rows),'FAILED',[r for r in rows if not r['passed']],flush=True)
