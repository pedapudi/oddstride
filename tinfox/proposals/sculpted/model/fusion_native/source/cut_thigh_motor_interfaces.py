"""Add independently dimensioned motor, flange and stator-tie interfaces."""
import ast,json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text() for p in ['intent_geometry.py','cohesive_limb_intent.py','cohesive_thigh_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);c=next(o.component for o in d.rootComponent.occurrences if o.component.partNumber=='CANDIDATE_cohesive_thigh_master');assert c.features.count==14;g=IntentGeometry(d,c);n=CohesiveThighIntent(g);body=c.bRepBodies.item(0)
 for key,value in {'lc_rs02_body_fit':.25,'lc_rs02_case_end_y':50.5,'lc_rs02_flange_radius':48.3,'lc_rs02_flange_y':50.3,'lc_rs02_flange_width':3.4,'lc_rs02_crank_radius':40.2,'lc_rs02_crank_y':53.5,'lc_rs02_crank_width':38,'lc_stator_tie_hole_radius':2.8,'lc_stator_tie_counterbore_radius':3.1,'lc_stator_tie_counterbore_y':60,'lc_stator_tie_counterbore_depth':8,'lc_knee_cavity_radius':53,'lc_knee_cavity_y':50.5,'lc_knee_cavity_width':40.5,'lc_knee_cavity_edge':3}.items():g.parameter(key,value,comment='Explicit RS02/interface family dimension; never uniformly scale with limb length')
 for y,depth,r,name in [('lc_thigh_inner_y-1 mm','lc_rs02_case_end_y-lc_thigh_inner_y+1 mm','lc_motor_case_radius+lc_rs02_body_fit','RS02 case fit'),('lc_rs02_flange_y','lc_rs02_flange_width','lc_rs02_flange_radius','RS02 flange clearance'),('lc_rs02_crank_y','lc_rs02_crank_width','lc_rs02_crank_radius','Output crank chamber')]:
  sk=n.circles(y,[('0 mm','0 mm',r)],name);body=n.extrude_all(sk,depth,name,fusion.FeatureOperations.CutFeatureOperation,body)
 for y,depth,r,name in [('lc_thigh_inner_y-1 mm','lc_stator_tie_counterbore_y+1 mm-lc_thigh_inner_y','lc_stator_tie_hole_radius','Three stator tie passages'),('lc_stator_tie_counterbore_y','lc_stator_tie_counterbore_depth','lc_stator_tie_counterbore_radius','Three stator tie counterbores')]:
  defs=[(x,z,r) for x,z in TIE_CENTERS];sk=n.circles(y,defs,name);body=n.extrude_all(sk,depth,name,fusion.FeatureOperations.CutFeatureOperation,body)
 sk=n.circles('lc_knee_cavity_y',[('0 mm','-lc_thigh_length','lc_knee_cavity_radius')],'Knee motion chamber');tool=n.extrude_all(sk,'lc_knee_cavity_width','Knee rounded clearance tool',fusion.FeatureOperations.NewBodyFeatureOperation);edges=core.ObjectCollection.create()
 for e in tool.edges:
  if e.geometry.objectType==core.Circle3D.classType():edges.add(e)
 assert edges.count==2,edges.count;inp=c.features.filletFeatures.createInput();inp.edgeSetInputs.addConstantRadiusEdgeSet(edges,g.value('lc_knee_cavity_edge'),False);f=c.features.filletFeatures.add(inp);f.name='Knee chamber edge radii';tool=f.bodies.item(0);body=g.combine(body,[tool],fusion.FeatureOperations.CutFeatureOperation,'Open knee motion chamber');assert c.bRepBodies.count==1
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-thigh-motor-interfaces.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));print(json.dumps({'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'paths':[path],'saved':False}))
'''
mod=ast.parse((ROOT.parent/'build.py').read_text());angles=next(ast.literal_eval(n.value) for n in mod.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='POD_TIE_ANGLES' for t in n.targets));s=s.replace('TIE_CENTERS',repr([(f'lc_stator_tie_radius*cos({a} deg)',f'lc_stator_tie_radius*sin({a} deg)') for a in angles]))
r=rpc(s,'cohesive-thigh-motor-interfaces',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-thigh-motor-interfaces.json').write_text(json.dumps(record,indent=2));print(record)
for path in record['paths']:fetch(path,Path(path).name)
