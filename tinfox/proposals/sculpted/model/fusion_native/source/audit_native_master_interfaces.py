"""Inspect selected interfaces directly on saved native assembly solids."""
import json,datetime
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
status=json.loads((ROOT/'manifests/native-master-status.json').read_text());assembly=json.loads((ROOT/'audits/native-master-shared-subsystem-refresh.json').read_text());paths={k:v['path'] for k,v in assembly['instances'].items()}
pairs=[['body_center_0','front_fascia'],['body_center_0','body_nose_surround'],['front_fascia','body_nose_surround'],['body_center_0','chassis_crossmember_121'],['front_fascia','chassis_crossmember_121'],['body_nose_surround','chassis_crossmember_121'],['body_center_0','chassis_beam_102'],['body_center_0','chassis_beam_-102'],['chassis_lower_brace','chassis_beam_102'],['chassis_lower_brace','chassis_beam_-102'],['electronics_shelf','chassis_lower_brace'],['belly_center_0','battery_cassette'],['FL_bearing_inner','FL_shin_inner'],['FL_bearing_outer','FL_shin_outer']]+[['body_center_0',leg+'_roll_motor'] for leg in ['FL','FR','RL','RR']]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context: str):
 app=core.Application.get();previous=app.activeDocument;doc=authoring_document(app,'master');assert doc.dataFile.versionNumber==VERSION and doc.dataFile.isComplete and not doc.isModified;doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;versions={o.attributes.itemByName('Tinfox','Subsystem').value:o.documentReference.version for o in root.occurrences};assert versions==VERSIONS;all_occurrences={o.fullPathName:o for o in root.allOccurrences};tick=time.monotonic();rows=[]
 for pair in PAIRS:
  entities=core.ObjectCollection.create();body_counts=[]
  for name in pair:
   occ=all_occurrences[PATHS[name]];assert occ.component.bRepBodies.count>0;body_counts.append(occ.component.bRepBodies.count)
   for body in occ.component.bRepBodies:entities.add(body.createForAssemblyContext(occ))
  inputs=d.createInterferenceInput(entities);assert inputs is not None;inputs.areCoincidentFacesIncluded=False;started=time.monotonic();results=d.analyzeInterference(inputs);assert results is not None;volumes=[]
  for result in results:
   body=result.interferenceBody;assert body is not None and body.isValid;volumes.append(abs(body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume)*1000)
  volume=sum(volumes);rows.append({'pair':pair,'bodies':body_counts,'interference_count':results.count,'volume_mm3':volume,'passed':volume<1e-6,'seconds':time.monotonic()-started})
 assert not doc.isModified;previous.activate();print(json.dumps({'passed':all(row['passed'] for row in rows),'master_version':doc.dataFile.versionNumber,'file_id':doc.dataFile.id,'subsystem_versions':versions,'saved_unmodified':not doc.isModified,'checker':'Fusion Design.analyzeInterference on root-context native body proxies; transient result volumes, no model bodies created','conditions':{'pose':'Frozen stand','coincident_faces_included':False,'volume_tolerance_mm3':1e-6},'checks':rows,'elapsed_seconds':time.monotonic()-tick,'scope':'Selected saved-baseline interfaces only. Coincident bearing/support faces are allowed. This does not validate a newer browser revision, continuous motion, tool/holder access, strength or real fit.'}))
'''.replace('VERSIONS',repr(status['subsystem_versions'])).replace('VERSION',str(status['saved_version'])).replace('PAIRS',repr(pairs)).replace('PATHS',repr(paths))
r=rpc(s,'native-master-critical-interfaces',timeout=240,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);record['updated_utc']=datetime.datetime.now(datetime.UTC).isoformat();record['source_model_sha256']=status['source_reference_sha256'];record['native_inputs']=json.loads((ROOT/'manifests/current-native-exports.json').read_text())['parts'];(ROOT/'audits/native-master-critical-interfaces.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'checks':len(record['checks']),'seconds':record['elapsed_seconds'],'failed':[r for r in record['checks'] if not r['passed']]})
