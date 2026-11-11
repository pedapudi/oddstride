"""Locate the first native/replayed geometry divergence in an isolated document."""
import json,sys
from pathlib import Path
from build_part import recipe
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
def diagnose(key):
 graph=recipe(key);expected=json.loads((ROOT/'audits'/f'{key}-recipe-replay.json').read_text())['nodes']
 script=(ROOT/'source/fusion_builder.py').read_text()+'''
def run(_context: str):
    app=core.Application.get();master=next(d for d in app.documents if d.name.startswith('Tinfox - Native Master Assembly'));master.activate()
    scratch=app.documents.add(core.DocumentTypes.FusionDesignDocumentType)
    d=fusion.Design.cast(app.activeProduct);d.designType=fusion.DesignTypes.ParametricDesignType
    c=d.rootComponent;c.partNumber=KEY
    builder=Builder(d,c,KEY,GRAPH['nodes']);builder.expected_nodes=EXPECTED;builder.diagnostic_tolerance=.0002
    started=time.perf_counter();mismatch=None
    try:builder.finish(GRAPH['root'])
    except DiagnosticMismatch as error:mismatch=json.loads(str(error))
    result={'part':KEY,'diagnostic_passed':mismatch is None,'first_mismatch':mismatch,'elapsed_seconds':time.perf_counter()-started,'trace':builder.diagnostic_trace,'slowest_native_features':sorted(builder.timings,key=lambda row:row['seconds_since_previous_feature'],reverse=True)[:15],'scope':'Isolated diagnostic only; no part was added to the native master.'}
    scratch.close(False);master.activate();print(json.dumps(result))
'''
 for token,value in [('KEY',key),('GRAPH',graph),('EXPECTED',expected)]:script=script.replace(token,repr(value))
 result=rpc(script,key+'-diagnostic')
 if not result[0].get('success',True):return False
 record=json.loads(result[0]['message']);(ROOT/'audits'/f'{key}-diagnostic.json').write_text(json.dumps(record,indent=2));print(json.dumps({k:v for k,v in record.items() if k!='trace'},indent=2));return record['diagnostic_passed']
if __name__=='__main__':diagnose(sys.argv[1])
