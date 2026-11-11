"""Capture the final restored geometry after shared and handed edit tests."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);paths=[];parts=[]
 for occ in d.rootComponent.occurrences:
  c=occ.component
  if not c.partNumber.startswith('CANDIDATE_cohesive_shin_'):continue
  suffix=c.partNumber.replace('CANDIDATE_cohesive_shin_','').replace('_','-');label='cohesive-shin-'+suffix+'-final';occ.isLightBulbOn=True;c.bRepBodies.item(0).isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native',label+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));paths.append(path);parts.append({'part':c.partNumber,'file':label+'.step','features':c.features.count,'sketches':c.sketches.count})
  if suffix=='master':occ.isLightBulbOn=False
 material=d.rootComponent.material;properties=[{'id':p.id,'name':p.name,'type':p.objectType,'value':getattr(p,'value',None),'units':getattr(p,'units',None)} for p in material.materialProperties if 'dens' in p.name.lower() or 'dens' in p.id.lower()];libraries=[{'name':lib.name,'id':lib.id,'matching_materials':[m.name for m in lib.materials if 'pet' in m.name.lower() or 'generic' in m.name.lower()]} for lib in app.materialLibraries]
 print(json.dumps({'paths':paths,'parts':parts,'material':material.name,'density_properties':properties,'material_libraries':libraries,'saved':False}))
'''
r=rpc(s,'cohesive-shin-final-geometry',timeout=120);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-shin-final-geometry.json').write_text(json.dumps(record,indent=2))
for p in record['paths']:fetch(p,Path(p).name)
print(record)
