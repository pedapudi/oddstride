"""Save a clean, reviewable bench assembly without claiming authority prematurely."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
from motor_complex_exports import COMPONENTS
ROOT=Path(__file__).resolve().parents[1];palette=json.loads((ROOT.parents[3]/'design/appearance.json').read_text())
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''\nimport adsk.core as core,adsk.fusion as fusion,json,os,tempfile,time

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);bench=next(o for o in root.occurrences if o.component.partNumber=='BENCH_MOTOR_COMPLEX');assert [o for o in root.occurrences if o.isLightBulbOn]==[bench];library=app.materialLibraries.itemById('BA5EE55E-9982-449B-9D66-9F036540E140');template=library.appearances.itemByName('Plastic - Matte (White)');colors={}
 for role,hexcolor in COLORS.items():
  name='Tinfox '+role;appearance=d.appearances.itemByName(name)or d.appearances.addByCopy(template,name);rgb=tuple(int(hexcolor[i:i+2],16)for i in[1,3,5])
  for key in ['opaque_albedo','surface_albedo']:
   prop=core.ColorProperty.cast(appearance.appearanceProperties.itemById(key))
   if prop:prop.value=core.Color.create(*rgb,255)
  colors[role]=appearance
 rows=[]
 for c in d.allComponents:
  key=REVERSE.get(c.partNumber);ref=c.attributes.itemByName('Tinfox','BenchReferenceRole');role=None
  if key:role='fox'if key in['thigh_outer','input_crank']else'ivory'if key=='thigh_inner'else'metal'if key.startswith('roll_inner')or key=='roll_outer_spacer_1'else'charcoal'
  elif ref:role='accent'if ref.value in['connector_plug','connector_boot']else'charcoal'if ref.value.startswith(('vendor_','connector_'))else'metal'
  elif c.partNumber.startswith('CANDIDATE_bt_'):role='metal'
  if role:
   for body in c.bRepBodies:body.appearance=colors[role]
   c.attributes.add('Tinfox','AppearanceRole',role)
  if key:
   assert c.bRepBodies.count==1 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);rows.append({'part':key,'component':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'bodies':1})
 assert len(rows)==13;bench.component.attributes.add('Tinfox','PublicationScope','Detached unpowered three-RS02 motor complex; native authority pending final edits, saved reopen and surface-export checks.');root.attributes.add('Tinfox','VisibleReviewScope','Current motor complex only. Hidden prior robot and construction dependencies are retained; Master is not yet refreshed.');camera=app.activeViewport.camera;camera.eye=core.Point3D.create(24,32,18);camera.target=core.Point3D.create(-3,0,-7);camera.upVector=core.Vector3D.create(0,0,1);camera.isSmoothTransition=False;app.activeViewport.camera=camera;app.activeViewport.fit();app.activeViewport.refresh();path=os.path.join(tempfile.gettempdir(),'tinfox-native','motor-complex-native-work.png');assert app.activeViewport.saveAsImageFile(path,1800,1200);before=doc.dataFile.versionNumber;assert doc.save('Checkpoint the complete native 13-part paired-6810 motor complex, independent purchased references, shared fit parameters and clean bench view. Source shape and staged-assembly checks pass; final family/reopen/export gates remain pending. No full-robot authority change.');print(json.dumps({'previous_version':before,'version_at_return':doc.dataFile.versionNumber,'save_requested':True,'complete_at_return':doc.dataFile.isComplete,'modified_at_return':doc.isModified,'parts':rows,'capacity':capacity,'screenshot':path,'source_of_truth':False}))
'''.replace('KNOWN',repr(known_files())).replace('COLORS',repr(palette['colors'])).replace('REVERSE',repr({v[0]:k for k,v in COMPONENTS.items()}))
compile(s,'checkpoint_motor_complex_work.py','exec');r=rpc(s,'motor-complex-work-checkpoint',timeout=240);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/motor-complex-work-checkpoint.json').write_text(json.dumps(record,indent=2));print(record)
