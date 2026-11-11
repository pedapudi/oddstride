"""Discard only the identified failed, unsaved nose replay document."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
script='''import adsk.core as core,adsk.fusion as fusion,json

def run(_context: str):
 app=core.Application.get();before=[{'name':d.name,'saved':d.isSaved,'modified':d.isModified} for d in app.documents];removed=[]
 for doc in list(app.documents):
  if doc.name!='Tinfox native work - body_nose_surround':continue
  assert not doc.isSaved,'A saved document needs separate reference review'
  doc.activate();design=fusion.Design.cast(app.activeProduct);owner=design.attributes.itemByName('Tinfox','OwnedPartBuild');assert owner is not None and owner.value=='body_nose_surround','Do not discard unknown work'
  c=design.rootComponent
  removed.append({'name':doc.name,'owner':owner.value,'feature_count':c.features.count,'sketch_count':c.sketches.count,'body_count':c.bRepBodies.count,'edge_count':sum(b.edges.count for b in c.bRepBodies),'face_count':sum(b.faces.count for b in c.bRepBodies),'saved_cloud_file':False,'reason':'Failed replay construction, retired after user rejected the excessive construction complexity'})
  assert doc.close(False)
 after=[{'name':d.name,'saved':d.isSaved,'modified':d.isModified} for d in app.documents]
 assert not any(d['name']=='Tinfox native work - body_nose_surround' for d in after)
 head=next(d for d in app.documents if d.name.startswith('Tinfox - Head'));head.activate();design=fusion.Design.cast(app.activeProduct)
 assert not head.isModified
 failed_components=[c.name for c in design.allComponents if c.partNumber=='body_nose_surround'];assert not failed_components,'Unexpected saved failed component requires reference review'
 print(json.dumps({'before':before,'after':after,'removed_failed_work':removed,'failed_nose_documents_before':sum(d['name']=='Tinfox native work - body_nose_surround' for d in before),'failed_nose_documents_after':0,'failed_nose_components_in_head':failed_components,'head_file_id':head.dataFile.id,'head_version':head.dataFile.versionNumber,'head_current_components':[o.component.partNumber for o in design.rootComponent.occurrences],'saved_cloud_files_deleted':0,'new_cloud_files':0,'unknown_unsaved_work_touched':False,'passed':True}))
'''
r=rpc(script,'failed-nose-cleanup',timeout=60);assert r[0].get('success'),r
record=json.loads(r[0]['message']);(ROOT/'audits/failed-nose-cleanup.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
