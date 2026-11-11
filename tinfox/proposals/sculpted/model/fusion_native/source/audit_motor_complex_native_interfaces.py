"""Check actual bench placements, separate vendor visibility and critical native interfaces."""
import json
from pathlib import Path
from run_native import rpc
from motor_complex_exports import COMPONENTS
ROOT=Path(__file__).resolve().parents[1];hardware=json.loads((ROOT/'manifests/motor-complex-hardware.json').read_text())
pairs=[['thigh_inner','thigh_outer'],['thigh_outer','motor_mount_ring'],['thigh_outer','Knee pitch motor'],['thigh_inner','hip_hub'],['thigh_outer','input_crank'],['motor_carrier_1','Hip pitch motor'],['hip_stator_closure_1','Hip pitch motor'],['motor_carrier_1','hip_stator_closure_1'],['roll_cartridge_1','roll_stator_backplate_1'],['roll_cartridge_1','motor_carrier_1'],['roll_cartridge_1','Roll motor']]
for bearing in ['FL_roll_bearing_6810_0','FL_roll_bearing_6810_1']:
 for part in ['roll_cartridge_1','motor_carrier_1','roll_inner_spacer_1','roll_outer_spacer_1']:pairs.append([part,bearing])
for angle in [90,210,330]:pairs.append(['thigh_outer','Pod M3x60 screw '+str(angle)])
for angle in range(0,360,60):pairs.append(['input_crank','Knee output M4x12 '+str(angle)])
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;bench=next(o for o in root.occurrences if o.component.partNumber=='BENCH_MOTOR_COMPLEX');objects={};tick=time.monotonic();rows=[];visible_bodies=[]
 def walk(occ):
  c=occ.component
  for b in c.bRepBodies:
   proxy=b.createForAssemblyContext(occ);assert proxy.isVisible,(occ.fullPathName,b.name);visible_bodies.append(occ.fullPathName+' / '+b.name)
  key=REVERSE.get(c.partNumber);ref=c.attributes.itemByName('Tinfox','BenchReferenceName')
  if key or ref:
   name=key if key else ref.value;assert name not in objects;assert c.bRepBodies.count==1;objects[name]=(occ,c.bRepBodies.item(0).createForAssemblyContext(occ))
  for child in c.occurrences:walk(child.createForAssemblyContext(occ))
 walk(bench);assert len(objects)==116,(len(objects),list(objects));assert len(visible_bodies)==124;placements=[]
 for ref in REFERENCES:
  occ,body=objects[ref['name']];bb=body.boundingBox;bounds=[v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]];error=max(abs(a-b)for a,b in zip(bounds,ref['bounds_mm']));assert error<.015,(ref['name'],bounds,ref['bounds_mm'],error);placements.append({'name':ref['name'],'max_bounds_error_mm':error,'native_path':occ.fullPathName,'independently_hideable':True})
 for pair in PAIRS:
  entities=core.ObjectCollection.create()
  for key in pair:entities.add(objects[key][1])
  inputs=d.createInterferenceInput(entities);inputs.areCoincidentFacesIncluded=False;started=time.monotonic();results=d.analyzeInterference(inputs);assert results is not None;volumes=[abs(r.interferenceBody.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume)*1000 for r in results];volume=sum(volumes);rows.append({'pair':pair,'volume_mm3':volume,'passed':volume<1e-5,'seconds':time.monotonic()-started})
 print(json.dumps({'passed':all(r['passed']for r in rows),'checkpoint_version':doc.dataFile.versionNumber,'working_modified':doc.isModified,'references':placements,'visible_bodies':len(visible_bodies),'checks':rows,'checker':'Native Fusion root-context body proxies; exact solid interference, coincident faces excluded','elapsed_seconds':time.monotonic()-tick,'scope':'Static detached motor complex. Does not establish loaded strength, continuous robot motion or universal CNC access.'}))
'''.replace('REFERENCES',repr(hardware['parts'])).replace('PAIRS',repr(pairs)).replace('REVERSE',repr({v[0]:k for k,v in COMPONENTS.items()}))
r=rpc(s,'motor-complex-native-critical-interfaces',timeout=600,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/motor-complex-native-critical-interfaces.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'checks':len(record['checks']),'failed':[x for x in record['checks']if not x['passed']]})
