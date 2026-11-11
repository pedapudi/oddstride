"""Author the equivalent lower shell with shared native body dimensions."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
assert json.loads((ROOT/'audits/compact-lower-shell-local-replay.json').read_text())['passed']
s='\n'.join((ROOT/'source'/p).read_text() for p in ['intent_geometry.py','compact_cover_intent.py','compact_lower_shell_intent.py'])+'''
def run(_context: str):
 import json,time,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:R7U8KNNBSA6o3YwVNF2ZQQ';assert doc.dataFile.versionNumber==5 and not doc.isModified;d=fusion.Design.cast(app.activeProduct);assert not any(c.partNumber=='CANDIDATE_compact_belly_center_0' for c in d.allComponents);tick=time.monotonic();occ=d.rootComponent.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Shared-datum lower body shell';c.partNumber='CANDIDATE_compact_belly_center_0';g=IntentGeometry(d,c);body=CompactLowerShellIntent(g).build();assert d.computeAll();issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues;body.material=d.materials.itemByName('PETG mass estimate (1270 kg/m3)');body.appearance=d.appearances.itemByName('Tinfox ivory');occ.isLightBulbOn=False
 for sk in c.sketches:sk.isLightBulbOn=False
 for pl in c.constructionPlanes:pl.isLightBulbOn=False
 for ax in c.constructionAxes:ax.isLightBulbOn=False
 body.name='Structural lower enclosure';path=os.path.join(tempfile.gettempdir(),'tinfox-native','compact-lower-shell-native.step');occ.isLightBulbOn=True;assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));occ.isLightBulbOn=False;assert os.path.getsize(path)>50000;print(json.dumps({'saved':False,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'volume_mm3':body.volume*1000,'path':path,'elapsed_seconds':time.monotonic()-tick,'source_shape_changed':False,'scope':'Equivalent native lower shell candidate; final native surface/sections and family edits remain.'}))
'''
r=rpc(s,'compact-lower-shell-native-build',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/compact-lower-shell-native-build.json').write_text(json.dumps(record,indent=2));print(record);fetch(record['path'],Path(record['path']).name)
