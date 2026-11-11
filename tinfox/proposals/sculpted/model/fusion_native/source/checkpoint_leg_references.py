"""Save qualified reference placements in the existing native Leg document."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
assert json.loads((ROOT/'audits/native-leg-reference-qualification.json').read_text())['passed']
s=script_header()+'''
import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,time

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);groups=[c for c in d.allComponents if c.partNumber.startswith('REFERENCE_')];assert len(groups)==24;assert all(j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for c in d.allComponents for j in c.joints);before=doc.dataFile.versionNumber;tick=time.monotonic();assert doc.save('Add 248 purchased hardware/vendor reference instances to the 24 native leg frames; verify source geometry and eight driven pose placements. Custom histories and prior fit parameters retained.');path=os.path.join(tempfile.gettempdir(),'tinfox-native','Tinfox-Leg-native-hardware-assembly.f3d');assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path));print(json.dumps({'save_requested':True,'previous_version':before,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'path':path,'reference_groups':24,'reference_instances':248,'capacity':capacity,'elapsed_seconds':time.monotonic()-tick}))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'leg-hardware-checkpoint',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/leg-hardware-checkpoint.json').write_text(json.dumps(record,indent=2));print(record);fetch(record['path'],Path(record['path']).name)
