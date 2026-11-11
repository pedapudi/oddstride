"""Reuse the accepted native structural envelope before its obsolete motor interfaces."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);d.activateRootComponent();root=d.rootComponent;assert not any(c.partNumber=='DFMA_THIGH_SEED_FL'for c in d.allComponents);source=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_sl_thigh_master');feature=next(f for f in source.features if f.name=='Hollow structural thigh with linked sidewalls');tick=time.monotonic();source_index=feature.timelineObject.index;assert feature.timelineObject.rollTo(False)
 try:
  shell=feature.bodies.item(0);fill_feature=next(f for f in source.features if f.name=='Continuous exterior crown');fill=fill_feature.bodies.item(0);assert shell.isSolid and fill.isSolid and shell.entityToken!=fill.entityToken;occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='DFMA shared structural envelope before motor interfaces';c.partNumber='DFMA_THIGH_SEED_FL'
  for body,name in [(shell,'Shared hollow thigh envelope'),(fill,'Shared complete exterior clipping envelope')]:
   items=core.ObjectCollection.create();items.add(body);copy=c.features.copyPasteBodies.add(items);copy.name='Linked native '+name.lower();assert copy.isParametric;copy.bodies.item(0).name=name
  occ.isLightBulbOn=False
 finally:d.timeline.moveToEnd()
 assert c.bRepBodies.count==2;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);c.attributes.add('Tinfox','Role','Hidden native construction source. Reuses the accepted structural curves before motor/tie interfaces; not a physical part.');print(json.dumps({'part_number':c.partNumber,'features':c.features.count,'bodies':c.bRepBodies.count,'source_component':source.partNumber,'source_feature':feature.name,'source_feature_index_before_insert':source_index,'new_feature_indices':[f.timelineObject.index for f in c.features],'timeline_at_end':d.timeline.markerPosition==d.timeline.count,'saved':False,'seconds':time.monotonic()-tick}))
'''
if __name__=='__main__':
 r=rpc(s,'dfma-thigh-native-seed',timeout=360);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/dfma-thigh-native-seed.json').write_text(json.dumps(record,indent=2));print(record)
