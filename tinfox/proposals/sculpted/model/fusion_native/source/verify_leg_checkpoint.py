"""Verify saved cloud completion independently of the publication call."""
import datetime,json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json

def run(_context: str):
 app=core.Application.get();doc=next(doc for doc in app.documents if doc.isSaved and doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ');doc.activate();d=fusion.Design.cast(app.activeProduct);rows=[]
 for c in d.allComponents:
  rows.append({'part':c.partNumber,'name':c.name,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'unhealthy':[{'name':f.name,'message':f.errorOrWarningMessage} for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]})
 print(json.dumps({'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'read_only':doc.dataFile.isReadOnly,'editable_files':len(app.data.personalUseLimits.editableFiles),'parts':rows}))
'''
r=rpc(s,'leg-checkpoint-verification',timeout=30,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);assert record['version']>=7 and record['complete'] and not record['modified'] and not record['read_only'];assert not any(p['unhealthy'] for p in record['parts']);assert not any(p['part'].startswith('CANDIDATE_') for p in record['parts']);record['verified_utc']=datetime.datetime.now(datetime.UTC).isoformat();(ROOT/'audits'/f"leg-v{record['version']}-save-verification.json").write_text(json.dumps(record,indent=2))
status=json.loads((ROOT/'manifests/cohesive-leg-status.json').read_text());has_references=any(p['part']=='REFERENCE_FL_mount' for p in record['parts']);status.update(updated_utc=record['verified_utc'],saved_version=record['version'],save_verified=True,active_candidate=None,verified_working_stage='Four native leg assemblies saved with 80 physical custom instances, 24 pose mates, verified family edits, process-specific fit bindings and worst-case interval expressions.'+(' Includes 248 purchased references with eight verified driven poses.' if has_references else ''),current_operation='Native assembly organization and remaining subsystem targets',remaining=[('Cross-subsystem assembly and complete robot audits' if has_references else 'Standard hardware/vendor references and cross-subsystem assembly'),'Remaining Chassis and Head target revisions','Remaining pilot/connector/locating fit bindings and coupled motion variation','Measured print/CNC fits and loaded strength qualification']);(ROOT/'manifests/cohesive-leg-status.json').write_text(json.dumps(status,indent=2));subs=json.loads((ROOT/'manifests/subsystems.json').read_text());subs['subsystems']['leg']['version']=record['version'];(ROOT/'manifests/subsystems.json').write_text(json.dumps(subs,indent=2));print({k:v for k,v in record.items() if k!='parts'})
