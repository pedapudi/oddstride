"""Replace only the retired knee plate and nine socket references in the active bench."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
assert json.loads((ROOT/'audits/knee-seat-family-edit-restore.json').read_text())['passed']
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;bench=next(o for o in root.occurrences if o.component.partNumber=='BENCH_MOTOR_COMPLEX');holder=next(o for o in root.occurrences if o.component.partNumber=='BENCH_PURCHASED_LIBRARY');tick=time.monotonic();retired=[];replacements=[]
 oldplate=next(o for o in bench.component.occurrences if o.component.partNumber=='CANDIDATE_sl_motor_mount_ring');matrix=oldplate.transform2;assert max(abs(v-w)for v,w in zip(matrix.asArray(),core.Matrix3D.create().asArray()))<1e-8;part=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_ks_motor_mount_ring');new=bench.component.occurrences.addExistingComponent(part,matrix);new.isGroundToParent=True;new.isLightBulbOn=True;part.bRepBodies.item(0).isLightBulbOn=True;new.attributes.add('Tinfox','BenchPart','motor_mount_ring');retired.append({'path':oldplate.fullPathName,'part_number':oldplate.component.partNumber,'action':'Removed superseded active occurrence; original native construction and saved Leg20 retained.'});assert oldplate.deleteMe()
 leaves=[]
 def walk(c):
  for o in c.occurrences:
   a=o.component.attributes.itemByName('Tinfox','BenchReferenceName')
   if a and a.value.startswith('Knee stator M3x8 '):leaves.append((c,o,a.value))
   else:walk(o.component)
 walk(holder.component);assert len(leaves)==9
 for parent,old,name in leaves:
  angle=int(name.rsplit(' ',1)[1]);part=next(c for c in d.allComponents if c.partNumber=='BENCH_REFERENCE_KNEE_DIN7991_'+str(angle));m=old.transform2;assert max(abs(v-w)for v,w in zip(m.asArray(),core.Matrix3D.create().asArray()))<1e-8;new=parent.occurrences.addExistingComponent(part,m);new.isLightBulbOn=True;part.bRepBodies.item(0).isLightBulbOn=True;retired.append({'path':old.fullPathName,'part_number':old.component.partNumber,'action':'Removed obsolete socket-head active occurrence; historical Leg20 and original reference snapshot retained.'});assert old.deleteMe();replacements.append({'name':name,'part_number':part.partNumber,'specification':'M3 x 8 DIN7991, nominal 5.9 mm 90 degree head'})
 for o in root.occurrences:o.isLightBulbOn=o==bench
 visible=[];roles=[];numbers=[]
 def inspect(o):
  o.isLightBulbOn=True;c=o.component
  for b in c.bRepBodies:
   b.isLightBulbOn=True;proxy=b.createForAssemblyContext(o);assert proxy.isVisible,(o.fullPathName,b.name);visible.append(o.fullPathName+' / '+b.name);numbers.append(c.partNumber);a=c.attributes.itemByName('Tinfox','BenchReferenceRole');roles.append(a.value if a else'custom_or_stock')
  for child in c.occurrences:
   inspect(child.createForAssemblyContext(o))
 inspect(bench);assert len(visible)==124;assert roles.count('vendor_motor')==3;assert sum(r.startswith('connector_')for r in roles)==24;assert numbers.count('CANDIDATE_ks_motor_mount_ring')==1;assert 'CANDIDATE_sl_motor_mount_ring'not in numbers;assert sum(n.startswith('BENCH_REFERENCE_KNEE_DIN7991_')for n in numbers)==9
 bench.component.name='Motor complex - seated knee revision candidate';app.activeViewport.fit();print(json.dumps({'saved_version':doc.dataFile.versionNumber,'working_modified':doc.isModified,'candidate_only':True,'retired_active_occurrences':retired,'replacement_hardware':replacements,'visible_bodies':len(visible),'motors':3,'independent_connector_bodies':24,'elapsed_seconds':time.monotonic()-tick,'authority':'Canonical exported Leg20 remains unchanged until this revision passes saved-state and export gates.'}))
'''
r=rpc(s,'knee-seated-bench-activation',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/knee-seated-bench-activation.json').write_text(json.dumps(record,indent=2));print(record)
