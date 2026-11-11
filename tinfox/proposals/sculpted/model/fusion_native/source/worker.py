"""Resume the V0 native build when the user-provided Fusion tunnel is available.

One writer owns Fusion. Stops between parts if STOP_WORKER is present. A failed
part is recorded for review; an unknown execution state triggers reconciliation
before another mutation. This worker never switches the authoritative CAD source.
"""
import json,sys,time,datetime,hashlib,urllib.request,fcntl,traceback,subprocess,os
from pathlib import Path
from build_part import build
from mirror_part import mirror,source_for
from reconcile import reconcile
NATIVE=Path(__file__).resolve().parents[1];MODEL=NATIVE.parent
STATUS=NATIVE/'manifests/worker-status.json';STOP=NATIVE/'manifests/STOP_WORKER'
ORDER=['lidar_lid','power_button','knee_axle','knee_inner_spacer','sleeve_0','sleeve_1','shin_clamp_sleeve_37','shin_clamp_sleeve_105','pod_sleeve_90','pod_sleeve_210','pod_sleeve_330','battery_access_latch_-1','battery_latch_-1','battery_side_panel_-1','chassis_crossmember_121','shin_outer','input_crank','thigh_inner','thigh_outer','roll_cartridge_1','motor_carrier_1','motor_carrier_-1','chassis_beam_-102','battery_cassette','body_center_0','belly_center_0','sensor_bezel','front_fascia','body_nose_surround','foot']
def status(state,**extra):
 row={'pid':os.getpid(),'state':state,'updated_utc':datetime.datetime.now(datetime.UTC).isoformat(),'design_revision':'V0','authoritative_source':'CadQuery V0 until complete native migration audits pass',**extra}
 STATUS.write_text(json.dumps(row,indent=2));print(row['updated_utc'],state,extra.get('part',''),flush=True)
def ping():
 p=json.load(open('/tmp/fusion-mcp-connection.json'));body={'jsonrpc':'2.0','id':198,'method':'ping'}
 try:
  with urllib.request.urlopen(urllib.request.Request(p['url'],data=json.dumps(body).encode(),headers=p['headers']),timeout=4) as r:return r.status==200
 except (OSError,ValueError):return False

def main():
 lock=open(NATIVE/'manifests/worker.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 source=json.loads((NATIVE/'manifests/parts.json').read_text());frozen=source['source_model_sha256'];keys=[p['id'] for p in source['parts']]
 pending=ORDER+[k for k in keys if k not in ORDER];pending=[k for k in pending if k in keys]
 deferred_path=NATIVE/'manifests/deferred-parts.json'
 deferred=json.loads(deferred_path.read_text())['parts'] if deferred_path.exists() else []
 pending=[k for k in pending if k not in deferred]
 failed={};built=set();needs_reconcile=True;completed_since_save=0;deadline=time.monotonic()+8*3600
 while pending and time.monotonic()<deadline and not STOP.exists():
  live=hashlib.sha256((MODEL/source['source_file']).read_bytes()).hexdigest()
  if live!=frozen:status('source_changed',expected=frozen,actual=live);return
  if not ping():
   status('waiting_for_fusion_transport',remaining=len(pending),failed=failed)
   time.sleep(60);continue
  if needs_reconcile:
   status('reconciling_native_document')
   try:state=reconcile()
   except Exception as error:
    status('reconciliation_failed',detail=str(error));time.sleep(60);continue
   built={p['id'] for p in state['parts']};pending=[k for k in pending if k not in built];needs_reconcile=False
   if not pending:break
  key=pending.pop(0);dependency=source_for(key)
  if dependency and dependency[0] not in built:
   if dependency[0] in failed:failed[key]='Canonical native part failed: '+dependency[0];continue
   pending.append(key);continue
  status('building_native_part',part=key,remaining=len(pending),built=len(built))
  try:success=mirror(key) if dependency else build(key)
  except Exception as error:
   failed[key]={'kind':'execution_state_unknown','detail':str(error)};pending.insert(0,key);needs_reconcile=True
   status('execution_state_unknown',part=key,detail=str(error));time.sleep(30);continue
  if not success:failed[key]={'kind':'native_feature_error','evidence':'audits/'+key+('-mirror' if dependency else '-build')+'-rpc.json'};continue
  built.add(key);completed_since_save+=1
  audit_script=NATIVE/'source/audit_part.py';python=NATIVE.parents[3]/'.venv/bin/python'
  status('auditing_native_shape',part=key)
  result=subprocess.run([str(python),str(audit_script),key],capture_output=True,text=True)
  print(result.stdout,flush=True)
  if result.returncode:failed[key]={'kind':'audit_execution_error','detail':result.stderr[-2000:]}
  else:
   audit=json.loads((NATIVE/'audits'/f'{key}-geometry.json').read_text())
   if not audit['geometric_gate_passed']:failed[key]={'kind':'shape_audit_failed','evidence':'audits/'+key+'-geometry.json'}
  if completed_since_save>=12:needs_reconcile=True;completed_since_save=0
 if ping():
  try:state=reconcile();built={p['id'] for p in state['parts']}
  except Exception as error:failed['checkpoint']=str(error)
 status('stopped_by_marker' if STOP.exists() else 'feature_build_pass_finished' if not pending else 'time_window_finished',built=len(built),remaining=pending,deferred_parts=deferred,failed=failed,migration_gate_passed=False)
if __name__=='__main__':main()
