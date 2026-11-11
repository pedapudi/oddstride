import cadquery as cq,hashlib,json,math
from pathlib import Path
R=Path('/home/sunil/git/oddstride/tinfox/proposals/sculpted/model/fusion_native/exports/dfma-architecture-v1');O=Path(__file__).parent
expected={'primary':'4909ffed568ad0c16231410bef115b43e2a75f46fa3a0b864efa4630eb42e59d','secondary':'17a865404a3570e2123cea4799e7528f7f818d52388e8f654395b3a277e1ce23'}
shapes={};inputs={}
for k,h in expected.items():
 p=R/f'dfma-thigh-{k}-detailed.step';got=hashlib.sha256(p.read_bytes()).hexdigest();assert got==h;shapes[k]=cq.importers.importStep(str(p)).val();inputs[str(p)]={'sha256':got,'valid':shapes[k].isValid(),'solid_count':len(shapes[k].Solids())}
checks=[]
# Only the former thin shelf region, at the same noncoincident Z plane used in the finding.
for k,s in shapes.items():
 sec=s.intersect(cq.Face.makePlane(300,300,(0,0,-42),(0,0,1)))
 faces=[]
 for f in sec.Faces():
  b=f.BoundingBox();faces.append({'area_mm2':f.Area(),'bounds_mm':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]})
 # Restrict attention to the old inboard shelf below Y47.
 probe=cq.Solid.makeBox(30,38,1,cq.Vector(.01,9,-42.5));overlap=s.intersect(probe)
 checks.append({'name':k+'_former_positive_x_inboard_shelf','section_z_mm':-42,'section_faces':faces,'probe_positive_x_volume_mm3':overlap.Volume(),'passed':abs(overlap.Volume())<1e-6 if k=='primary' else len(faces)==1,'acceptance': 'Primary split remains atX0' if k=='primary' else 'Former isolated tapered shelf is joined to the continuous secondary section'})
# Detect actual cut-end edge Y from three radial sections through the300-degree column.
s=shapes['secondary'];d=cq.Vector(.5,0,-math.sqrt(3)/2);n=cq.Vector(math.sqrt(3)/2,0,.5)
for t in [-4,0,4]:
 sec=s.intersect(cq.Face.makePlane(500,500,n.multiply(t),n));edges=[]
 for f in sec.Faces():
  for e in f.Edges():
   pts,_=e.sample(24);ys=[p.y for p in pts];rs=[p.dot(d)for p in pts]
   if max(ys)-min(ys)<1e-6 and 43<ys[0]<50 and max(rs)>42 and min(rs)<45:edges.append({'y_mm':ys[0],'radial_extent_mm':[min(rs),max(rs)]})
 found=[e for e in edges if abs(e['y_mm']-46.5)<1e-6]
 checks.append({'name':'window_end_radial_section','tangential_offset_mm':t,'horizontal_edges':edges,'window_end_y_mm':46.5 if found else None,'tube_foot_y_mm':50.4,'band_mm':3.9 if found else None,'passed':bool(found)})
r={'scope':'Two corrected local details only; native motion/insertion/driver matrices not repeated','inputs':inputs,'checks':checks,'passed':all(c['passed']for c in checks)and all(v['valid']and v['solid_count']==1 for v in inputs.values()),'excluded_diagnostic':{'path':'diagnostic-overstrict-secondary-probe.json','reason':'Initial secondary probe incorrectly required absence of the positiveX barrel; the intended change reallocates the continuous barrel to the secondary and removes the isolated tapered shelf, rather than deleting this barrel.'},'limitations':['Local geometric detailing accepted; print orientation/supports, preload, physical cable bend and operating strength remain unqualified.']};p=O/'final-detail-delta.json';p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));print('REPORT_SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
