"""Reconcile journaled obsolete-joint retirement after its client timeout."""
import hashlib,json,subprocess
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
unknown=json.loads((ROOT/'manifests/publication-state.json').read_text());assert unknown['tag']=='remove-obsolete-pose-joints' and unknown['state']=='execution_state_unknown'
raw=subprocess.check_output(['ssh','sunil@sunils-mac-mini.lan','cat ~/Library/Caches/Tinfox/retired-pose-removal.json'],timeout=20);journal=json.loads(raw);assert journal['stage']=='complete'and journal['result']['passed'];assert len(journal['result']['deleted_pose_joints'])==24
script=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');d=fusion.Design.cast(doc.products.itemByProductType('DesignProductType'));old=[o for o in d.rootComponent.occurrences if o.component.partNumber in ['ASSEMBLY_FL','ASSEMBLY_FR','ASSEMBLY_RL','ASSEMBLY_RR']];current=[o for o in d.rootComponent.occurrences if o.component.partNumber.startswith('CURRENT_ASSEMBLY_')];assert len(old)==4 and len(current)==4;assert all(o.component.joints.count==0 and not o.isLightBulbOn for o in old);assert all(o.component.joints.count==6 for o in current);assert d.timeline.markerPosition==d.timeline.count;assert d.userParameters.itemByName('qa_current_pose_case')is None;print(json.dumps({'passed':True,'old_pose_joints':0,'current_pose_joints':24,'old_construction_modules_retained':4,'saved_version':doc.dataFile.versionNumber,'modified':doc.isModified,'timeline_at_end':True}))
'''
reply=rpc(script,'obsolete-pose-removal-timeout-reconciliation',timeout=180,read_only=True);assert reply[0]['success'],reply;readback=json.loads(reply[0]['message']);result=journal['result'];result['separate_readback']=readback;result['transport_timeout']=unknown;result['remote_journal_sha256']=hashlib.sha256(raw).hexdigest()
(ROOT/'audits/removed-obsolete-pose-joints.json').write_text(json.dumps(result,indent=2));(ROOT/'audits/removed-obsolete-pose-joints-client-timeout.json').write_text(json.dumps(unknown,indent=2));(ROOT/'manifests/publication-state.json').write_text(json.dumps({'state':'reconciled','prior_operation':unknown,'evidence':'audits/removed-obsolete-pose-joints.json','safe_to_continue':True},indent=2));print(readback)
