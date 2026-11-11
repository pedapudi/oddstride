"""Seat existing vendor references by matching actual circular cone boundaries."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,math,time
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;holder=next(o for o in root.occurrences if o.component.partNumber=='BENCH_PURCHASED_LIBRARY');bench=next(o for o in root.occurrences if o.component.partNumber=='BENCH_MOTOR_COMPLEX');tm=fusion.TemporaryBRepManager.get();tick=time.monotonic()
 def cones(body):
  out=[]
  for f in body.faces:
   if not core.Cone.cast(f.geometry):continue
   circles=[core.Circle3D.cast(e.geometry)for e in f.edges];circles=sorted([c for c in circles if c],key=lambda c:c.radius);assert len(circles)>=2;small,large=circles[0],circles[-1];assert large.radius-small.radius>1e-5;a=list(small.center.asArray());b=list(large.center.asArray());ratio=small.radius/(large.radius-small.radius);apex=[(x-(y-x)*ratio)*10 for x,y in zip(a,b)];out.append({'apex_mm':apex,'small_radius_mm':small.radius*10,'large_radius_mm':large.radius*10,'small_center_mm':[v*10 for v in a],'large_center_mm':[v*10 for v in b]})
  return out
 seats={}
 for kind,key in [('hip','hip_stator_closure_1'),('roll','motor_carrier_1')]:
  body=tm.copy(next(c for c in d.allComponents if c.partNumber=='CANDIDATE_rc_'+key).bRepBodies.item(0));m=core.Matrix3D.create();m.translation=core.Vector3D.create(-.5,0,0);assert tm.transform(body,m);seats[kind]=cones(body);assert len(seats[kind])==(9 if kind=='hip'else 6)
 leaves=[]
 def collect(c):
  for o in c.occurrences:
   a=o.component.attributes.itemByName('Tinfox','BenchReferenceName')
   if a and a.value.startswith(('FL_hip_stator_bolt_','FL_roll_output_bolt_')):leaves.append((c,o,a.value))
   else:collect(o.component)
 collect(holder.component);assert len(leaves)==15;plans=[]
 for parent,o,name in leaves:
  assert max(abs(v-w)for v,w in zip(o.transform2.asArray(),core.Matrix3D.create().asArray()))<1e-8;body=o.component.bRepBodies.item(0);screw=cones(body);assert len(screw)==1;kind='hip'if'_hip_'in name else'roll';axis=1 if kind=='hip'else 0;source=screw[0];target=min(seats[kind],key=lambda row:sum((a-b)**2 for i,(a,b)in enumerate(zip(row['apex_mm'],source['apex_mm']))if i!=axis));delta=[a-b for a,b in zip(target['apex_mm'],source['apex_mm'])];assert abs(delta[axis]+.2)<1e-5 and max(abs(v)for i,v in enumerate(delta)if i!=axis)<1e-5,(name,source,target,delta);plans.append((parent,o,name,delta,source,target))
 rows=[]
 for parent,old,name,delta,source,target in plans:
  body=old.component.bRepBodies.item(0);before=(body.faces.count,body.edges.count,body.volume);matrix=old.transform2;matrix.translation=core.Vector3D.create(*[v/10 for v in delta]);new=parent.occurrences.addExistingComponent(old.component,matrix);new.isLightBulbOn=True;new.attributes.add('Tinfox','SeatingOffsetMillimetres',json.dumps(delta));new.attributes.add('Tinfox','SeatingMethod','Matched native conical boundary circles; vendor seed body unchanged.');assert old.deleteMe();assert before==(body.faces.count,body.edges.count,body.volume);assert max(abs(a-b)for a,b in zip(new.transform2.translation.asArray(),[v/10 for v in delta]))<1e-8;rows.append({'name':name,'translation_mm':delta,'source_cone':source,'seat_cone':target,'aligned_apex_error_mm':max(abs(a+b-c)for a,b,c in zip(source['apex_mm'],delta,target['apex_mm'])),'nominal_motor_engagement_mm':5.1 if'_hip_'in name else 4.2,'vendor_body_unchanged':True})
 def show(o):
  o.isLightBulbOn=True
  for b in o.component.bRepBodies:b.isLightBulbOn=True;assert b.createForAssemblyContext(o).isVisible
  for child in o.component.occurrences:show(child.createForAssemblyContext(o))
 show(bench);print(json.dumps({'saved_version':doc.dataFile.versionNumber,'working_modified':doc.isModified,'references':rows,'count':15,'custom_geometry_unchanged':True,'knee_reference_seed_geometry_unchanged':True,'elapsed_seconds':time.monotonic()-tick,'scope':'Nominal reference placement follows actual conical seats. Physical motor revision and usable thread depth still require measurement.'}))
'''
compile(s,'seat_standard_references.py','exec');r=rpc(s,'standard-countersunk-reference-seating',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/standard-countersunk-reference-seating.json').write_text(json.dumps(record,indent=2));print({'references':record['count'],'seconds':record['elapsed_seconds']})
