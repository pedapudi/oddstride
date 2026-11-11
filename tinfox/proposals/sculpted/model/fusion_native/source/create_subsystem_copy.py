"""Copy an existing native component group into one subsystem document.

The source master is retained unchanged. All native child feature inventories and
volumes must survive the copy before the document enters the subsystem manifest.
"""
import json,sys
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
ROLES={'leg':('Shared leg designs','Tinfox - Leg module'),'chassis':('Body and chassis','Tinfox - Chassis'),'head':('Electronics and sensors','Tinfox - Head')}
role=sys.argv[1];source_group,name=ROLES[role]
script=script_header()+'''import adsk,adsk.core as core,adsk.fusion as fusion,json,time

def run(_context: str):
 app=core.Application.get();master=next(d for d in app.documents if d.name.startswith('Tinfox - Native Master Assembly'));master.activate();master_design=fusion.Design.cast(app.activeProduct);assert not master.isModified,'Preserve the saved source master'
 source=next(o.component for o in master_design.rootComponent.occurrences if o.component.name==SOURCE_GROUP)
 def inventory(component):
  rows={}
  for occurrence in component.occurrences:
   c=occurrence.component
   rows[c.partNumber]={'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'volume_mm3':sum(b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume for b in c.bRepBodies)*1000,'linked':occurrence.isReferencedComponent}
  return rows
 before=inventory(source)
 project=master.dataFile.parentProject;folder=next((f for f in project.rootFolder.dataFolders if f.name=='05 Native subsystems'),None)
 if folder is None:folder=project.rootFolder.dataFolders.add('05 Native subsystems')
 existing=next((f for f in folder.dataFiles if f.name==NAME),None)
 capacity=require_personal_capacity(app,master,KNOWN,new_cloud_files=0 if existing else 1,reserve_slots=1)
 if existing:file=existing
 else:
  future=source.saveCopyAs(NAME,folder,'Native subsystem consolidation candidate. Source master and migration baseline are preserved.','');deadline=time.monotonic()+60
  while future.dataFile is None and time.monotonic()<deadline:adsk.doEvents();time.sleep(.1)
  file=future.dataFile;assert file is not None,'Upload pending; inspect before retry'
 document=next((doc for doc in app.documents if doc.isSaved and doc.dataFile.id==file.id),None)
 if document is None:document=app.documents.open(file,True)
 else:document.activate()
 design=fusion.Design.cast(app.activeProduct);after=inventory(design.rootComponent)
 assert set(before)==set(after),('Part inventory changed',set(before)^set(after))
 for key,expected in before.items():
  actual=after[key]
  for field in ['features','sketches','bodies']:assert actual[field]==expected[field],(key,field,expected[field],actual[field])
  assert abs(actual['volume_mm3']-expected['volume_mm3'])<max(.001,abs(expected['volume_mm3'])*1e-8),(key,'volume',expected['volume_mm3'],actual['volume_mm3'])
 assert not master.isModified
 print(json.dumps({'role':ROLE,'name':file.name,'file_id':file.id,'version':file.versionNumber,'source_master_file_id':master.dataFile.id,'source_master_version':master.dataFile.versionNumber,'source_group':SOURCE_GROUP,'phase':'native_group_copy_verified','before':before,'after':after,'capacity':capacity,'source_master_modified':master.isModified,'consolidation_complete':False,'migration_gate_passed':False}))
'''
for token,value in [('SOURCE_GROUP',source_group),('KNOWN',known_files()),('NAME',name),('ROLE',role)]:script=script.replace(token,repr(value))
response=rpc(script,role+'-subsystem-copy',timeout=180);assert response[0].get('success'),response
record=json.loads(response[0]['message']);path=ROOT/'manifests/subsystems.json';data=json.loads(path.read_text()) if path.exists() else {'schema':1,'migration_gate_passed':False,'subsystems':{}};data['subsystems'][role]=record;path.write_text(json.dumps(data,indent=2));(ROOT/'audits'/f'{role}-subsystem-copy.json').write_text(json.dumps(record,indent=2));print(json.dumps({'role':role,'file_id':record['file_id'],'version':record['version'],'native_parts':len(record['after']),'phase':record['phase']},indent=2))
