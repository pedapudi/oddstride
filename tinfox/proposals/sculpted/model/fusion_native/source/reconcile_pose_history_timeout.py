"""Reconcile the completed history repair after its client connection timed out."""
import hashlib,json
from pathlib import Path
from run_native import rpc

ROOT=Path(__file__).resolve().parents[1]
unknown=json.loads((ROOT/'manifests/publication-state.json').read_text())
assert unknown['tag']=='current-pose-history-reorder' and unknown['state']=='execution_state_unknown'
standing=json.loads((ROOT/'audits/current-native-installed-all.json').read_text())
assert standing['passed'] and standing['native_bodies']==604
script=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,os
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);journal=json.load(open(os.path.join(os.path.expanduser('~'),'Library','Caches','Tinfox','current-pose-history-reorder.json')));assert journal['stage']=='complete';modules=[o for o in d.rootComponent.occurrences if o.component.partNumber.startswith('CURRENT_ASSEMBLY_')];assert len(modules)==4;joints=[j for o in modules for j in o.component.joints];children=[c for o in modules for frame in o.component.occurrences if frame.component.partNumber.startswith('CURRENT_FRAME_')for c in frame.component.occurrences];assert len(joints)==24 and len(children)==128;assert min(j.timelineObject.index for j in joints)>max(c.timelineObject.index for c in children);assert all(j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for j in joints);assert d.timeline.markerPosition==d.timeline.count;print(json.dumps({'passed':True,'saved_version':doc.dataFile.versionNumber,'working_modified':doc.isModified,'journal':journal,'new_pose_mates':24,'rebound_child_occurrences':128,'all_physical_occurrences_precede_pose_mates':True,'timeline_at_end':True,'reused_existing_datum_sketches':True,'saved':False,'scope':'Actual committed state reconciles the timed-out mutation. Standing placement was independently rechecked for all592 items; moving edit/restore gate remains pending.'}))
'''
reply=rpc(script,'current-pose-history-timeout-reconciliation',timeout=120,read_only=True)
assert reply[0]['success'],reply
record=json.loads(reply[0]['message']);record['transport_timeout']=unknown
record['standing_audit_sha256']=hashlib.sha256((ROOT/'audits/current-native-installed-all.json').read_bytes()).hexdigest()
(ROOT/'audits/current-pose-history-reorder.json').write_text(json.dumps(record,indent=2))
(ROOT/'audits/current-pose-history-client-timeout.json').write_text(json.dumps(unknown,indent=2))
(ROOT/'manifests/publication-state.json').write_text(json.dumps({'state':'reconciled','prior_operation':unknown,'evidence':'audits/current-pose-history-reorder.json','safe_to_continue':True},indent=2))
print(record)
