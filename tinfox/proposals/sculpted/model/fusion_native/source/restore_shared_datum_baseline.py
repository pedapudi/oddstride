import sys,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'source'));from run_native import rpc
header=(p/'source/native_documents.py').read_text()+'\nimport adsk.core as core,adsk.fusion as fusion,json\n'+(p/'source/shared_datum_inspection.py').read_text()
s=header+'''
def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');assert doc.activate();print(json.dumps({'active':doc.name}))
'''
r=rpc(s,'activate-chassis-datum-restoration',timeout=30);assert r[0]['success'],r
s=header+'''
def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');assert doc==app.activeDocument;d=fusion.Design.cast(app.activeProduct);d.userParameters.itemByName('robot_hip_x').expression='185 mm';d.userParameters.itemByName('robot_fastener_diametral_allowance').expression='.4 mm';assert d.computeAll();state=shared_datum_state(app,'chassis');assert not state['unhealthy'];assert state['fastener_probe']==0;assert doc.save('Restore frozen robot dimensions after the native parameter-link test: hip datum 185 mm and fastener allowance 0.4 mm. Cross-file update behavior is still under qualification.');print(json.dumps({'restored':True,'state':state,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified}))
'''
r=rpc(s,'shared-datum-source-restored',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(p/'audits/shared-datum-source-restored.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k!='state'})
