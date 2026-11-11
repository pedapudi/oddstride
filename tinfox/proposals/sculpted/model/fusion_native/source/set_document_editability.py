"""Use Fusion's own document-status commands and verify the resulting status.

Only whitelisted Tinfox documents can be activated. Deactivation additionally
requires a completed saved candidate and never targets a working subsystem.
"""
import json,sys,time
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import known_files
ROOT=Path(__file__).resolve().parents[1]
def set_status(part,editable):
 known=known_files();matches=[(key,row) for key,row in known.items() if row['part']==part];assert len(matches)==1,(part,matches)
 file_id,meta=matches[0]
 if not editable:assert meta.get('completed_saved_candidate'),('Not an eligible retired/completed file',part)
 script='''import adsk.core as core,json

def run(_context: str):
 app=core.Application.get();file=app.data.findFileById(FILE_ID);assert file.parentProject.id==PROJECT_ID and file.isComplete
 doc=next((d for d in app.documents if d.isSaved and d.dataFile.id==FILE_ID),None)
 if doc is None:doc=app.documents.open(file,True)
 else:doc.activate()
 assert not doc.isModified,'Never rotate a document containing unsaved changes'
 before=app.data.personalUseLimits.editableFileCount
 already_correct=(not file.isReadOnly)==EDITABLE
 if not already_correct:
  if EDITABLE:assert app.data.personalUseLimits.maxEditableFileCount-before>=2,'Retain a free slot after activation'
  command_id='ActiveDocumentActivateCommand' if EDITABLE else 'ActiveDocumentDeactivateCommand';command=app.userInterface.commandDefinitions.itemById(command_id);assert command is not None,'This Fusion version does not expose the supported document-status command'
  assert command.execute(),'Document status command was not accepted'
 else:command_id=None
 print(json.dumps({'file_id':FILE_ID,'part':PART,'requested_editable':EDITABLE,'before_editable_count':before,'command_id':command_id,'already_correct':already_correct}))
'''
 for token,value in [('FILE_ID',file_id),('PROJECT_ID',meta['project_id']),('EDITABLE',editable),('PART',part)]:script=script.replace(token,repr(value))
 response=rpc(script,part+'-set-editability',timeout=30);assert response[0].get('success'),response
 record=json.loads(response[0]['message'])
 verify='''import adsk.core as core,json

def run(_context: str):
 app=core.Application.get();file=app.data.findFileById(FILE_ID);print(json.dumps({'file_id':file.id,'is_read_only':file.isReadOnly,'editable_file_count':app.data.personalUseLimits.editableFileCount,'max_editable_file_count':app.data.personalUseLimits.maxEditableFileCount,'version':file.versionNumber}))
'''.replace('FILE_ID',repr(file_id))
 for attempt in range(3):
  response=rpc(verify,part+'-verify-editability',timeout=30,read_only=True);assert response[0].get('success'),response
  result=json.loads(response[0]['message'])
  if result['is_read_only']!=editable:break
  time.sleep(1)
 record.update(verification=result,passed=result['is_read_only']!=editable)
 path=ROOT/'audits/document-editability-changes.json';history=json.loads(path.read_text()) if path.exists() else [];history.append(record);path.write_text(json.dumps(history,indent=2));assert record['passed'],record
 print(json.dumps(record,indent=2));return record
if __name__=='__main__':
 assert sys.argv[2] in ['editable','read-only'];set_status(sys.argv[1],sys.argv[2]=='editable')
