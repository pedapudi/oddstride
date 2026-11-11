"""Build the intentional five-section shin loft before adding joint interfaces."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/n).read_text()for n in ['native_documents.py','intent_geometry.py','cohesive_limb_intent.py','rounded_shin_intent.py'])+'''
def run(_context: str):
 import json,time,tempfile,os
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert d.activateRootComponent();assert not any(c.partNumber=='CANDIDATE_round_shin_master'for c in d.allComponents);tick=time.monotonic();occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Rounded shin shared structural master';c.partNumber='CANDIDATE_round_shin_master';body=RoundedShinIntent(IntentGeometry(d,c)).loft();assert c.bRepBodies.count==1;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);path=os.path.join(tempfile.gettempdir(),'tinfox-native','rounded-shin-outer-loft.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>10000;occ.isLightBulbOn=False;print(json.dumps({'saved':False,'path':path,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'elapsed_seconds':time.monotonic()-tick,'scope':'Shared outer loft construction stage, not a finished printable shell.'}))
'''
r=rpc(s,'rounded-shin-outer-loft-native',timeout=420);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/rounded-shin-outer-loft-native.json').write_text(json.dumps(record,indent=2));print(record,flush=True);fetch(record['path'],Path(record['path']).name)
