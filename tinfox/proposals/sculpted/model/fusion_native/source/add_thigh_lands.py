"""Add structural screw lands clipped by the shared native envelope."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text() for p in ['intent_geometry.py','cohesive_limb_intent.py','cohesive_thigh_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);c=next(o.component for o in d.rootComponent.occurrences if o.component.partNumber=='CANDIDATE_cohesive_thigh_master');assert c.features.count==4;g=IntentGeometry(d,c);n=CohesiveThighIntent(g)
 hollow=c.features.extrudeFeatures.item(1);assert hollow.name=='Constant wall structural cavity';hollow.timelineObject.rollTo(True);objects=core.ObjectCollection.create();objects.add(c.bRepBodies.item(0));copy=c.features.copyPasteBodies.add(objects);copy.name='Linked exterior clipping envelope';envelope=copy.bodies.item(0);envelope.name='Construction envelope';d.timeline.moveToEnd();body=next(b for b in c.bRepBodies if b!=envelope);assert c.bRepBodies.count==2
 for key,value in {'lc_thigh_clamp_rear_x':-38,'lc_thigh_clamp_front_x':26,'lc_thigh_land_rear_radius':12,'lc_thigh_land_front_radius':8,'lc_thigh_stator_land_radius':5.2,'lc_thigh_stator_land_depth':13,'lc_stator_tie_radius':43.5}.items():g.parameter(key,value)
 for key,value in {'lc_thigh_clamp_rear_z':'-(70/170)*lc_thigh_length','lc_thigh_clamp_front_z':'-(48/170)*lc_thigh_length'}.items():g.parameter(key,value)
 lands=[]
 for name,depth,definitions in [('Structural closure lands','lc_thigh_width',[('lc_thigh_clamp_rear_x','lc_thigh_clamp_rear_z','lc_thigh_land_rear_radius'),('lc_thigh_clamp_front_x','lc_thigh_clamp_front_z','lc_thigh_land_front_radius')]),('Stator tie lands','lc_thigh_stator_land_depth',TIE_DEFS)]:
  sk=n.circles('lc_thigh_inner_y',definitions,name);profiles=core.ObjectCollection.create()
  for p in sk.profiles:profiles.add(p)
  inp=c.features.extrudeFeatures.createInput(profiles,fusion.FeatureOperations.NewBodyFeatureOperation);inp.setDistanceExtent(False,g.value(depth));f=c.features.extrudeFeatures.add(inp);f.name=name;pieces=list(f.bodies);sk.isLightBulbOn=False
  for index,piece in enumerate(pieces):
   clipped=g.combine(piece,[envelope],fusion.FeatureOperations.IntersectFeatureOperation,name+' envelope trim '+str(index+1),True);lands.append(clipped)
 body=g.combine(body,lands,fusion.FeatureOperations.JoinFeatureOperation,'Integral structural screw lands');c.features.removeFeatures.add(envelope).name='Remove construction envelope';assert c.bRepBodies.count==1
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','cohesive-thigh-lands.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));print(json.dumps({'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'faces':body.faces.count,'edges':body.edges.count,'paths':[path],'saved':False}))
'''
import sys
sys.path.insert(0,str(ROOT.parent))
# Read the three design angles without importing CadQuery in the RPC client.
import ast
mod=ast.parse((ROOT.parent/'build.py').read_text());angles=None
for node in mod.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='POD_TIE_ANGLES' for t in node.targets):angles=ast.literal_eval(node.value)
assert angles is not None
s=s.replace('TIE_DEFS',repr([(f'lc_stator_tie_radius*cos({a} deg)',f'lc_stator_tie_radius*sin({a} deg)','lc_thigh_stator_land_radius') for a in angles]))
r=rpc(s,'cohesive-thigh-lands',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-thigh-lands.json').write_text(json.dumps(record,indent=2));print(record)
for path in record['paths']:fetch(path,Path(path).name)
