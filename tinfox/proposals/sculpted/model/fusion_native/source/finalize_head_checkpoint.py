"""Name and color the qualified native Head geometry; retain export/release blockers."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
assert json.loads((ROOT/'audits/nose-direct-native-section-comparison.json').read_text())['passed']
assert json.loads((ROOT/'audits/head-family-edit-restore.json').read_text())['passed']
assert json.loads((ROOT/'audits/head-silhouettes.json').read_text())['passed']
script='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;rows=[]
 for occ in root.occurrences:
  c=occ.component;key=c.partNumber.replace('CANDIDATE_','');assert key in ['sensor_bezel','front_fascia','body_nose_surround'];c.partNumber=key;c.name={'sensor_bezel':'Sensor bezel','front_fascia':'Compound front fascia','body_nose_surround':'Front shoulder bridge'}[key]
  assert c.bRepBodies.count==1;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features)
  appearance=d.appearances.itemByName('Tinfox '+('glass' if key=='sensor_bezel' else 'ivory'));assert appearance
  c.appearance=appearance;c.bRepBodies.item(0).appearance=appearance;occ.isLightBulbOn=True;c.bRepBodies.item(0).isLightBulbOn=True
  c.attributes.add('Tinfox','NativeGeometryStatus','Native shape, five Head family edits, external silhouettes, and sampled interface/removal comparisons passed. Nose disputed section independently verified inside Fusion.')
  c.attributes.add('Tinfox','ReleaseBlockers','STEP nose planar trim self-consistency remains unresolved. Frozen fascia/bezel overlap retained. No manufacturing release or whole-robot source-of-truth promotion.')
  rows.append({'id':key,'name':c.name,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'faces':c.bRepBodies.item(0).faces.count,'edges':c.bRepBodies.item(0).edges.count,'linked':occ.isReferencedComponent})
 folder=os.path.join(tempfile.gettempdir(),'tinfox-native');path=os.path.join(folder,'Tinfox-Head-native-checkpoint.f3d');assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path))
 app.activeViewport.refresh();png=os.path.join(folder,'Tinfox-Head-native-checkpoint.png');assert app.activeViewport.saveAsImageFile(png,1800,1100)
 before=doc.dataFile.versionNumber;assert doc.save('Name compact native Head components and apply shared appearance. Direct native section and five parameter edits verified; export consistency and source overlap remain release blockers.')
 print(json.dumps({'previous_version':before,'save_requested':True,'parts':rows,'editable_files':len(app.data.personalUseLimits.editableFiles),'paths':[path,png],'source_of_truth_changed':False,'manufacturing_ready':False}))
'''
r=rpc(script,'head-native-final-checkpoint',timeout=120);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/head-native-final-checkpoint.json').write_text(json.dumps(record,indent=2))
for path in record['paths']:fetch(path,Path(path).name)
print(json.dumps(record))
