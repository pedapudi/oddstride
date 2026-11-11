"""Replace the transverse tie pair with qualified native construction and linked reflection."""
import hashlib,json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
assert json.loads((ROOT/'audits/frame-tie-family-edit-restore.json').read_text())['passed']
for side in ['front','rear']:
 label='frame-intent-'+side+'-tie-restored';sha=hashlib.sha256((ROOT/'exports'/f'{label}.step').read_bytes()).hexdigest()
 for suffix,gate in [('geometry','geometric_gate_passed'),('sections','section_gate_passed')]:
  r=json.loads((ROOT/'audits'/f'{label}-{suffix}.json').read_text());assert r[gate] and r['native_step_sha256']==sha
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,tempfile,os,time

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');assert doc==app.activeDocument and doc.dataFile.versionNumber==14;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);before=[]
 # Delete the retired handed dependent before its former canonical source.
 for key in ['chassis_crossmember_-121','chassis_crossmember_121']:
  occ=next(o for o in root.occurrences if o.component.partNumber==key);before.append({'part':key,'features':occ.component.features.count,'sketches':occ.component.sketches.count});assert occ.deleteMe()
 after=[];paths=[]
 for key,side in [('chassis_crossmember_121','front'),('chassis_crossmember_-121','rear')]:
  occ=next(o for o in root.occurrences if o.component.partNumber=='CANDIDATE_'+key);c=occ.component;c.partNumber=key;occ.isLightBulbOn=True;c.attributes.add('Tinfox','ConstructionQuality','Shared frame and shoulder dimensions; native four-position countersink Hole feature, front sensor variant and linked rear reflection. Three frame/deck edit-restores and frozen boundary/section comparisons pass.');c.attributes.add('Tinfox','ManufacturingRelease','False');after.append({'part':key,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count});path=os.path.join(tempfile.gettempdir(),'tinfox-native','frame-intent-'+side+'-tie-final.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>10000;paths.append(path)
 removed=[]
 diagnostic=d.userParameters.itemByName('frame_tie_countersink_depth')
 if diagnostic is not None and diagnostic.isDeletable:removed.append(diagnostic.name);assert diagnostic.deleteMe()
 while True:
  eligible=[p for p in d.userParameters if p.name.startswith('chassis_crossmember_') and p.isDeletable]
  if not eligible:break
  for p in eligible:removed.append(p.name);assert p.deleteMe()
 assert d.computeAll();assert not any(c.partNumber.startswith('CANDIDATE_') for c in d.allComponents)
 for c in d.allComponents:
  issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,(c.name,issues)
 assert doc.save('Replace the transverse ties with a four-feature front tie and three-feature linked rear reflection. Shared hip spacing, frame width and fastener clearance move both ties with the rail pattern; three edit/restore cases pass. Frozen boundaries and sections match within 0.001 mm. Remaining cassette and reference-placement bindings are separate work. Generated CAD remains authoritative.');print(json.dumps({'save_requested':True,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'before':before,'after':after,'removed_unused_parameters':removed,'paths':paths,'capacity':capacity,'source_of_truth':False}))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'frame-tie-native-checkpoint',timeout=240);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/frame-tie-native-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k not in ['capacity','removed_unused_parameters']},flush=True)
for p in record['paths']:fetch(p,Path(p).name)
