"""Create two structural native manufacturing parts from the shared DFMA envelope."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
files=['native_documents.py','intent_geometry.py','native_nonuniform_spline.py','cohesive_limb_intent.py','cohesive_thigh_intent.py','slim_thigh_intent.py','dfma_thigh_intent.py'];base='\n'.join((ROOT/'source'/p).read_text()for p in files)
for outer in [False,True]:
 s=base+'''
def run(_context:str):
 import json,time
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);d.activateRootComponent();root=d.rootComponent;pn='DFMA_THIGH_SECONDARY_FL'if OUTER else'DFMA_THIGH_PRIMARY_FL';assert not any(c.partNumber==pn for c in d.allComponents);master=next(c for c in d.allComponents if c.partNumber=='DFMA_THIGH_SEED_FL');lower=next(c for c in d.allComponents if c.partNumber==('CANDIDATE_mc_thigh_outer'if OUTER else'CANDIDATE_sl_thigh_inner'));modules=[o for o in root.occurrences if o.component.partNumber.startswith('CURRENT_ASSEMBLY_')];first=min(modules,key=lambda o:o.timelineObject.index);assert max(f.timelineObject.index for f in master.features)<first.timelineObject.index;assert max(f.timelineObject.index for f in lower.features)<first.timelineObject.index;tick=time.monotonic();assert first.timelineObject.rollTo(True)
 try:
  o=root.occurrences.addNewComponent(core.Matrix3D.create());c=o.component;c.partNumber=pn;c.name='Integrated secondary motor cover and thigh'if OUTER else'Integrated primary motor cradle and thigh';copied=[]
  for source,name in [(next(b for b in master.bRepBodies if b.name=='DFMA shared proximal structural limb'),'Shared native proximal structure'),(next(b for b in master.bRepBodies if b.name=='Construction DFMA shared split'),'Shared manufacturing split'),(lower.bRepBodies.item(0),'Unchanged native knee and lower limb')]:
   items=core.ObjectCollection.create();items.add(source);copy=c.features.copyPasteBodies.add(items);copy.name=name;assert copy.isParametric;copied.append(copy.bodies.item(0))
  body=DfmaThighIntent(IntentGeometry(d,c)).finished_half(*copied,OUTER);assert c.bRepBodies.count==1 and body.isSolid
  for sk in c.sketches:sk.isVisible=False
  for plane in c.constructionPlanes:plane.isLightBulbOn=False
 finally:d.timeline.moveToEnd()
 assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);group=next(c for c in d.allComponents if c.partNumber=='DFMA_PROPOSAL_FL');matrix=core.Matrix3D.create();matrix.translation=core.Vector3D.create(d.userParameters.itemByName('pr_pitch_x_offset').value,0,0);alias=group.occurrences.addExistingComponent(c,matrix);alias.isLightBulbOn=True;o.isLightBulbOn=False;body.appearance=lower.bRepBodies.item(0).appearance;c.attributes.add('Tinfox','Status','Isolated DFMA proposal. Integrated motor mounting and common long screws; insertion/tool/motion checks pending. No strength or print release.');print(json.dumps({'part_number':pn,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'saved':False,'assembly_translation_mm':[v*10 for v in matrix.translation.asArray()],'seconds':time.monotonic()-tick}))
'''.replace('OUTER',repr(outer))
 tag='dfma-thigh-'+('secondary'if outer else'primary');r=rpc(s,tag,timeout=1800);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits'/(tag+'.json')).write_text(json.dumps(record,indent=2));print(record,flush=True)
