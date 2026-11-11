"""Place a static native bench with creation-time transforms and shared references."""
import json
from pathlib import Path
from run_native import rpc
from motor_complex_exports import COMPONENTS
ROOT=Path(__file__).resolve().parents[1];hardware=json.loads((ROOT/'manifests/motor-complex-hardware.json').read_text());roles={p['name']:p['role']for p in hardware['parts']}
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;tick=time.monotonic();assert not any(c.partNumber=='BENCH_MOTOR_COMPLEX'for c in d.allComponents);library={key:next(c for c in d.allComponents if c.partNumber==number)for key,number in PARTS.items()};before={key:(c.features.count,c.sketches.count,c.bRepBodies.count)for key,c in library.items()};bench=root.occurrences.addNewComponent(core.Matrix3D.create());bench.component.name='Motor complex - paired 6810 bench assembly';bench.component.partNumber='BENCH_MOTOR_COMPLEX';bench.isGrounded=True;c=bench.component;rows=[]
 def place(part,x):
  matrix=core.Matrix3D.create();matrix.translation=core.Vector3D.create(x/10,0,0);o=c.occurrences.addExistingComponent(part,matrix);o.isGroundToParent=True
  # Assert the first translated occurrence before building the rest of the graph.
  actual=o.transform2.translation;proxy=o.createForAssemblyContext(bench);world=proxy.transform2.translation;assert abs(actual.x*10-x)<1e-7 and abs(world.x*10-x)<1e-7,(part.partNumber,x,list(o.transform2.asArray()),list(proxy.transform2.asArray()));return o
 keys=['roll_cartridge_1']+[key for key in library if key!='roll_cartridge_1']
 for key in keys:
  part=library[key];x=-5 if key.startswith(('roll_','motor_carrier','hip_stator_closure'))else 0;o=place(part,x);o.attributes.add('Tinfox','BenchPart',key);o.attributes.add('Tinfox','GeometryRole','Native custom part');o.attributes.add('Tinfox','PlacementScope','Static bench at the checked baseline. Motion and automatic assembly resizing are not claimed.');rows.append({'part':key,'path':o.createForAssemblyContext(bench).fullPathName,'expected_x_mm':x,'native_component':part.partNumber,'matrix':list(o.createForAssemblyContext(bench).transform2.asArray())})
 for key in ['pod_sleeve_90','pod_sleeve_210','pod_sleeve_330','sleeve_0','sleeve_1']:
  part=next(p for p in d.allComponents if p.partNumber=='CANDIDATE_bt_'+key);o=place(part,0);o.attributes.add('Tinfox','BenchCutStock',key)
 holder=next(o for o in root.occurrences if o.component.partNumber=='BENCH_PURCHASED_LIBRARY');leaves=[]
 def collect(component):
  if component.bRepBodies.count:leaves.append(component)
  for child in component.occurrences:collect(child.component)
 collect(holder.component);assert len(leaves)==103 and {p.attributes.itemByName('Tinfox','BenchReferenceName').value for p in leaves}==set(ROLES);refs=[]
 for part in leaves:
  name=part.attributes.itemByName('Tinfox','BenchReferenceName').value;assert part.bRepBodies.count==1;part.attributes.add('Tinfox','GeometryRole','Purchased reference only; not custom native authoring');part.attributes.add('Tinfox','BenchReferenceRole',ROLES[name]);part.bRepBodies.item(0).name=name;refs.append({'name':name,'role':ROLES[name],'body':part.bRepBodies.item(0).name})
 purchase=place(holder.component,0);purchase.attributes.add('Tinfox','GeometryRole','Separately hideable purchased references in checked baseline coordinates')
 if d.snapshots.hasPendingSnapshot:d.snapshots.add().name='Static motor-complex placement'
 assert d.computeAll()
 for row in rows:
  o=next(o for o in c.occurrences if o.attributes.itemByName('Tinfox','BenchPart')and o.attributes.itemByName('Tinfox','BenchPart').value==row['part']);m=list(o.createForAssemblyContext(bench).transform2.asArray());assert abs(m[3]*10-row['expected_x_mm'])<1e-7,(row,m);row['matrix']=m
 for key,part in library.items():assert before[key]==(part.features.count,part.sketches.count,part.bRepBodies.count),key
 visibility=[]
 for o in root.occurrences:
  old=o.isLightBulbOn;o.isLightBulbOn=o==bench;visibility.append({'name':o.name,'part_number':o.component.partNumber,'before':old,'after':o.isLightBulbOn})
 assert sum(r['role']=='vendor_motor'for r in refs)==3;assert sum(r['role'].startswith('connector_')for r in refs)==24
 app.activeViewport.fit();print(json.dumps({'saved':False,'custom_parts':rows,'cut_stock_components':5,'references':refs,'motors':3,'independent_connector_bodies':24,'root_visibility':visibility,'native_histories_unchanged':True,'joints':0,'static_placement':True,'elapsed_seconds':time.monotonic()-tick,'scope':'Detached bench. Shared purchased library reused once; old assemblies and required construction parents retained hidden. Master unchanged.'}))
'''.replace('PARTS',repr({k:v[0]for k,v in COMPONENTS.items()})).replace('ROLES',repr(roles))
compile(s,'motor_complex_native_assembly.py','exec');r=rpc(s,'motor-complex-native-assembly',timeout=900);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/motor-complex-native-assembly.json').write_text(json.dumps(record,indent=2));print({'saved':False,'parts':len(record['custom_parts']),'references':len(record['references']),'seconds':record['elapsed_seconds']})
