"""Link the revised crank and repair a broken generated foot mirror."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;rows=[];paths=[]
 for source_key,key,name in [('CANDIDATE_input_crank','CANDIDATE_input_crank_right','Right integrated knee drive crank'),('foot','CANDIDATE_foot_right','Right compliant foot')]:
  assert not any(o.component.partNumber==key for o in root.occurrences);source_occ=next(o for o in root.occurrences if o.component.partNumber==source_key);source=source_occ.component;occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.partNumber=key;c.name=name;objects=core.ObjectCollection.create()
  for b in source.bRepBodies:objects.add(b.createForAssemblyContext(source_occ))
  copy=c.features.copyPasteBodies.add(objects);copy.name='Linked canonical native geometry';originals=list(c.bRepBodies);objects=core.ObjectCollection.create()
  for b in originals:objects.add(b)
  inp=c.features.mirrorFeatures.createInput(objects,c.xZConstructionPlane);inp.isCombine=False;c.features.mirrorFeatures.add(inp).name='Right-hand reflection'
  for b in originals:c.features.removeFeatures.add(b).name='Keep handed solid'
  assert d.computeAll();assert c.bRepBodies.count==1;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);row={'part':key,'features':c.features.count,'source':source_key,'source_external':source_occ.isReferencedComponent}
  if source_key=='foot':
   old=next(o for o in root.occurrences if o.component.partNumber=='foot_right');a=old.component.bRepBodies.item(0);b=c.bRepBodies.item(0);assert abs(a.volume-b.volume)<1e-7;assert a.boundingBox.minPoint.distanceTo(b.boundingBox.minPoint)<1e-7;assert a.boundingBox.maxPoint.distanceTo(b.boundingBox.maxPoint)<1e-7;row['retired_failed_component']=old.name;assert old.deleteMe();c.partNumber='foot_right';row['part']=c.partNumber
  path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-input-crank-right.step' if source_key!='foot' else 'foot-right-repaired.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));paths.append(path);rows.append(row)
 p=d.userParameters.itemByName('lc_crank_radius');old=p.expression;c=next(o.component for o in root.occurrences if o.component.partNumber=='CANDIDATE_input_crank_right');baseline=c.bRepBodies.item(0).volume
 try:p.expression='29 mm';assert d.computeAll();assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);assert abs(c.bRepBodies.item(0).volume-baseline)>1e-5
 finally:p.expression=old;assert d.computeAll()
 assert abs(c.bRepBodies.item(0).volume-baseline)<1e-7
 print(json.dumps({'parts':rows,'paths':paths,'handed_crank_edit_restored':True,'saved':False}))
'''
r=rpc(s,'cohesive-input-crank-handed-foot-repair',timeout=240);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-input-crank-handed-foot-repair.json').write_text(json.dumps(record,indent=2));print(record)
for path in record['paths']:fetch(path,Path(path).name)
