"""Build the current 28 mm crank with native functional primitives and patterns."""
import ast,hashlib,json,shutil
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1];MODEL=ROOT.parent
for file,function in [('integrated_candidate.py','input_crank'),('build.py','pivot_ears')]:
 def node(path):return next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==function)
 assert ast.dump(node(MODEL/file))==ast.dump(node(ROOT/'snapshots/cohesive-limb/source'/file))
source=MODEL/'output/integrated-candidate/step/input_crank.step';target=ROOT/'snapshots/cohesive-limb/step/input_crank.step'
if not target.exists():shutil.copyfile(source,target)
record={'source_step_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'scope':'Current input crank: constructor and pivot-ear ASTs equal the frozen cohesive source snapshot.','source_model_sha256':'7a30dd8d92258b011e043f6fb43992ff9ac718232dd030ec2a7c79b33f68d63a'};(ROOT/'snapshots/cohesive-limb/input-crank-reference.json').write_text(json.dumps(record,indent=2))
s='\n'.join((ROOT/'source'/p).read_text() for p in ['intent_geometry.py','cohesive_limb_intent.py','cohesive_crank_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert not any(o.component.partNumber=='CANDIDATE_input_crank' for o in root.occurrences);occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.partNumber='CANDIDATE_input_crank';c.name='Integrated knee drive crank';g=IntentGeometry(d,c);n=CohesiveCrankIntent(g);body=n.interfaces(n.blank());health=[{'feature':f.name,'state':str(f.healthState),'message':f.errorOrWarningMessage} for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-input-crank.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));print(json.dumps({'part':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'faces':body.faces.count,'edges':body.edges.count,'paths':[path],'saved':False,'unhealthy':health}))
'''
r=rpc(s,'cohesive-input-crank',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-input-crank.json').write_text(json.dumps(record,indent=2));print(record)
for path in record['paths']:fetch(path,Path(path).name)
