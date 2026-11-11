"""Read Fusion's editable-file inventory without changing document status."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]

def known_files():
    manifest=json.loads((ROOT/'manifests/parts.json').read_text());project=manifest['fusion_project']['id'];registry=json.loads((ROOT/'manifests/native-files.json').read_text())
    result={manifest['fusion_document']['id']:{'part':'native_master','project_id':project,'completed_saved_candidate':False}}
    # These standalone documents were saved once and are not being replaced.
    complete={'battery_cassette','foot','shin_inner'}
    for key,row in registry.items():result[row['file_id']]={'part':key,'project_id':project,'completed_saved_candidate':key in complete}
    subsystems=ROOT/'manifests/subsystems.json'
    if subsystems.exists():
        for key,row in json.loads(subsystems.read_text()).get('subsystems',{}).items():
            result[row['file_id']]={'part':'subsystem_'+key,'project_id':project,'completed_saved_candidate':False}
    proof=ROOT/'audits/native-part-document-proof.json'
    if proof.exists():
        data=json.loads(proof.read_text())
        if data.get('passed'):result[data['file_id']]={'part':'stator_native_validation_copy','project_id':project,'completed_saved_candidate':True}
    return result

def script_header():return (ROOT/'source/personal_plan_guard.py').read_text()

def inspect():
    known=known_files();script=script_header()+'''

def run(_context: str):
 import adsk.core as core
 app=core.Application.get()
 print(json.dumps(personal_plan_inventory(app,KNOWN,PROTECTED)))
'''
    master=json.loads((ROOT/'manifests/parts.json').read_text())['fusion_document']['id']
    script=script.replace('KNOWN',repr(known)).replace('PROTECTED',repr([master]))
    response=rpc(script,'personal-plan-preflight',timeout=30,read_only=True)
    assert response[0].get('success'),response
    result=json.loads(response[0]['message']);(ROOT/'audits/personal-plan-live-inventory.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':inspect()
