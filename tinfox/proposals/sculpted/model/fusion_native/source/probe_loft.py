"""Test a single native loft in isolation before rebuilding a complete part."""
import sys,json
from pathlib import Path
from build_part import recipe
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
key=sys.argv[1];node=int(sys.argv[2]);graph=recipe(key)
if '--flat-test' in sys.argv:
 tool=next(n for n in graph['nodes'] if n['id']==2046);points=[[-80,103.5,-210],[-80,120,-210],[-80,120,60],[-80,103.5,60]]
 tool['outerWire']['edges']=[{'kind':'line','start':a,'end':b} for a,b in zip(points,points[1:]+points[:1])]

script=(ROOT/'source/fusion_builder.py').read_text()+'''
def run(_context: str):
 import os,tempfile
 app=core.Application.get();master=next(d for d in app.documents if d.name.startswith('Tinfox - Native Master Assembly'));master.activate()
 document=app.documents.add(core.DocumentTypes.FusionDesignDocumentType);d=fusion.Design.cast(app.activeProduct);d.designType=fusion.DesignTypes.ParametricDesignType;c=d.rootComponent
 builder=Builder(d,c,KEY+'_probe',GRAPH['nodes']);body=builder.finish(NODE)
 path=os.path.join(tempfile.gettempdir(),'tinfox-native',KEY+'_node_'+str(NODE)+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c))
 d.computeAll();print(json.dumps({'path':path,'volume_mm3':body.volume*1000,'features':c.features.count,'sketches':c.sketches.count,'feature_records':[{'name':f.name,'health':int(f.healthState),'message':f.errorOrWarningMessage,'operation':int(f.operation) if hasattr(f,'operation') else None} for f in c.features]}))
 document.close(False);master.activate()
'''
for token,value in [('KEY',key),('GRAPH',graph),('NODE',node)]:script=script.replace(token,repr(value))
r=rpc(script,key+'-node-'+str(node)+'-probe');assert r[0].get('success'),r
info=json.loads(r[0]['message']);fetch(info['path'],Path(info['path']).name)
