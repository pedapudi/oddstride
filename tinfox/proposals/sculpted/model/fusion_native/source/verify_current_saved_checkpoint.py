"""Verify the new current Leg or Master save without rejecting required construction IDs."""
import datetime,json,sys
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];role=sys.argv[1];assert role in ['leg','master'];save=json.loads((ROOT/('audits/current-pose-history-checkpoint.json'if role=='leg'else'audits/current-native-master-checkpoint.json')).read_text())
if role=='leg' and (ROOT/'audits/current-leg-final-visibility-checkpoint.json').exists():
    visibility=json.loads((ROOT/'audits/current-leg-final-visibility-checkpoint.json').read_text())
    if visibility['previous_version']>=save['previous_version']:save=visibility
expected=save['previous_version']+1
script=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,ROLE);d=fusion.Design.cast(doc.products.itemByProductType('DesignProductType'));root=d.rootComponent;links=[]
 if ROLE=='master':links=[{'role':o.attributes.itemByName('Tinfox','Subsystem').value,'version':o.documentReference.version}for o in root.occurrences]
 print(json.dumps({'file_id':doc.dataFile.id,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'read_only':doc.dataFile.isReadOnly,'editable_files':len(app.data.personalUseLimits.editableFiles),'visible_root':[o.component.partNumber for o in root.occurrences if o.isLightBulbOn],'subsystems':links,'timeline_count':d.timeline.count,'timeline_at_end':d.timeline.markerPosition==d.timeline.count}))
'''.replace('ROLE',repr(role))
reply=rpc(script,'current-'+role+'-save-verification',timeout=90,read_only=True);assert reply[0]['success'],reply;record=json.loads(reply[0]['message']);assert record['version']==expected and record['complete']and not record['modified']and not record['read_only']and record['timeline_at_end'],record;record['verified_utc']=datetime.datetime.now(datetime.UTC).isoformat();path='audits/current-'+role+'-v'+str(expected)+'-save-verification.json';(ROOT/path).write_text(json.dumps(record,indent=2));subs=json.loads((ROOT/'manifests/subsystems.json').read_text())
if role=='leg':subs['subsystems'][role].update(version=expected,save_verified=True,verification_report=path,phase='current_four_leg_assembly_pose_verified')
else:
    assert {r['role']:r['version']for r in record['subsystems']}==save['subsystem_versions'];subs.update(master_saved_version=expected,master_save_verification=path);status=json.loads((ROOT/'manifests/native-master-status.json').read_text());status.update(saved_version=expected,save_verification=path,subsystem_versions=save['subsystem_versions'],assembly_audit='audits/current-master-assembly-refresh.json',source_of_truth=False,open_gates=['Saved Master reopen and native whole review export.','Independent browser/motion parity and explicit whole low-profile authority approval.']);(ROOT/'manifests/native-master-status.json').write_text(json.dumps(status,indent=2))
(ROOT/'manifests/subsystems.json').write_text(json.dumps(subs,indent=2));print(record)
