"""Advance native part references and report versions and feature health."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
SCRIPT='''import adsk.core as core,adsk.fusion as fusion,json

def run(_context: str):
 app=core.Application.get();doc=next(d for d in app.documents if d.name.startswith('Tinfox - Native Master Assembly'));doc.activate();d=fusion.Design.cast(app.activeProduct)
 def references():
  result=[]
  for group in d.rootComponent.occurrences:
   for occ in group.component.occurrences:
    if occ.isReferencedComponent:
     file=occ.documentReference.dataFile;result.append({'part':occ.component.partNumber,'version':file.versionNumber,'latest_version':file.latestVersion.versionNumber,'file_id':file.id})
  return result
 before=references();doc.updateAllReferences()
 advanced=False
 if doc.canAdvanceToLatest:advanced=doc.advanceToLatest()
 d.computeAll();after=references();health=[]
 for group in d.rootComponent.occurrences:
  for occ in group.component.occurrences:
   c=occ.component
   for feature in c.features:
    if feature.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState:health.append({'part':c.partNumber,'feature':feature.name,'message':feature.errorOrWarningMessage})
 doc.save('Refresh native part references after qualified geometry repairs; full migration gates remain open.')
 print(json.dumps({'before':before,'after':after,'feature_health_issues':health,'is_up_to_date':doc.isUpToDate,'advanced_working_changes':advanced}))
'''
r=rpc(SCRIPT,'native-reference-refresh');assert r[0].get('success'),r
record=json.loads(r[0]['message']);(ROOT/'audits/native-reference-refresh.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
