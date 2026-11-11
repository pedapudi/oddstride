"""Preserve the bridge's intended flat and rounded perimeter patches."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
script='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile
def run(_context: str):
 app=core.Application.get();assert app.activeDocument.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);occ=next(o for o in d.rootComponent.occurrences if o.component.partNumber=='CANDIDATE_body_nose_surround');c=occ.component;feature=next(f for f in c.features if f.name=='Continuous mounting bridge');feature.timelineObject.rollTo(True);feature.isTangentEdgesMerged=False;d.timeline.moveToEnd();assert d.computeAll();issues=[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues
 occ.isLightBulbOn=True;body=c.bRepBodies.item(0);body.isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','body_nose_surround-patched.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));occ.isLightBulbOn=False;print(json.dumps({'path':path,'faces':body.faces.count,'edges':body.edges.count,'volume':body.volume*1000,'saved':False}))
'''
r=rpc(script,'nose-bridge-edge-matching',timeout=120);assert r[0]['success'],r;record=json.loads(r[0]['message']);fetch(record['path'],Path(record['path']).name);print(json.dumps(record))
