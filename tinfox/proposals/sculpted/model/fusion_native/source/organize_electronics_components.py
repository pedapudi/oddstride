"""Move the three chassis-mounted electronics parts into the Chassis design.

The source master stays intact. Native feature archives carry histories between
subsystem copies; the Head copy loses its duplicates only after Chassis saves.
"""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'manifests/subsystems.json').read_text())
script='''import adsk,adsk.core as core,adsk.fusion as fusion,json,tempfile,os,time

def run(_context: str):
 app=core.Application.get();master=next(d for d in app.documents if d.name.startswith('Tinfox - Native Master Assembly'));assert not master.isModified
 def activate(file_id):
  doc=next((d for d in app.documents if d.isSaved and d.dataFile.id==file_id),None)
  if doc is None:doc=app.documents.open(app.data.findFileById(file_id),True)
  else:doc.activate()
  assert not doc.dataFile.isReadOnly and not doc.isModified
  return doc,fusion.Design.cast(app.activeProduct)
 def inventory(c):return {'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'volume_mm3':sum(b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume for b in c.bRepBodies)*1000,'base_features':sum('BaseFeature' in f.objectType for f in c.features),'mesh_bodies':c.meshBodies.count}
 def save(doc,message):
  version=doc.dataFile.versionNumber;assert doc.save(message);deadline=time.monotonic()+90
  while (doc.isModified or doc.dataFile.versionNumber<=version or not doc.dataFile.isComplete) and time.monotonic()<deadline:adsk.doEvents();time.sleep(.1)
  assert not doc.isModified and doc.dataFile.versionNumber>version and doc.dataFile.isComplete
 keys=['electronics_shelf','lidar_lid','power_button'];head,hd=activate(HEAD_ID);source={};paths={}
 for key in keys:
  matches=[o for o in hd.rootComponent.occurrences if o.component.partNumber==key];assert len(matches)==1,key;c=matches[0].component;source[key]=inventory(c)
  path=os.path.join(tempfile.gettempdir(),'tinfox-native',key+'-native-component.f3d');assert hd.exportManager.execute(hd.exportManager.createFusionArchiveExportOptions(path,c));paths[key]=path
 chassis,cd=activate(CHASSIS_ID);records=[]
 for key in keys:
  assert not any(o.component.partNumber==key for o in cd.rootComponent.occurrences),key
  assert app.importManager.importToTarget2(app.importManager.createFusionArchiveImportOptions(paths[key]),cd.rootComponent) is not None
  matches=[o for o in cd.rootComponent.occurrences if o.component.partNumber==key];assert len(matches)==1,key;c=matches[0].component;actual=inventory(c);expected=source[key]
  for field in ['features','sketches','bodies','base_features','mesh_bodies']:assert expected[field]==actual[field],(key,expected,actual)
  assert abs(expected['volume_mm3']-actual['volume_mm3'])<.001,(key,expected,actual)
  assert not matches[0].isReferencedComponent
  records.append({'part':key,'before':expected,'after':actual,'passed':True})
 cd.computeAll();save(chassis,'Group chassis-mounted electronics with the native Chassis components.')
 head.activate()
 for key in keys:
  occurrence=next(o for o in hd.rootComponent.occurrences if o.component.partNumber==key);assert occurrence.deleteMe()
 save(head,'Remove chassis electronics duplicates after verified native transfer to Chassis.')
 assert not master.isModified
 print(json.dumps({'parts':records,'chassis_version':chassis.dataFile.versionNumber,'head_version':head.dataFile.versionNumber,'chassis_part_ids':[o.component.partNumber for o in cd.rootComponent.occurrences],'head_part_ids':[o.component.partNumber for o in hd.rootComponent.occurrences],'source_master_modified':master.isModified,'passed':True}))
'''.replace('HEAD_ID',repr(manifest['subsystems']['head']['file_id'])).replace('CHASSIS_ID',repr(manifest['subsystems']['chassis']['file_id']))
r=rpc(script,'organize-electronics-components',timeout=300);assert r[0].get('success'),r
record=json.loads(r[0]['message']);(ROOT/'audits/organize-electronics-components.json').write_text(json.dumps(record,indent=2));manifest=json.loads((ROOT/'manifests/subsystems.json').read_text())
for role in ['chassis','head']:manifest['subsystems'][role].update(version=record[role+'_version'],part_ids=record[role+'_part_ids'])
(ROOT/'manifests/subsystems.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(record,indent=2))
