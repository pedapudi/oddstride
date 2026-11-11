"""Read-only Personal-plan inventory and capacity checks before native writes.

Autodesk exposes no documented setter for editable-file status. This module
never activates, deactivates, deletes, closes, or saves a document. It reports
known saved Tinfox candidates for the separately guarded Fusion UI commands.

Sources:
https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_PersonalUseLimits.htm
https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Data_personalUseLimits.htm
https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_DataFile_isReadOnly.htm
"""
import json

class PersonalPlanCapacityError(RuntimeError):
    pass

def personal_plan_inventory(app, known_files, protected_file_ids=()):
    limits=app.data.personalUseLimits
    protected=set(protected_file_ids)
    open_saved={}
    unsaved_count=0
    for document in app.documents:
        if not document.isSaved:
            unsaved_count+=1
            continue
        file=document.dataFile
        if file is not None:
            open_saved[file.id]={'modified':document.isModified,'name':document.name}
            if document.isModified:protected.add(file.id)
    if limits is None:
        return {'personal_plan':False,'editable_file_count':None,'max_editable_file_count':None,'available_slots':None,'known_tinfox_editable_files':[],'manual_read_only_candidates':[],'unsaved_open_documents':unsaved_count,'status_change_api_supported':False}
    files=list(limits.editableFiles)
    rows=[];candidates=[];unmanaged=0
    for file in files:
        known=known_files.get(file.id)
        if known is None:
            unmanaged+=1
            continue
        row={'file_id':file.id,'name':file.name,'part':known.get('part'),'project_id':file.parentProject.id,'is_read_only':file.isReadOnly,'upload_complete':file.isComplete,'open_modified':open_saved.get(file.id,{}).get('modified',False),'protected':file.id in protected}
        project_matches=file.parentProject.id==known.get('project_id')
        eligible=(known.get('completed_saved_candidate',False) and project_matches and file.isComplete and not row['is_read_only'] and not row['protected'])
        row['manual_read_only_candidate']=eligible
        rows.append(row)
        if eligible:candidates.append({'file_id':file.id,'name':file.name,'part':known.get('part')})
    count=limits.editableFileCount;maximum=limits.maxEditableFileCount
    return {'personal_plan':True,'editable_file_count':count,'max_editable_file_count':maximum,'available_slots':maximum-count,'known_tinfox_editable_files':rows,'unmanaged_editable_file_count':unmanaged,'manual_read_only_candidates':candidates,'unsaved_open_documents':unsaved_count,'status_change_api_supported':False,'status_note':'isReadOnly has no setter. The separately guarded set_document_editability.py invokes Fusion Make Editable/Make Read-Only commands and independently verifies status. Read-only can also reflect permissions or another editor.'}

def require_personal_capacity(app, master, known_files, new_cloud_files=1, reserve_slots=1, protected_file_ids=()):
    assert new_cloud_files>=0 and reserve_slots>=0
    assert master.isSaved and master.dataFile is not None,'Save the known master before native publication'
    protected=set(protected_file_ids)|{master.dataFile.id}
    inventory=personal_plan_inventory(app,known_files,protected)
    inventory.update(new_cloud_files=new_cloud_files,reserved_free_slots=reserve_slots,required_available_slots=new_cloud_files+reserve_slots,master_file_id=master.dataFile.id)
    if master.dataFile.isReadOnly:
        raise PersonalPlanCapacityError(json.dumps({'reason':'The native master is read-only. Make that master Editable before modifying its assembly.','inventory':inventory}))
    if inventory['personal_plan'] and inventory['available_slots']<new_cloud_files+reserve_slots:
        raise PersonalPlanCapacityError(json.dumps({'reason':'Insufficient editable-document capacity. Stop before creating or publishing a file. In Manage documents, set only a listed saved Tinfox candidate to Read-Only. Keep the master and current work editable. No files were changed by this check.','inventory':inventory}))
    return inventory
