"""Author a native part archive without allocating a cloud document slot.

Qualified native feature histories are merged into subsystem documents later.
The generated STEP/STL files are audit and manufacturing exports only.
"""
import json,sys
from pathlib import Path
from build_part import recipe,LABELS
from run_native import rpc
from fetch_exports import fetch
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
def build(key):
 graph=recipe(key)
 script=script_header()+(ROOT/'source/fusion_builder.py').read_text()+'''

def run(_context: str):
 import time,tempfile,os,adsk
 app=core.Application.get();master=next(d for d in app.documents if d.name.startswith('Tinfox - Native Master Assembly'));assert not master.isModified
 capacity=require_personal_capacity(app,master,KNOWN,new_cloud_files=0,reserve_slots=1)
 document=app.documents.add(core.DocumentTypes.FusionDesignDocumentType);document.name='Tinfox native work - '+KEY;d=fusion.Design.cast(app.activeProduct)
 d.designType=fusion.DesignTypes.ParametricDesignType;c=d.rootComponent;c.partNumber=KEY;d.attributes.add('Tinfox','OwnedPartBuild',KEY)
 graph=GRAPH;start=time.perf_counter();builder=Builder(d,c,KEY,graph['nodes']);body=builder.finish(graph['root'])
 d.computeAll()
 issues=[f.name+': '+f.errorOrWarningMessage for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues
 construction=time.perf_counter()-start
 volume=sum(b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume for b in c.bRepBodies)*1000
 assert abs(volume-graph['volume_mm3'])/graph['volume_mm3']<.01,('Gross volume mismatch',KEY,volume,graph['volume_mm3'])
 path=os.path.join(tempfile.gettempdir(),'tinfox-native');os.makedirs(path,exist_ok=True)
 paths=[os.path.join(path,KEY+extension) for extension in ['.step','.stl','.f3d']]
 ex=d.exportManager;assert ex.execute(ex.createSTEPExportOptions(paths[0],c))
 opts=ex.createSTLExportOptions(c,paths[1]);opts.unitType=fusion.DistanceUnits.MillimeterDistanceUnits;opts.meshRefinement=fusion.MeshRefinementSettings.MeshRefinementHigh;assert ex.execute(opts)
 assert ex.execute(ex.createFusionArchiveExportOptions(paths[2]))
 record={'part':KEY,'label':LABEL,'sketches':c.sketches.count,'feature_count':c.features.count,'parameter_count':d.userParameters.count,'volume_mm3':volume,'body_count':c.bRepBodies.count,'native_construction_seconds':construction,'paths':paths,'features':[{'name':f.name,'type':f.objectType} for f in c.features],'personal_plan_capacity':capacity,'cloud_document_created':False,'source_master_modified':master.isModified}
 document.close(False);master.activate()
 print(json.dumps(record))
'''
 for token,value in [('KNOWN',known_files()),('GRAPH',graph),('KEY',key),('LABEL',LABELS.get(key,key.replace('_',' ').capitalize()))]:script=script.replace(token,repr(value))
 (ROOT/'source/last_local_script.py').write_text(script)
 messages=rpc(script,key+'-local-build',timeout=1200);assert messages[0].get('success'),messages
 record=json.loads(messages[0]['message']);registry_path=ROOT/'manifests/local-native-archives.json';registry=json.loads(registry_path.read_text()) if registry_path.exists() else {};registry[key]=record;registry_path.write_text(json.dumps(registry,indent=2))
 for path in record['paths']:fetch(path,Path(path).name)
 manifest_path=ROOT/'manifests/parts.json';manifest=json.loads(manifest_path.read_text());part=next(p for p in manifest['parts'] if p['id']==key)
 part.update(native_feature_count=record['feature_count'],native_sketch_count=record['sketches'],native_component=record['label'],native_local_archive='exports/'+key+'.f3d',state='native_built_pending_audit');manifest_path.write_text(json.dumps(manifest,indent=2));return record
if __name__=='__main__':
 record=build(sys.argv[1]);print(json.dumps({k:record[k] for k in ['part','feature_count','sketches','native_construction_seconds','cloud_document_created']},indent=2))
