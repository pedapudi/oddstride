"""Verify regeneration of an authored native F3D archive in an isolated document."""
import json,sys
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];key=sys.argv[1]
script='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
 app=core.Application.get();master=next(d for d in app.documents if d.name.startswith('Tinfox - Native Master Assembly'));master.activate()
 path=os.path.join(tempfile.gettempdir(),'tinfox-native',KEY+'.f3d');options=app.importManager.createFusionArchiveImportOptions(path);document=app.importManager.importToNewDocument(options);document.activate();d=fusion.Design.cast(app.activeProduct);c=d.rootComponent
 before=sum(b.volume for b in c.bRepBodies)*1000;d.computeAll();after=sum(b.volume for b in c.bRepBodies)*1000
 issues=[{'feature':f.name,'message':f.errorOrWarningMessage} for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]
 result={'part':KEY,'sketches':c.sketches.count,'features':c.features.count,'before_volume_mm3':before,'after_volume_mm3':after,'health_issues':issues,'passed':not issues and abs(after-before)/max(before,1)<1e-6}
 document.close(False);master.activate();print(json.dumps(result))
'''.replace('KEY',repr(key))
r=rpc(script,key+'-native-archive-regeneration');assert r[0].get('success'),r
record=json.loads(r[0]['message']);(ROOT/'audits'/f'{key}-regeneration.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
