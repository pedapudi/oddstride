"""Save the validated bench and inventory retained history without removing dependencies."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
from motor_complex_exports import COMPONENTS
ROOT=Path(__file__).resolve().parents[1]
for name in ['motor-complex-family-edits.json','motor-complex-native-critical-interfaces.json','motor-complex-effective-visibility.json']:
 assert json.loads((ROOT/'audits'/name).read_text())['passed'],name
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,hashlib,time

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);bench=next(o for o in root.occurrences if o.component.partNumber=='BENCH_MOTOR_COMPLEX');reverse={v:k for k,v in PARTS.items()};assert [o for o in root.occurrences if o.isLightBulbOn]==[bench];rows=[];visible=[]
 def walk(occ):
  for b in occ.component.bRepBodies:
   proxy=b.createForAssemblyContext(occ);assert proxy.isVisible;visible.append({'path':occ.fullPathName,'body':b.name})
  for child in occ.component.occurrences:walk(child.createForAssemblyContext(occ))
 walk(bench);assert len(visible)==124
 for o in root.occurrences:
  c=o.component;key=reverse.get(c.partNumber)
  if key:category='Published bench native definition; root occurrence hidden, shared bench occurrence current';c.attributes.add('Tinfox','CanonicalGeometryScope','Detached 13-part motor complex; saved native feature history. Full robot is not promoted.');c.attributes.add('Tinfox','CanonicalPartKey',key)
  elif c.partNumber=='BENCH_MOTOR_COMPLEX':category='Current visible static assembly'
  elif c.partNumber in ['CANDIDATE_sl_thigh_outer','CANDIDATE_sl_thigh_master']:category='Retained native construction dependency of corrected thigh'
  elif c.partNumber=='BENCH_PURCHASED_LIBRARY':category='Shared purchased-reference parent; current child occurrence is inside bench'
  elif c.partNumber.startswith('CANDIDATE_bt_'):category='Native cut-stock family; active bench instances and deferred full-limb variants'
  elif c.partNumber.startswith('ASSEMBLY_'):category='Retired visible robot assembly; hidden with obsolete motion joints suppressed'
  elif c.partNumber.startswith('CANDIDATE_'):category='Hidden migration/deferred family; dependency removal not proven, conservatively retained'
  else:category='Hidden baseline or native construction; conservatively retained'
  rows.append({'part_number':c.partNumber,'name':c.name,'root_visible':o.isLightBulbOn,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'unhealthy_features':[{'name':f.name,'message':f.errorOrWarningMessage}for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState],'classification':category})
 bench.component.attributes.add('Tinfox','PublicationScope','Native detached motor complex: 13 custom parts, 3 motors, independently hideable connectors. Static assembly only. Final saved reopen and direct-export validation are recorded in the external authority manifest.');root.attributes.add('Tinfox','AuthorityScope','Only the explicitly published 13-part bench scope can become native-canonical. Hidden older robot assemblies and Master are migration references.');folder=os.path.join(tempfile.gettempdir(),'tinfox-native','motor-complex-native');path=os.path.join(folder,'assembled-motor-complex.3mf');opts=d.exportManager.createC3MFExportOptions(bench,path);opts.sendToPrintUtility=False;opts.surfaceDeviation=.001;opts.normalDeviation=.03;assert d.exportManager.execute(opts);assert os.path.getsize(path)>1000000;assembly={'path':path,'sha256':hashlib.sha256(open(path,'rb').read()).hexdigest(),'bytes':os.path.getsize(path)};before=doc.dataFile.versionNumber;assert doc.save('Save the clean native 13-part motor complex and independent purchased hardware. Source surfaces, 748 staged assembly checks, 28 native solid interfaces, actual placements and six parameter edits/restores pass. Historical robot assemblies remain hidden; full robot authority and loaded strength are not claimed.');print(json.dumps({'save_requested':True,'previous_version':before,'version_at_return':doc.dataFile.versionNumber,'complete_at_return':doc.dataFile.isComplete,'modified_at_return':doc.isModified,'capacity':capacity,'visible_body_count':len(visible),'root_inventory':rows,'deleted_documents':0,'deleted_components':0,'retired_solver_report':'audits/retired-leg-solver-cleanup.json','assembly_3mf':assembly,'native_source_of_truth':False}))
'''.replace('KNOWN',repr(known_files())).replace('PARTS',repr({k:v[0]for k,v in COMPONENTS.items()}))
r=rpc(s,'motor-complex-final-checkpoint',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/motor-complex-final-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k not in['root_inventory','capacity']})
