"""Checkpoint each native definition before any separate export operation."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
files=['native_documents.py','intent_geometry.py','cohesive_limb_intent.py','paired_roll_intent.py','cohesive_crank_intent.py','cohesive_carrier_intent.py','paired_housing_intent.py','dfma_shared_roll_cap_intent.py']
base='\n'.join((ROOT/'source'/p).read_text()for p in files)
rows=[]
for pn,name,method in [('DFMA_SHARED_ROLL_CAP_FL','Shared stator-fastened race cap','cap'),('DFMA_ROLL_HOUSING_FL','Through-bored bearing housing without retainer hardware','cartridge'),('DFMA_ROLL_BACKPLATE_FL','Removable stator backplate without retainer pockets','backplate')]:
 script=base+'''
def run(_context:str):
 import json,os,time
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc.dataFile.versionNumber==31 and doc.dataFile.isComplete;doc.activate();d=fusion.Design.cast(app.activeProduct);d.activateRootComponent();root=d.rootComponent;assert not any(c.partNumber==PART for c in d.allComponents);baseline={p.name:p.expression for p in d.userParameters};tick=time.monotonic();joints=[j for c in d.allComponents if c.partNumber.startswith('CURRENT_ASSEMBLY_')for j in c.joints];first=min(joints,key=lambda j:j.timelineObject.index);assert first.timelineObject.rollTo(True)
 try:
  o=root.occurrences.addNewComponent(core.Matrix3D.create());c=o.component;c.partNumber=PART;c.name=TITLE;body=getattr(DfmaSharedRollCapIntent(IntentGeometry(d,c)),METHOD)();assert c.bRepBodies.count==1 and body.isSolid;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);body.name=TITLE
  for s in c.sketches:s.isVisible=False
  for p in c.constructionPlanes:p.isLightBulbOn=False
 finally:d.timeline.moveToEnd()
 group=next(c for c in d.allComponents if c.partNumber=='DFMA_PROPOSAL_FL');cup=next(c for c in d.allComponents if c.partNumber=='DFMA_REAR_LOADED_CUP_FL');body.appearance=cup.bRepBodies.item(0).appearance;alias=group.occurrences.addExistingComponent(c,core.Matrix3D.create());alias.isLightBulbOn=True;o.isLightBulbOn=False;c.attributes.add('Tinfox','Status','Isolated DFMA proposal; nominal fit checks pending. Not a loaded or manufacturing release.');assert all(d.userParameters.itemByName(k).expression==v for k,v in baseline.items());print(json.dumps({'part_number':PART,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'feature_indices':[f.timelineObject.index for f in c.features],'timeline_at_end':d.timeline.markerPosition==d.timeline.count,'saved':False,'baseline_parameter_expressions_unchanged':True,'seconds':time.monotonic()-tick}))
'''
 script=script.replace('PART',repr(pn)).replace('TITLE',repr(name)).replace('METHOD',repr(method));tag='dfma-author-'+method;r=rpc(script,tag,timeout=1500);assert r[0]['success'],r;row=json.loads(r[0]['message']);rows.append(row);(ROOT/'audits'/('dfma-authored-'+method+'.json')).write_text(json.dumps(row,indent=2));print(row,flush=True)
(ROOT/'audits/dfma-shared-roll-cap-native.json').write_text(json.dumps({'parts':rows,'scope':'Separate successful authoring transactions; exports intentionally separate.','saved':False},indent=2))
