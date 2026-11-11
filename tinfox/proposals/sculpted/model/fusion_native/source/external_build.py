"""Author editable native part documents and insert referenced occurrences in V0."""
import json,sys
from pathlib import Path
from build_part import recipe,LABELS
from run_native import rpc
from fetch_exports import fetch
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
def build(key,replace=False):
 manifest=json.loads((ROOT/'manifests/parts.json').read_text());graph=recipe(key)
 group='Shared leg designs';folder='Leg masters'
 if key.startswith(('battery_','chassis_','body_','belly_','front_')):group='Body and chassis';folder='Body and chassis'
 if key.startswith(('electronics_','lidar_','sensor_','power_')):group='Electronics and sensors';folder='Electronics and sensors'
 script=script_header()+(ROOT/'source/fusion_builder.py').read_text()+'''

def run(_context: str):
 import time,tempfile,os,adsk
 app=core.Application.get();master=next(d for d in app.documents if d.name.startswith('Tinfox - Native Master Assembly'))
 capacity_before=require_personal_capacity(app,master,KNOWN_FILES,new_cloud_files=1,reserve_slots=1,protected_file_ids=CURRENT_FILE_IDS)
 master.activate()
 master_design=fusion.Design.cast(app.activeProduct);group=next(o.component for o in master_design.rootComponent.occurrences if o.component.name==GROUP)
 existing=[o for o in group.occurrences if o.component.partNumber==KEY]
 assert REPLACE or not existing,'Part already exists in master'
 project=next(p for p in app.data.activeHub.dataProjects if p.id==PROJECT_ID)
 parent=next((f for f in project.rootFolder.dataFolders if f.name=='04 Native parts'),None)
 if parent is None:parent=project.rootFolder.dataFolders.add('04 Native parts')
 folder=next((f for f in parent.dataFolders if f.name==FOLDER),None)
 if folder is None:folder=parent.dataFolders.add(FOLDER)
 name='V0 - '+LABEL+' ['+KEY+']'
 previous_file=next((f for f in folder.dataFiles if f.name==name),None)
 assert REPLACE or previous_file is None,'Native file already exists; reconcile before rebuilding'
 # Replacements are authored in isolation. The published source remains intact
 # until the new feature history has regenerated, exported and uploaded.
 document=app.documents.add(core.DocumentTypes.FusionDesignDocumentType);d=fusion.Design.cast(app.activeProduct)
 d.designType=fusion.DesignTypes.ParametricDesignType;c=d.rootComponent;c.partNumber=KEY;d.attributes.add('Tinfox','OwnedPartBuild',KEY)
 graph=GRAPH;start=time.perf_counter();builder=Builder(d,c,KEY,graph['nodes']);body=builder.finish(graph['root'])
 d.computeAll()
 issues=[f.name+': '+f.errorOrWarningMessage for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues
 construction=time.perf_counter()-start
 volume=body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000
 assert abs(volume-graph['volume_mm3'])/graph['volume_mm3']<.01,('Gross volume mismatch',KEY,volume,graph['volume_mm3'])
 path=os.path.join(tempfile.gettempdir(),'tinfox-native');os.makedirs(path,exist_ok=True)
 paths=[os.path.join(path,KEY+extension) for extension in ['.step','.stl','.f3d']]
 ex=d.exportManager;assert ex.execute(ex.createSTEPExportOptions(paths[0],c))
 opts=ex.createSTLExportOptions(c,paths[1]);opts.unitType=fusion.DistanceUnits.MillimeterDistanceUnits;opts.meshRefinement=fusion.MeshRefinementSettings.MeshRefinementHigh;assert ex.execute(opts)
 assert ex.execute(ex.createFusionArchiveExportOptions(paths[2]))
 upload_name=name if previous_file is None else name+' - replacement pending '+str(int(time.time()))
 capacity_at_publish=require_personal_capacity(app,master,KNOWN_FILES,new_cloud_files=1,reserve_slots=1,protected_file_ids=CURRENT_FILE_IDS)
 future=c.saveCopyAs(upload_name,folder,'V0 native editable part. Shape and assembly migration gates remain open.','')
 deadline=time.monotonic()+60
 while future.dataFile is None and time.monotonic()<deadline:adsk.doEvents();time.sleep(.1)
 data_file=future.dataFile;assert data_file is not None,'Native copy upload pending; reconcile before retry'
 record={'part':KEY,'label':LABEL,'file_id':data_file.id,'file_name':data_file.name,'folder':'04 Native parts/'+FOLDER,'sketches':c.sketches.count,'feature_count':c.features.count,'parameter_count':d.userParameters.count,'volume_mm3':volume,'body_count':c.bRepBodies.count,'native_construction_seconds':construction,'paths':paths,'features':[{'name':f.name,'type':f.objectType} for f in c.features]}
 master.activate()
 dependent_mirrors=[o for o in group.occurrences if o.component.partNumber==KEY+'_right']
 for occurrence in dependent_mirrors:occurrence.deleteMe()
 for occurrence in existing:occurrence.deleteMe()
 occurrence=group.occurrences.addByInsert(data_file,core.Matrix3D.create(),True)
 assert occurrence is not None and occurrence.isReferencedComponent
 # The source document was fully regenerated above. Recomputing the entire
 # growing assembly for each publication duplicates the final assembly gate.
 published_volume=sum(b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume for b in occurrence.component.bRepBodies)*1000
 assert abs(published_volume-volume)<max(.01,volume*1e-7),('Published reference differs',volume,published_volume)
 master.save('Reference native part file: '+KEY+'; migration audit remains open.')
 if previous_file:
  validation=next(f for f in project.rootFolder.dataFolders if f.name=='02 Validation exports')
  retired=next((f for f in validation.dataFolders if f.name=='Retired native drafts'),None)
  if retired is None:retired=validation.dataFolders.add('Retired native drafts')
  previous_file.name='Retired - '+name+' - '+str(int(time.time()))
  assert previous_file.move(retired)
  data_file.name=name
  record['retired_file_ids']=[previous_file.id]
  record['file_name']=name
 record['removed_mirrors_to_rebuild']=[KEY+'_right'] if dependent_mirrors else []
 record['published_volume_mm3']=published_volume
 record['personal_plan_capacity']={'before_build':capacity_before,'before_publication':capacity_at_publish}
 document.close(False);master.activate()
 print(json.dumps(record))
'''
 known=known_files();current_ids=[file_id for file_id,row in known.items() if row.get('part')==key]
 for token,value in [('KNOWN_FILES',known),('CURRENT_FILE_IDS',current_ids),('PROJECT_ID',manifest['fusion_project']['id']),('GRAPH',graph),('GROUP',group),('FOLDER',folder),('KEY',key),('LABEL',LABELS.get(key,key.replace('_',' ').capitalize())),('REPLACE',replace)]:script=script.replace(token,repr(value))
 (ROOT/'source/last_external_script.py').write_text(script)
 messages=rpc(script,key+'-external-build')
 if not messages[0].get('success',True):return False
 record=json.loads(messages[0]['message']);registry_path=ROOT/'manifests/native-files.json';registry=json.loads(registry_path.read_text()) if registry_path.exists() else {}
 registry[key]=record;registry_path.write_text(json.dumps(registry,indent=2))
 for path in record['paths']:fetch(path,Path(path).name)
 manifest=json.loads((ROOT/'manifests/parts.json').read_text());part=next(p for p in manifest['parts'] if p['id']==key)
 part.update(native_file_id=record['file_id'],native_feature_count=record['feature_count'],native_sketch_count=record['sketches'],native_component=record['label'],state='native_built_pending_audit');(ROOT/'manifests/parts.json').write_text(json.dumps(manifest,indent=2))
 return True
if __name__=='__main__':sys.exit(0 if build(sys.argv[1],'--replace' in sys.argv) else 1)
