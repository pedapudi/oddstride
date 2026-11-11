"""Publish the qualified current body geometry inside the existing Chassis document."""
import hashlib,json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1];target=json.loads((ROOT/'manifests/current-body-target.json').read_text())
labels={'body_center_0':'cover','belly_center_0':'belly','chassis_beam_102':'right-rail','chassis_beam_-102':'left-rail','chassis_crossmember_121':'front-tie','chassis_crossmember_-121':'rear-tie'}
for key,label in labels.items():
 label='cohesive-body-'+label;sha=hashlib.sha256((ROOT/'exports'/f'{label}.step').read_bytes()).hexdigest()
 for suffix,gate in [('geometry','geometric_gate_passed'),('sections','section_gate_passed')]:
  report=json.loads((ROOT/'audits'/f'{label}-{suffix}.json').read_text());assert report[gate] and report['native_step_sha256']==sha;assert report['source_step_sha256']==target['files'][key]['step']['sha256']
assert json.loads((ROOT/'audits/cohesive-body-native-interfaces.json').read_text())['passed']
assert json.loads((ROOT/'audits/cohesive-body-reference-verification.json').read_text())['passed']
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time
def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');doc.activate();assert doc.dataFile.versionNumber==17;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);retired=[]
 for key in ['chassis_beam_-102','chassis_beam_102','chassis_crossmember_-121','chassis_crossmember_121','body_center_0']:
  occ=next(o for o in root.occurrences if o.component.partNumber==key);retired.append({'part':key,'features':occ.component.features.count,'sketches':occ.component.sketches.count});assert occ.deleteMe()
 parts=[]
 for key in KEYS:
  wanted=key if key=='belly_center_0' else 'CANDIDATE_cc_'+key;occ=next(o for o in root.occurrences if o.component.partNumber==wanted);c=occ.component;c.partNumber=key;occ.isLightBulbOn=True;occ.isGrounded=True;c.attributes.add('Tinfox','SourceModelSHA256',SOURCE);c.attributes.add('Tinfox','SourceSTEP_SHA256',STEPS[key]);c.attributes.add('Tinfox','GeometryStatus','Current body revision: surface/section comparison, targeted native solid interfaces and two edit/restores pass. Whole-robot updated-limb and manufacturing release gates remain pending.');c.attributes.add('Tinfox','ManufacturingRelease','False');c.bRepBodies.item(0).name=c.name+' structural solid';parts.append({'part':key,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'faces':c.bRepBodies.item(0).faces.count})
 assert d.computeAll();assert not any(c.partNumber.startswith('CANDIDATE_') for c in d.allComponents)
 issues=[(c.partNumber,f.name,f.errorOrWarningMessage) for c in d.allComponents for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues;assert all(j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for j in root.joints)
 assert doc.save('Update the native enclosure, shortened lower wrap, cleaned motor rails and transverse ties to the current body revision. Integrate accessible cover and tie thread pads, replace twelve standard screw references and remove ten obsolete loose nuts. Six shape/section comparisons, fourteen native interfaces and two edit/restores pass. Latest limb migration, broader motion and CNC/strength qualification remain pending; generated CAD remains authoritative.');print(json.dumps({'save_requested':True,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'parts':parts,'retired':retired,'capacity':capacity,'source_model_sha256':SOURCE,'source_of_truth':False,'scope':'Saved native body checkpoint; not the completed latest robot migration.'}))
'''.replace('KNOWN',repr(known_files())).replace('KEYS',repr(list(labels))).replace('SOURCE',repr(target['source_model_sha256'])).replace('STEPS',repr({k:target['files'][k]['step']['sha256'] for k in labels}))
r=rpc(s,'cohesive-body-native-checkpoint',timeout=240);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-body-native-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k!='capacity'})
