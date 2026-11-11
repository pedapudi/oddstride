"""Drive the thigh cavity from a native linked offset of the shared outline."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text() for p in ['intent_geometry.py','cohesive_limb_intent.py','cohesive_thigh_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);c=next(o.component for o in d.rootComponent.occurrences if o.component.partNumber=='CANDIDATE_cohesive_thigh_master');assert c.features.count==3;g=IntentGeometry(d,c);body=c.bRepBodies.item(0);source=c.sketches.item(0)
 plane=g.plane(c.xZConstructionPlane,'lc_thigh_inner_y+lc_shell_wall','Thigh internal floor');sk=c.sketches.add(plane);sk.name='Structural wall from linked outer envelope';curves=[]
 ordered=[source.sketchCurves.sketchArcs.item(0)]+[source.sketchCurves.sketchControlPointSplines.item(i) for i in range(7,14)]+[source.sketchCurves.sketchArcs.item(1)]+[source.sketchCurves.sketchControlPointSplines.item(i) for i in range(7)]
 for original in ordered:
  projected=sk.project2([original],True);assert len(projected)==1,(original.objectType,original.isConstruction,len(projected));curves.append(projected[0])
 sk.isComputeDeferred=False;inp=sk.geometricConstraints.createOffsetInput(curves,g.value('-lc_shell_wall'));offset=sk.geometricConstraints.addOffset2(inp);assert offset
 for curve in curves:curve.isConstruction=True
 assert sk.profiles.count==1,sk.profiles.count;body=g.extrude(sk,'lc_thigh_width-2*lc_shell_wall','Constant wall structural cavity',fusion.FeatureOperations.CutFeatureOperation,[body]).bodies.item(0)
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-thigh-hollow.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));print(json.dumps({'part':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'source_curve_count':len(curves),'offset_expression':'-lc_shell_wall','paths':[path],'saved':False}))
'''
r=rpc(s,'cohesive-thigh-hollow',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-thigh-hollow.json').write_text(json.dumps(record,indent=2));print(record)
for path in record['paths']:fetch(path,Path(path).name)
