"""Publish verified native feature history and replace a stale linked draft.

F3D archives here were exported from our native sketch/feature builds. Opening
one preserves its editable history; this never imports a mesh or a STEP solid.
Superseded cloud drafts are retained in the validation folder with explicit names.
"""
import json,sys
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1];key=sys.argv[1]
registry=json.loads((ROOT/'manifests/native-files.json').read_text());record=registry[key]
script=script_header()+'''import adsk,adsk.core as core,adsk.fusion as fusion,json,os,tempfile,time

def run(_context: str):
 app=core.Application.get();master=next(d for d in app.documents if d.name.startswith('Tinfox - Native Master Assembly'))
 capacity_before=require_personal_capacity(app,master,KNOWN_FILES,new_cloud_files=1,reserve_slots=1,protected_file_ids=[FILE_ID])
 master.activate()
 old=app.data.findFileById(FILE_ID);project=old.parentProject;name=ORIGINAL_NAME
 parent=next(f for f in project.rootFolder.dataFolders if f.name=='04 Native parts')
 folder=next(f for f in parent.dataFolders if f.name==PART_FOLDER)
 archive=os.path.join(tempfile.gettempdir(),'tinfox-native',KEY+'.f3d');options=app.importManager.createFusionArchiveImportOptions(archive);source_doc=app.importManager.importToNewDocument(options);source_doc.activate();design=fusion.Design.cast(app.activeProduct);component=design.rootComponent
 assert component.partNumber==KEY
 design.computeAll();issues=[f.name+': '+f.errorOrWarningMessage for f in component.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues
 before_volume=sum(b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume for b in component.bRepBodies)*1000
 capacity_at_publish=require_personal_capacity(app,master,KNOWN_FILES,new_cloud_files=1,reserve_slots=1,protected_file_ids=[FILE_ID])
 future=component.saveCopyAs(name+' - verified replacement pending '+str(int(time.time())),folder,'Native feature archive regenerated successfully. Assembly migration checks remain open.','');deadline=time.monotonic()+60
 while future.dataFile is None and time.monotonic()<deadline:adsk.doEvents();time.sleep(.1)
 new=future.dataFile;assert new is not None,'New native upload pending; reconcile before retry'
 master.activate();d=fusion.Design.cast(app.activeProduct);removed_mirrors=[]
 group=next(g.component for g in d.rootComponent.occurrences if any(o.component.partNumber==KEY for o in g.component.occurrences))
 for occurrence in list(group.occurrences):
  if occurrence.component.partNumber==KEY+'_right':removed_mirrors.append(occurrence.component.partNumber);occurrence.deleteMe()
 for occurrence in list(group.occurrences):
  if occurrence.component.partNumber==KEY:occurrence.deleteMe()
 occurrence=group.occurrences.addByInsert(new,core.Matrix3D.create(),True)
 volume=sum(b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume for b in occurrence.component.bRepBodies)*1000
 assert abs(volume-before_volume)<max(.01,before_volume*1e-7),('Published reference differs',before_volume,volume)
 master.save('Use verified native feature archive for '+KEY+'; migration gate remains open.')
 validation=next(f for f in project.rootFolder.dataFolders if f.name=='02 Validation exports');retired=next((f for f in validation.dataFolders if f.name=='Retired native drafts'),None)
 if retired is None:retired=validation.dataFolders.add('Retired native drafts')
 old.name='Retired - '+name+' - '+str(int(time.time()));assert old.move(retired)
 new.name=name
 feature_count=component.features.count;sketch_count=component.sketches.count
 source_doc.close(False);master.activate()
 print(json.dumps({'part':KEY,'old_file_id':FILE_ID,'file_id':new.id,'file_name':new.name,'version':new.versionNumber,'volume_mm3':volume,'archive_volume_mm3':before_volume,'removed_mirrors_to_rebuild':removed_mirrors,'feature_count':feature_count,'sketches':sketch_count,'retired_draft_folder':'02 Validation exports/Retired native drafts','personal_plan_capacity':{'before_open':capacity_before,'before_publication':capacity_at_publish},'passed':True}))
'''
for token,value in [('KNOWN_FILES',known_files()),('FILE_ID',record['file_id']),('ORIGINAL_NAME',record['file_name']),('PART_FOLDER',record['folder'].split('/')[-1]),('KEY',key)]:script=script.replace(token,repr(value))
r=rpc(script,key+'-publish-native-archive');assert r[0].get('success'),r
result=json.loads(r[0]['message']);(ROOT/'audits'/f'{key}-published-reference.json').write_text(json.dumps(result,indent=2))
record.setdefault('retired_file_ids',[]).append(record['file_id']);record.update(file_id=result['file_id'],file_name=result['file_name'],published_version=result['version']);registry[key]=record;(ROOT/'manifests/native-files.json').write_text(json.dumps(registry,indent=2));print(json.dumps(result,indent=2))
