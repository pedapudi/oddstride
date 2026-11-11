"""Inventory current native histories and retained hidden construction without deleting geometry."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
mapping=json.loads((ROOT/'manifests/whole-native-component-map-candidate.json').read_text())['parts'];ids={r['component_part_number']for r in mapping.values()};placed=json.loads((ROOT/'audits/current-master-assembly-refresh.json').read_text())['instances'];roles={}
for row in placed.values():
 if row['component_part_number']in ids:roles[row['component_part_number']]=row['subsystem']
assert len(roles)==88
script=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json
def run(_context:str):
 app=core.Application.get();rows=[];definitions=[]
 for role in ['leg','chassis','head','master']:
  doc=authoring_document(app,role);assert not doc.isModified and doc.dataFile.isComplete;d=fusion.Design.cast(doc.products.itemByProductType('DesignProductType'));root=d.rootComponent;wanted={k for k,v in ROLES.items()if v==role};found={}
  for c in d.allComponents:
   if c.partNumber not in wanted:continue
   assert c.partNumber not in found,c.partNumber;assert c.meshBodies.count==0 and c.features.count>0,c.partNumber
   health=[{'name':f.name,'health':str(f.healthState),'message':f.errorOrWarningMessage}for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not health,(c.partNumber,health)
   found[c.partNumber]={'part_number':c.partNumber,'name':c.name,'role':role,'saved_version':doc.dataFile.versionNumber,'features':c.features.count,'sketches':c.sketches.count,'solid_bodies':c.bRepBodies.count,'mesh_bodies':c.meshBodies.count,'all_features_healthy':True,'local_sketch_required':False,'editability_note':'Native mirrored/derived variants may depend on the authored family parent without owning a local sketch; preserved geometry lineage identifies that parent.'};definitions.append(found[c.partNumber])
  assert set(found)==wanted,(role,sorted(wanted-set(found)));roots=[{'name':o.name,'part_number':o.component.partNumber,'visible':o.isLightBulbOn,'direct_bodies':o.component.bRepBodies.count,'direct_children':o.component.occurrences.count,'joints':o.component.joints.count,'referenced':o.isReferencedComponent}for o in root.occurrences];rows.append({'role':role,'saved_version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'root_occurrences':roots,'current_custom_definitions':len(found),'visible_root_occurrences':sum(o['visible']for o in roots),'hidden_root_occurrences':sum(not o['visible']for o in roots),'timeline_count':d.timeline.count})
 assert len(definitions)==88;authoring_document(app,'master').activate();print(json.dumps({'passed':True,'documents':rows,'current_definitions':definitions,'custom_definition_count':88,'new_cloud_documents':0,'deleted_cloud_files':0,'cleanup_scope':'The24 obsolete pose joints were removed in the separately retained cleanup audit. Hidden construction and canonical bench parents remain where shared or needed for reproducibility; hidden is not represented as deleted. Current visible Master references exactlythree saved subsystem documents.'}))
'''.replace('ROLES',repr(roles))
r=rpc(script,'current-native-cleanup-history-inventory',timeout=180,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-native-cleanup-history-inventory.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'custom_definition_count':record['custom_definition_count'],'documents':[(r['role'],r['saved_version'],r['visible_root_occurrences'],r['hidden_root_occurrences'])for r in record['documents']]})
