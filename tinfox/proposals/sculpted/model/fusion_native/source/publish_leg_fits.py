"""Save the qualified native four-leg hierarchy in the existing subsystem file."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
assert all(json.loads((ROOT/'audits'/name).read_text())['passed'] for name in ['native-leg-assembly-qualification.json','native-leg-fit-qualification.json','native-leg-fit-stacks.json'])
s=script_header()+'''
import adsk.core as core,adsk.fusion as fusion
def run(_context: str):
 import json,os,tempfile,time
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);root=d.rootComponent;parts=[];joints=[]
 for leg in root.occurrences:
  if not leg.component.partNumber.startswith('ASSEMBLY_'):continue
  for j in leg.component.joints:assert j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState;joints.append(j.name)
  for frame in leg.childOccurrences:
   if frame.component.attributes.itemByName('Tinfox','KinematicFrame'):
    for part in frame.childOccurrences:parts.append({'key':part.component.partNumber,'path':part.fullPathName,'source':part.attributes.itemByName('Tinfox','SourceInstance').value})
 assert len(parts)==80 and len(joints)==24;before=doc.dataFile.versionNumber;tick=time.monotonic();assert doc.save('Bind hardware fits, process-specific compensation, symmetric seam relief and worst-case stack parameters; edit/restore audits preserve reference geometry');path=os.path.join(tempfile.gettempdir(),'tinfox-native','Tinfox-Leg-native-fit-assembly.f3d');assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path));print(json.dumps({'save_requested':True,'previous_version':before,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'path':path,'parts':parts,'joints':joints,'capacity':capacity,'elapsed_seconds':time.monotonic()-tick}))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'native-leg-fit-publication',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/native-leg-fit-publication.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k not in ['parts','joints']});fetch(record['path'],Path(record['path']).name)
