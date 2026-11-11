"""Replace the rail pair with qualified native construction and linked reflection."""
import hashlib,json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
assert json.loads((ROOT/'audits/frame-rail-family-edit-restore.json').read_text())['passed']
for side in ['right','left']:
 label='frame-intent-'+side+'-rail-restored';sha=hashlib.sha256((ROOT/'exports'/f'{label}.step').read_bytes()).hexdigest()
 for suffix,gate in [('geometry','geometric_gate_passed'),('sections','section_gate_passed')]:
  r=json.loads((ROOT/'audits'/f'{label}-{suffix}.json').read_text());assert r[gate] and r['native_step_sha256']==sha
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,tempfile,os,time

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');assert doc==app.activeDocument and doc.dataFile.versionNumber==13;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);before=[]
 # Delete the retired handed dependent before its former canonical source.
 for key in ['chassis_beam_102','chassis_beam_-102']:
  occ=next(o for o in root.occurrences if o.component.partNumber==key);before.append({'part':key,'features':occ.component.features.count,'sketches':occ.component.sketches.count});assert occ.deleteMe()
 after=[];paths=[]
 for key,side in [('chassis_beam_102','right'),('chassis_beam_-102','left')]:
  occ=next(o for o in root.occurrences if o.component.partNumber=='CANDIDATE_'+key);c=occ.component;c.partNumber=key;occ.isLightBulbOn=True;c.attributes.add('Tinfox','ConstructionQuality','Shared frame and shoulder dimensions; patterned attachment profiles and native linked reflection. Three frame/deck edit-restores and frozen boundary/section comparisons pass.');c.attributes.add('Tinfox','ManufacturingRelease','False');after.append({'part':key,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count});path=os.path.join(tempfile.gettempdir(),'tinfox-native','frame-intent-'+side+'-rail-final.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>10000;paths.append(path)
 removed=[]
 while True:
  eligible=[p for p in d.userParameters if p.name.startswith('chassis_beam_') and p.isDeletable]
  if not eligible:break
  for p in eligible:removed.append(p.name);assert p.deleteMe()
 assert d.computeAll();assert not any(c.partNumber.startswith('CANDIDATE_') for c in d.allComponents)
 for c in d.allComponents:
  issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,(c.name,issues)
 assert doc.save('Replace the motor rails with a 36-feature canonical rail and three-feature linked reflection. Shared hip spacing, frame width and fastener clearance move both rails and paired brace/deck attachments; three edit/restore cases pass. Frozen boundaries and sections match within 0.001 mm. Remaining tie, cassette and reference-placement bindings are separate work. Generated CAD remains authoritative.');print(json.dumps({'save_requested':True,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'before':before,'after':after,'removed_unused_parameters':removed,'paths':paths,'capacity':capacity,'source_of_truth':False}))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'frame-rail-native-checkpoint',timeout=240);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/frame-rail-native-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k not in ['capacity','removed_unused_parameters']},flush=True)
for p in record['paths']:fetch(p,Path(p).name)
