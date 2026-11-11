"""Stage the corrected native closure assembly without releasing manufacturing files."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
assert json.loads((ROOT/'audits/recessed-closure-family-edit-restore.json').read_text())['passed']
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;bench=next(o for o in root.occurrences if o.component.partNumber=='BENCH_MOTOR_COMPLEX');holder=next(o for o in root.occurrences if o.component.partNumber=='BENCH_PURCHASED_LIBRARY');tick=time.monotonic();retired=[];parents=[]
 for key in ['hip_stator_closure_1','motor_carrier_1']:
  old=next(o for o in bench.component.occurrences if o.component.partNumber=='CANDIDATE_pr_'+key);part=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_rc_'+key);matrix=old.transform2;assert abs(matrix.translation.x*10+5)<1e-7;new=bench.component.occurrences.addExistingComponent(part,matrix);new.isGroundToParent=True;new.attributes.add('Tinfox','BenchPart',key);retired.append({'part':old.component.partNumber,'action':'Superseded active occurrence removed; native construction parent retained hidden.'});assert old.deleteMe()
 leaves=[]
 def collect(c):
  for o in c.occurrences:
   a=o.component.attributes.itemByName('Tinfox','BenchReferenceName')
   if a and a.value.startswith(('FL_carrier_closure_bolt_','FL_carrier_closure_washer_')):leaves.append((c,o,a.value))
   else:collect(o.component)
 collect(holder.component);assert len(leaves)==6
 for parent,old,name in leaves:
  oldnumber=old.component.partNumber
  if '_bolt_'in name:
   # The new parametric reference copies depend on this original vendor body.
   keep=root.occurrences.addExistingComponent(old.component,core.Matrix3D.create());keep.isLightBulbOn=False;keep.attributes.add('Tinfox','RetentionReason','Native copy parent for the recessed standard button. Not an active assembly instance.');parents.append(oldnumber);angle=name.rsplit('_',1)[1];part=next(c for c in d.allComponents if c.partNumber=='BENCH_REFERENCE_RECESSED_CLOSURE_'+angle);new=parent.occurrences.addExistingComponent(part,old.transform2);new.isLightBulbOn=True
  retired.append({'reference':name,'part_number':oldnumber,'action':'Removed superseded active button occurrence'if'_bolt_'in name else'Removed separate closure washer; the standard button now bears on its recessed floor.'});assert old.deleteMe()
 for o in root.occurrences:o.isLightBulbOn=o==bench
 visible=[];roles=[];numbers=[]
 def inspect(o):
  o.isLightBulbOn=True;c=o.component
  for b in c.bRepBodies:
   b.isLightBulbOn=True;assert b.createForAssemblyContext(o).isVisible;visible.append(o.fullPathName+' / '+b.name);numbers.append(c.partNumber);a=c.attributes.itemByName('Tinfox','BenchReferenceRole');roles.append(a.value if a else'custom_or_stock')
  for child in c.occurrences:inspect(child.createForAssemblyContext(o))
 inspect(bench);assert len(visible)==121;assert roles.count('vendor_motor')==3 and sum(r.startswith('connector_')for r in roles)==24;assert sum(n.startswith('BENCH_REFERENCE_RECESSED_CLOSURE_')for n in numbers)==3;assert not any('carrier_closure_washer_'in n for n in numbers);bench.component.name='Motor complex - reinforced closure candidate';bench.component.attributes.add('Tinfox','AssemblyReleaseReady','false');app.activeViewport.fit();print(json.dumps({'saved_version':doc.dataFile.versionNumber,'working_modified':doc.isModified,'candidate_only':True,'retired_active_occurrences':retired,'retained_hidden_reference_parents':parents,'assembly_inventory':{'custom_parts':13,'cut_stock_bodies':8,'purchased_references':100,'motors':3,'connector_bodies':24,'total_visible_bodies':121},'elapsed_seconds':time.monotonic()-tick,'scope':'Working revision only. Exact assembled pair classification and saved export gates remain pending.'}))
'''
compile(s,'activate_recessed_closure.py','exec');r=rpc(s,'recessed-closure-bench-activation',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/recessed-closure-bench-activation.json').write_text(json.dumps(record,indent=2));print(record)
