"""Move one verified unused Tinfox proof file into retained validation storage."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
proof=json.loads((ROOT/'audits/native-part-document-proof.json').read_text());manifest=json.loads((ROOT/'manifests/parts.json').read_text())
script='''import adsk.core as core,json

def run(_context: str):
 app=core.Application.get();file=app.data.findFileById(FILE_ID);assert file is not None and file.parentProject.id==PROJECT_ID and file.isComplete
 assert not file.hasParentReferences and file.parentReferences.count==0,'Retain any referenced proof file'
 for doc in app.documents:
  if doc.isSaved and doc.dataFile.id==FILE_ID:assert not doc.isModified,'Preserve unsaved changes'
 before={'name':file.name,'version':file.versionNumber,'folder':file.parentFolder.name,'read_only':file.isReadOnly}
 parent=next(f for f in file.parentProject.rootFolder.dataFolders if f.name=='02 Validation exports')
 folder=next((f for f in parent.dataFolders if f.name=='Native editability proofs'),None)
 if folder is None:folder=parent.dataFolders.add('Native editability proofs')
 moved=file.move(folder);assert moved and file.parentFolder.id==folder.id
 assert file.versionNumber==before['version'] and not file.hasParentReferences
 print(json.dumps({'file_id':FILE_ID,'action':'moved to validation archive','before':before,'after':{'name':file.name,'version':file.versionNumber,'folder':'02 Validation exports/Native editability proofs','read_only':file.isReadOnly},'references_before_and_after':0,'deleted_files':0,'editable_status_changed':False,'passed':True}))
'''
for token,value in [('FILE_ID',proof['file_id']),('PROJECT_ID',manifest['fusion_project']['id'])]:script=script.replace(token,repr(value))
response=rpc(script,'archive-unused-native-proof',timeout=60);assert response[0].get('success'),response
result=json.loads(response[0]['message']);(ROOT/'audits/cleanup-proof-file.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
