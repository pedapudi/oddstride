"""Protect the imported current reference library and verified first-leg placement."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1];assert json.loads((ROOT/'audits/current-native-installed-FL.json').read_text())['passed']
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);before=doc.dataFile.versionNumber;tick=time.monotonic();assert len([c for c in d.allComponents if c.partNumber.startswith('CURRENT_REFERENCE_')and not c.partNumber.startswith('CURRENT_REFERENCE_BUNDLE_')])==24;assert doc.save('Checkpoint current low-profile whole-robot integration: all488 purchased leg reference items imported and identified; first front-left leg has26 shared native custom/stock instances and122 purchased references placed in verified native pose frames. Canonical detached motor complex remains Leg24; whole-robot integration is not yet promoted.');print(json.dumps({'save_requested':True,'previous_version':before,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'capacity':capacity,'elapsed_seconds':time.monotonic()-tick,'whole_native_source_of_truth':False}))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'current-leg-reference-install-checkpoint',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-leg-reference-install-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k!='capacity'})
