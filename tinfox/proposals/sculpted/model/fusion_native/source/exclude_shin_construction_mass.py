"""Keep master history while excluding its construction solid from final mass."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core, adsk.fusion as fusion,json

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent
 master=next(o.component for o in root.occurrences if o.component.partNumber=='CANDIDATE_cohesive_shin_master');targets=[o.component for o in root.occurrences if o.component.partNumber.startswith('CANDIDATE_cohesive_shin_') and o.component!=master]
 assert len(targets)==4 and master.bRepBodies.count==1
 volumes={c.partNumber:c.bRepBodies.item(0).volume for c in targets};feature=master.features.removeFeatures.add(master.bRepBodies.item(0));feature.name='Exclude construction solid from assembled mass';assert master.bRepBodies.count==0
 p=d.userParameters.itemByName('lc_shank_foot_center');old=p.expression
 try:
  p.expression='149 mm';assert d.computeAll();response={c.partNumber:c.bRepBodies.item(0).boundingBox.minPoint.z*10 for c in targets};assert all(abs(v+137)<.002 for v in response.values()),response
 finally:p.expression=old;assert d.computeAll()
 for c in targets:
  assert c.bRepBodies.count==1 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features)
  assert abs(c.bRepBodies.item(0).volume-volumes[c.partNumber])<.002
 assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in master.features)
 master.attributes.add('Tinfox','Role','Construction master: native source before final Remove feature; not a manufacturing part')
 print(json.dumps({'master_final_body_count':master.bRepBodies.count,'master_features':master.features.count,'manufacturing_parts':len(targets),'linked_edit_response':response,'restored':True,'saved':False}))
'''
r=rpc(s,'cohesive-shin-construction-mass',timeout=240);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-shin-construction-mass.json').write_text(json.dumps(record,indent=2));print(record)
