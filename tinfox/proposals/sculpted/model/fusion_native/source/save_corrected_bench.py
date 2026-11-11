"""Save clean visibility after direct exports, preserving a pending assembly release."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);bench=next(o for o in root.occurrences if o.component.partNumber=='BENCH_MOTOR_COMPLEX')
 for o in root.occurrences:o.isLightBulbOn=(o==bench)
 visible=[]
 def walk(o):
  o.isLightBulbOn=True
  for b in o.component.bRepBodies:
   b.isLightBulbOn=True;p=b.createForAssemblyContext(o);assert p.isVisible;visible.append(o.fullPathName+' / '+b.name)
  for child in o.component.occurrences:walk(child.createForAssemblyContext(o))
 walk(bench);assert len(visible)==121
 bench.component.name='Motor complex - corrected native assembly';bench.component.attributes.add('Tinfox','AssemblyReleaseReady','false');bench.component.attributes.add('Tinfox','KnownDesignLimitation','Corrected geometry and references; independent broad static screen and final reopen verification pending. Unpowered fit scope only.');before=doc.dataFile.versionNumber
 assert doc.save('Corrected native motor complex: nine knee countersinks, reinforced recessed closure and matched cups, motor-case hub relief, seated hip/roll countersunk references. 121 bodies; all custom histories preserved. Direct exports retained from geometry checkpoint23; independent full static screen and final saved verification pending.')
 print(json.dumps({'previous_version':before,'version_at_return':doc.dataFile.versionNumber,'complete_at_return':doc.dataFile.isComplete,'modified_at_return':doc.isModified,'visible_bodies':len(visible),'capacity':capacity,'assembly_release_ready':False}))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'corrected-bench-final-checkpoint',timeout=240);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/corrected-bench-final-checkpoint.json').write_text(json.dumps(record,indent=2));print(record)
