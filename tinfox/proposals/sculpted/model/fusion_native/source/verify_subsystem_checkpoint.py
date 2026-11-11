"""Read saved state from the original subsystem, excluding assembly contexts."""
import json,sys,datetime
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
role=sys.argv[1];assert role in ['chassis','head','leg']
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,ROLE);d=fusion.Design.cast(doc.products.itemByProductType('DesignProductType'));rows=[]
 for c in d.allComponents:rows.append({'part':c.partNumber,'name':c.name,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'unhealthy':[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]})
 print(json.dumps({'name':doc.name,'file_id':doc.dataFile.id,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'read_only':doc.dataFile.isReadOnly,'editable_files':len(app.data.personalUseLimits.editableFiles),'parts':rows}))
'''.replace('ROLE',repr(role))
r=rpc(s,role+'-checkpoint-verification',timeout=30,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);assert record['complete'] and not record['modified'] and not record['read_only'];assert not any(p['unhealthy'] for p in record['parts']);assert not any(p['part'].startswith('CANDIDATE_') for p in record['parts']);record['verified_utc']=datetime.datetime.now(datetime.UTC).isoformat();(ROOT/'audits'/f"{role}-v{record['version']}-save-verification.json").write_text(json.dumps(record,indent=2));subs=json.loads((ROOT/'manifests/subsystems.json').read_text());subs['subsystems'][role].update(version=record['version'],save_verified=True,verification_report=f"audits/{role}-v{record['version']}-save-verification.json");(ROOT/'manifests/subsystems.json').write_text(json.dumps(subs,indent=2));print({k:v for k,v in record.items() if k!='parts'})
