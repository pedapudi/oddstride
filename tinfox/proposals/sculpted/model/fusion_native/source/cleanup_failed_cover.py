"""Remove only the verified failed, unsaved compact-cover construction."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:R7U8KNNBSA6o3YwVNF2ZQQ' and doc.dataFile.versionNumber==3;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;matches=[o for o in root.occurrences if o.component.partNumber=='CANDIDATE_current_body_center_0'];assert len(matches)==1;occ=matches[0];c=occ.component;record={'name':c.name,'part':c.partNumber,'features':[{'name':f.name,'health':int(f.healthState),'message':f.errorOrWarningMessage} for f in c.features],'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'saved':False,'reason':'Failed native revolve-axis sketch in the sole compact cover candidate. No cloud publication.'}
 def signature(comp):return {'features':comp.features.count,'sketches':comp.sketches.count,'bodies':comp.bRepBodies.count,'volumes':[b.volume for b in comp.bRepBodies]}
 before={o.component.partNumber:signature(o.component) for o in root.occurrences if o!=occ};assert occ.deleteMe();removed=[]
 while True:
  eligible=[p for p in d.userParameters if p.name.startswith('cover_') and p.isDeletable]
  if not eligible:break
  for p in eligible:removed.append(p.name);assert p.deleteMe()
 after={o.component.partNumber:signature(o.component) for o in root.occurrences};assert before==after;assert not any(comp.partNumber=='CANDIDATE_current_body_center_0' for comp in d.allComponents);print(json.dumps({'removed':record,'removed_unused_parameters':removed,'unrelated_parts_unchanged':len(before),'remaining_failed_candidates':0,'saved':False,'passed':True}))
'''
r=rpc(s,'failed-compact-cover-cleanup',timeout=60);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/failed-compact-cover-cleanup.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k not in ['removed','removed_unused_parameters']})
