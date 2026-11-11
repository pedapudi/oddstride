"""Update a native derive reference and inspect real propagated geometry."""
import json,sys
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];role=sys.argv[1];phase=sys.argv[2];assert role in ['leg','head'] and phase in ['edited','restored'];baseline=json.loads((ROOT/'audits/shared-datum-baseline.json').read_text())[role]
header=(ROOT/'source/native_documents.py').read_text()+'\nimport adsk.core as core,adsk.fusion as fusion,json,time\n'+(ROOT/'source/shared_datum_inspection.py').read_text()
s=header+'''
def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,ROLE)
 if doc!=app.activeDocument:assert doc.activate()
 print(json.dumps({'active':doc.name,'up_to_date':doc.isUpToDate}))
'''.replace('ROLE',repr(role))
r=rpc(s,'activate-'+role+'-datum-'+phase,timeout=30);assert r[0]['success'],r
s=header+'''
def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,ROLE);assert doc==app.activeDocument;tick=time.monotonic();before=shared_datum_state(app,ROLE)
 d=fusion.Design.cast(app.activeProduct);feature=d.rootComponent.features.deriveFeatures.item(0);source_doc=authoring_document(app,'chassis');assert source_doc.dataFile.isComplete;assert source_doc.dataFile.isComplete
 if feature.documentReference.isOutOfDate:assert feature.documentReference.getLatestVersion()
 assert d.activateRootComponent();assert feature.setSourceEntities(feature.sourceEntities,feature.excludedEntities)
 assert d.computeAll();state=shared_datum_state(app,ROLE);assert not state['unhealthy'];expected_x=190 if PHASE=='edited' else 185;assert abs(state['parameters_mm'][('lc_hip_x' if ROLE=='leg' else 'body_hip_x')]-expected_x)<1e-7,state
 delta=5 if PHASE=='edited' else 0;worst=0
 if ROLE=='leg':
  assert len(state['frames'])==24
  for name,values in state['frames'].items():
   expected=BASELINE['frames'][name].copy();expected[3]+=(1 if name.startswith('F') else -1)*delta/10;err=max(abs(a-b) for a,b in zip(expected,values));worst=max(worst,err);assert err<1e-7,(name,err)
 else:
  assert abs(state['parameters_mm']['saddle_fastener_diametral_clearance']-(.6 if PHASE=='edited' else .4))<1e-8;assert state['fastener_probe']==(2 if PHASE=='edited' else 0)
  for key,part in state['parts'].items():
   err=max(abs((b-a)-(delta if i in [0,3] else 0)) for i,(a,b) in enumerate(zip(BASELINE['parts'][key]['bounds_mm'],part['bounds_mm'])));worst=max(worst,err);assert err<.002,(key,err)
 print(json.dumps({'passed':True,'role':ROLE,'phase':PHASE,'before_reference_update':before,'state':state,'maximum_geometry_or_pose_error':worst,'elapsed_seconds':time.monotonic()-tick,'scope':'Actual derived datum propagation and restoration. Frame rail lengths, fixed body reference placements and whole-family fit remain separate.'}))
'''.replace('ROLE',repr(role)).replace('PHASE',repr(phase)).replace('BASELINE',repr(baseline))
r=rpc(s,role+'-datum-propagation-'+phase,timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits'/f'{role}-datum-propagation-{phase}.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k not in ['before_reference_update','state']})
