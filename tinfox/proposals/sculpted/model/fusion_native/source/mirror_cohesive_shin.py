"""Create native handed shin occurrences and prove their dimensional dependency."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;rows=[];paths=[]
 for side in ['inner','outer']:
  source=next(o.component for o in root.occurrences if o.component.partNumber=='CANDIDATE_cohesive_shin_'+side);key=source.partNumber+'_right';assert not any(o.component.partNumber==key for o in root.occurrences);occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.partNumber=key;c.name='Right shin '+side+' shell';objects=core.ObjectCollection.create();objects.add(source.bRepBodies.item(0));copy=c.features.copyPasteBodies.add(objects);copy.name='Linked left-hand manufacturing shell';assert copy.isParametric;original=copy.bodies.item(0)
  objects=core.ObjectCollection.create();objects.add(original);inp=c.features.mirrorFeatures.createInput(objects,c.xZConstructionPlane);inp.isCombine=False;f=c.features.mirrorFeatures.add(inp);f.name='Right-hand reflection';assert c.bRepBodies.count==2;c.features.removeFeatures.add(original).name='Keep right-hand manufacturing shell';assert c.bRepBodies.count==1;rows.append({'part':key,'features':c.features.count,'sketches':c.sketches.count,'source':source.partNumber,'native_link':copy.isParametric})
 targets=[o for o in root.occurrences if o.component.partNumber.startswith('CANDIDATE_cohesive_shin_')];p=d.userParameters.itemByName('lc_shank_foot_center');old=p.expression
 try:
  p.expression='149 mm';assert d.computeAll();response={o.component.partNumber:o.component.bRepBodies.item(0).boundingBox.minPoint.z*10 for o in targets};assert all(abs(z+137)<.002 for z in response.values()),response
 finally:p.expression=old;assert d.computeAll()
 for occ in targets:
  c=occ.component;assert c.bRepBodies.count==1 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);assert abs(c.bRepBodies.item(0).boundingBox.minPoint.z*10+136)<.002
  if not c.partNumber.endswith('_right'):continue
  label=c.partNumber.replace('CANDIDATE_cohesive_shin_','cohesive-shin-').replace('_','-');path=os.path.join(tempfile.gettempdir(),'tinfox-native',label+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));paths.append(path)
 print(json.dumps({'parts':rows,'one_mm_length_edit_response':response,'restore_passed':True,'paths':paths,'saved':False}))
'''
r=rpc(s,'cohesive-shin-handed-parts',timeout=240);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-shin-handed-parts.json').write_text(json.dumps(record,indent=2))
for p in record['paths']:fetch(p,Path(p).name)
print(record)
