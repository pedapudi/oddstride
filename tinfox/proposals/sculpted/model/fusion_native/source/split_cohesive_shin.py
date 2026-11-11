"""Create two manufacturing components linked to the shared native shin master."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/intent_geometry.py').read_text()+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;master=next(o for o in root.occurrences if o.component.partNumber=='CANDIDATE_cohesive_shin_master');assert master.component.features.count==21;rows=[];paths=[]
 for outer in [False,True]:
  key='CANDIDATE_cohesive_shin_'+('outer' if outer else 'inner');assert not any(o.component.partNumber==key for o in root.occurrences);occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.partNumber=key;c.name='Cohesive shin '+('outer' if outer else 'inner')+' shell';g=IntentGeometry(d,c);objects=core.ObjectCollection.create();objects.add(master.component.bRepBodies.item(0));copy=c.features.copyPasteBodies.add(objects);copy.name='Linked shared structural shin';assert copy.isParametric
  body=copy.bodies.item(0);plane=g.plane(c.xZConstructionPlane,'lc_shin_split_y','Structural clamshell split');inp=c.features.splitBodyFeatures.createInput(body,plane,True);f=c.features.splitBodyFeatures.add(inp);f.name='Split structural clamshell';assert c.bRepBodies.count==2
  remove=next(b for b in c.bRepBodies if (b.boundingBox.maxPoint.y<g.mm('lc_shin_split_y')/10+1e-6)==outer);feature=c.features.removeFeatures.add(remove);feature.name='Keep '+('outboard' if outer else 'inboard')+' manufacturing half';assert c.bRepBodies.count==1;body=c.bRepBodies.item(0);body.name=c.name
  path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-shin-'+('outer' if outer else 'inner')+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));paths.append(path);rows.append({'part':key,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'native_copy_parametric':copy.isParametric,'bounds_mm':[v*10 for v in body.boundingBox.minPoint.asArray()+body.boundingBox.maxPoint.asArray()]});plane.isLightBulbOn=False
 master.isLightBulbOn=False
 print(json.dumps({'parts':rows,'paths':paths,'saved':False,'source_of_truth_changed':False}))
'''
r=rpc(s,'cohesive-shin-shell-splits',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-shin-shell-splits.json').write_text(json.dumps(record,indent=2))
for p in record['paths']:fetch(p,Path(p).name)
print(record)
