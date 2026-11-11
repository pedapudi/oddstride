"""Retain native histories while localizing qualified subsystem components."""
import hashlib,json,sys
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
role=sys.argv[1]
settings={'leg':{'localize':['foot','shin_inner','thigh_outer'],'replace':['shin_outer']},'chassis':{'localize':['battery_cassette'],'replace':['body_center_0']},'head':{'localize':[],'replace':[]}}[role]
if len(sys.argv)>2:settings={'localize':[],'replace':sys.argv[2:]}
manifest=json.loads((ROOT/'manifests/subsystems.json').read_text());subsystem=manifest['subsystems'][role]
registry=json.loads((ROOT/'manifests/native-files.json').read_text())
local=ROOT/'manifests/local-native-archives.json'
if local.exists():registry.update(json.loads(local.read_text()))
replacements={key:{field:registry[key][field] for field in ['feature_count','sketches','body_count','volume_mm3']} for key in settings['replace']}
for key in replacements:
 for gate in ['geometry','sections']:
  assert json.loads((ROOT/'audits'/f'{key}-{gate}.json').read_text())['geometric_gate_passed' if gate=='geometry' else 'section_gate_passed'],(key,gate)
 replacements[key]['archive_sha256']=hashlib.sha256((ROOT/'exports'/f'{key}.f3d').read_bytes()).hexdigest()
script=script_header()+'''import adsk,adsk.core as core,adsk.fusion as fusion,json,os,tempfile,time,hashlib

def run(_context: str):
 app=core.Application.get();master=next(d for d in app.documents if d.name.startswith('Tinfox - Native Master Assembly'));assert not master.isModified
 require_personal_capacity(app,master,KNOWN,new_cloud_files=0,reserve_slots=1)
 file=app.data.findFileById(FILE_ID);doc=next((d for d in app.documents if d.isSaved and d.dataFile.id==FILE_ID),None)
 if doc is None:doc=app.documents.open(file,True)
 else:doc.activate()
 d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert not doc.isModified,'Reconcile unsaved subsystem changes before continuing'
 assert not file.isReadOnly,'Subsystem is read-only'
 def inventory(c):
  return {'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'volume_mm3':sum(b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume for b in c.bRepBodies)*1000,'base_features':sum('BaseFeature' in f.objectType for f in c.features),'mesh_bodies':c.meshBodies.count}
 def find(key):return [o for o in root.occurrences if o.component.partNumber==key]
 changes=[]
 for key in LOCALIZE:
  occurrences=find(key);assert len(occurrences)==1,(key,len(occurrences));o=occurrences[0]
  if not o.isReferencedComponent:continue
  before=inventory(o.component);assert o.breakLink();after=inventory(o.component)
  for field in ['features','sketches','bodies','base_features','mesh_bodies']:assert before[field]==after[field],(key,field,before,after)
  assert not o.isReferencedComponent and abs(before['volume_mm3']-after['volume_mm3'])<.001,(key,before,after)
  changes.append({'part':key,'operation':'localized_native_history','before':before,'after':after,'passed':True})
 for key,expected in REPLACEMENTS.items():
  occurrences=find(key);assert len(occurrences)<=1,(key,len(occurrences));old=occurrences[0] if occurrences else None
  if old is not None and not old.isReferencedComponent and old.component.sketches.count==expected['sketches']:continue
  path=os.path.join(tempfile.gettempdir(),'tinfox-native',key+'.f3d');assert hashlib.sha256(open(path,'rb').read()).hexdigest()==expected['archive_sha256']
  old_token=old.entityToken if old is not None else None;result=app.importManager.importToTarget2(app.importManager.createFusionArchiveImportOptions(path),root);assert result is not None
  candidates=[o for o in find(key) if o.entityToken!=old_token];assert len(candidates)==1,(key,len(candidates));new=candidates[0];c=new.component;after=inventory(c)
  for field,expected_field in [('features','feature_count'),('sketches','sketches'),('bodies','body_count')]:assert after[field]==expected[expected_field],(key,field,expected,after)
  assert not new.isReferencedComponent and after['base_features']==0 and after['mesh_bodies']==0
  assert abs(after['volume_mm3']-expected['volume_mm3'])<.001,(key,expected,after)
  issues=[f.name+': '+f.errorOrWarningMessage for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,(key,issues)
  before=inventory(old.component) if old is not None else None
  if old is not None:assert old.deleteMe()
  changes.append({'part':key,'operation':'merged_qualified_native_archive','before':before,'after':after,'archive_sha256':expected['archive_sha256'],'passed':True})
 d.computeAll()
 touched=set(LOCALIZE)|set(REPLACEMENTS)
 issues={o.component.partNumber:[f.name+': '+f.errorOrWarningMessage for f in o.component.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState] for o in root.occurrences if o.component.partNumber in touched};assert not any(issues.values()),issues
 version=doc.dataFile.versionNumber
 if changes:
  assert doc.save('Consolidate editable native histories into the '+ROLE+' subsystem; migration audit remains open.')
  deadline=time.monotonic()+90
  while (doc.isModified or doc.dataFile.versionNumber<=version or not doc.dataFile.isComplete) and time.monotonic()<deadline:adsk.doEvents();time.sleep(.1)
  assert not doc.isModified and doc.dataFile.versionNumber>version and doc.dataFile.isComplete,'Save incomplete; inspect before retry'
 assert not master.isModified
 print(json.dumps({'role':ROLE,'file_id':FILE_ID,'version':doc.dataFile.versionNumber,'changes':changes,'native_parts':len(list(root.occurrences)),'remaining_external_parts':[o.component.partNumber for o in root.occurrences if o.isReferencedComponent],'inventory':{o.component.partNumber:inventory(o.component) for o in root.occurrences},'source_master_modified':master.isModified,'phase':'qualified_histories_internalized','migration_gate_passed':False}))
'''
for token,value in [('FILE_ID',subsystem['file_id']),('LOCALIZE',settings['localize']),('REPLACEMENTS',replacements),('ROLE',role),('KNOWN',known_files())]:script=script.replace(token,repr(value))
response=rpc(script,role+'-subsystem-consolidate',timeout=300);assert response[0].get('success'),response
record=json.loads(response[0]['message']);(ROOT/'audits'/f'{role}-subsystem-consolidate.json').write_text(json.dumps(record,indent=2));manifest=json.loads((ROOT/'manifests/subsystems.json').read_text());manifest['subsystems'][role].update(version=record['version'],phase=record['phase'],consolidation=record);(ROOT/'manifests/subsystems.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({k:record[k] for k in ['role','file_id','version','remaining_external_parts','native_parts']},indent=2))
