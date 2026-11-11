"""Compare nominal material sections; this is not a strength calculation."""
import hashlib,json
import cadquery as cq
from integrated_candidate import ROOT,OUT,box
before=ROOT/'output/integrated-before-flow'
rows=[]
for name,stations in [('thigh_inner',[-120,-130,-140,-150]),('thigh_outer',[-120,-130,-140,-150]),('body_nose_surround',[130,140,170,190,220])]:
    old=cq.importers.importStep(str(before/'step'/(name+'.step'))).val()
    new=cq.importers.importStep(str(OUT/'step'/(name+'.step'))).val()
    for station in stations:
        slab=box(200,200,.2,(0,69,station)) if 'thigh' in name else box(.2,300,300,(station,0,0))
        rows.append({'part':name,'axis':'z' if 'thigh' in name else 'x','station_mm':station,
                     'previous_area_mm2':old.intersect(slab).Volume()/.2,'revised_area_mm2':new.intersect(slab).Volume()/.2})
(OUT/'section-comparison.json').write_text(json.dumps({'previous_model_sha256':hashlib.sha256((before/'model.json').read_bytes()).hexdigest(),'model_sha256':hashlib.sha256((OUT/'model.json').read_bytes()).hexdigest(),'slab_thickness_mm':.2,'sections':rows,'scope':'Average material area over thin slices. Does not establish bending stiffness, stress concentration, printed anisotropy, creep or fatigue.'},indent=2))
print('Section comparison written',flush=True)
