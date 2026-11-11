import sys,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'source'));from run_native import rpc
header=(p/'source/native_documents.py').read_text()+'\nimport adsk.core as core,adsk.fusion as fusion,json\n'+(p/'source/shared_datum_inspection.py').read_text()
s=header+'''
def run(_context: str):
 app=core.Application.get();print(json.dumps({role:shared_datum_state(app,role) for role in ['chassis','leg','head']}))
'''
r=rpc(s,'shared-datum-baseline',timeout=60,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);(p/'audits/shared-datum-baseline.json').write_text(json.dumps(record,indent=2))
s=header+'''
def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');assert not doc.isModified;assert doc.activate();print(json.dumps({'active':doc.name}))
'''
r=rpc(s,'activate-chassis-datum-test',timeout=30);assert r[0]['success'],r
s=header+'''
def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');assert doc==app.activeDocument;d=fusion.Design.cast(app.activeProduct);d.userParameters.itemByName('robot_hip_x').expression='190 mm';d.userParameters.itemByName('robot_fastener_diametral_allowance').expression='.6 mm';assert d.computeAll();state={role:shared_datum_state(app,role) for role in ['chassis','leg','head']};assert not state['chassis']['unhealthy'];print(json.dumps(state))
'''
r=rpc(s,'shared-datum-source-edit',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(p/'audits/shared-datum-source-edit.json').write_text(json.dumps(record,indent=2));print({role:{key:value for key,value in state.items() if key not in ['parts','frames','derived_parameters_mm']} for role,state in record.items()})
