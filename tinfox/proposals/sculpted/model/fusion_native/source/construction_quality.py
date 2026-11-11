"""Inventory native construction complexity and dimensional dependencies."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
subsystems=json.loads((ROOT/'manifests/subsystems.json').read_text())['subsystems']
script='''import adsk.core as core,adsk.fusion as fusion,json,collections,re

def run(_context: str):
 app=core.Application.get();active=app.activeDocument;result={}
 for role,file_id in FILES.items():
  doc=next(d for d in app.documents if d.isSaved and d.dataFile.id==file_id);doc.activate();design=fusion.Design.cast(app.activeProduct);parts=[]
  for c in design.allComponents:
   if not c.partNumber or not c.bRepBodies.count:continue
   sketches=[]
   for s in c.sketches:
    curves=s.sketchCurves
    sketches.append({'name':s.name,'entities':curves.count,'lines':curves.sketchLines.count,'arcs':curves.sketchArcs.count,'circles':curves.sketchCircles.count,'fitted_splines':curves.sketchFittedSplines.count,'fitted_spline_points':sum(x.fitPoints.count for x in curves.sketchFittedSplines),'control_point_splines':curves.sketchControlPointSplines.count,'dimensions':s.sketchDimensions.count,'constraints':s.geometricConstraints.count})
   parts.append({'part':c.partNumber,'name':c.name,'feature_count':c.features.count,'feature_types':dict(collections.Counter(f.objectType.split('::')[-1] for f in c.features)),'sketch_count':c.sketches.count,'sketch_entities':sum(s['entities'] for s in sketches),'fitted_spline_points':sum(s['fitted_spline_points'] for s in sketches),'dimension_count':sum(s['dimensions'] for s in sketches),'body_count':c.bRepBodies.count,'faces':sum(b.faces.count for b in c.bRepBodies),'edges':sum(b.edges.count for b in c.bRepBodies),'sketches':sketches})
  params=[{'name':p.name,'expression':p.expression,'units':p.unit} for p in design.userParameters]
  names={p['name'] for p in params};linked=[p for p in params if any(token in names for token in re.findall(r'[A-Za-z_][A-Za-z_0-9]*',p['expression']))]
  result[role]={'file_id':file_id,'version':doc.dataFile.versionNumber,'parts':parts,'user_parameter_count':len(params),'user_parameters_with_parameter_dependencies':len(linked),'independent_user_parameter_count':len(params)-len(linked),'parameterization_gate_passed':False}
 active.activate();print(json.dumps(result))
'''.replace('FILES',repr({k:v['file_id'] for k,v in subsystems.items()}))
r=rpc(script,'construction-quality-inventory',timeout=120,read_only=True);assert r[0].get('success'),r
d=json.loads(r[0]['message']);(ROOT/'audits/construction-quality.json').write_text(json.dumps(d,indent=2))
for role,data in d.items():
 print(role,'parameters',data['user_parameter_count'],'dependent',data['user_parameters_with_parameter_dependencies'])
 for p in sorted(data['parts'],key=lambda p:p['edges'],reverse=True)[:5]:print(p['part'],p['feature_count'],'features',p['sketch_count'],'sketches',p['edges'],'edges',p['faces'],'faces',p['fitted_spline_points'],'fit points')
