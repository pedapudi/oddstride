"""Inventory the current cover's actual editable dimensions and feature owners."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:R7U8KNNBSA6o3YwVNF2ZQQ';d=fusion.Design.cast(app.activeProduct);c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_current_body_center_0');rows=[]
 for p in c.modelParameters:
  owner=p.createdBy;rows.append({'name':p.name,'expression':p.expression,'owner_name':owner.name if hasattr(owner,'name') else None,'owner_type':owner.objectType,'role':p.role})
 print(json.dumps({'parameters':rows,'features':[{'name':f.name,'type':f.objectType} for f in c.features],'planes':[{'name':p.name,'expression':p.definition.offset.expression if isinstance(p.definition,fusion.ConstructionPlaneOffsetDefinition) else None} for p in c.constructionPlanes]}))
'''
r=rpc(s,'current-cover-parameter-inventory',timeout=30,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-cover-parameter-inventory.json').write_text(json.dumps(record,indent=2));print({'model_parameters':len(record['parameters']),'features':len(record['features'])})
