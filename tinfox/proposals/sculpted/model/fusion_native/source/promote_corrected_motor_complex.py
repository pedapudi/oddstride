"""Publish the saved corrected bench scope after independent export and static gates."""
import argparse,datetime,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--independent-static',required=True);p.add_argument('--independent-exports',required=True);p.add_argument('--browser',required=True);args=p.parse_args()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def evidence(p):
 p=Path(p).resolve();return {'path':str(p),'sha256':sha(p)}
candidate=ROOT/'manifests/motor-complex-corrected-candidate.json';m=read(candidate);saved=read(ROOT/'audits/corrected-bench-saved-reopen.json')
assert saved['passed'] and saved['reopened'] and saved['complete'] and not saved['modified'] and saved['version']==24
assert saved['snapshot']['visible_root']==['BENCH_MOTOR_COMPLEX'] and len(saved['snapshot']['placement'])==13
external=[]
for name in [args.independent_static,args.independent_exports,args.browser]:
 path=Path(name).resolve();d=read(path)
 if name==args.browser:assert not d['browser_errors'] and not d['missing_assets'] and d['bodies']==121 and d['custom_parts']==13 and d['motors']==3 and d['connector_bodies']==24 and all(d[k]for k in ['static_controls','all_custom_parts_isolated','sections','native_step_links'])
 elif name==args.independent_exports:assert d['candidate_validation_passed'] and len(d['parts'])==13 and d['total_stock_copies']==8
 else:assert d.get('passed',d.get('overall_passed',False)),name
 external.append(evidence(path))
# Publication requires the review records to bind these immutable inputs explicitly.
assert m['assembly_step_sha256'] in Path(args.independent_static).read_text()
assert sha(candidate) in Path(args.independent_exports).read_text()
assert m['review_model_sha256'] in Path(args.browser).read_text()
for f in ['knee-seat-family-edit-restore.json','recessed-closure-family-edit-restore.json','recessed-closure-family-export-restore.json','hub-case-family-edit-restore.json','corrected-thigh-split-native.json']:
 assert read(ROOT/'audits'/f)['passed']
for key,row in m['parts'].items():
 assert sha(ROOT/row['native_step'])==row['native_step_sha256'];assert sha(ROOT/row['native_3mf'])==row['native_3mf_sha256'];s=saved['snapshot']['parts'][key]
 assert s['features']==row['native_feature_count'] and s['sketches']==row['native_sketch_count']
 assert max(abs(a-b)for a,b in zip(s['bounds_mm'],row['native_bounds_mm']))<1e-6
 assert abs(s['volume_mm3']-row['native_volume_mm3'])<.002
 dx,dy,dz=row['assembly_translation_mm'];expected=[1.,0,0,dx/10,0,1.,0,dy/10,0,0,1.,dz/10,0,0,0,1.]
 assert max(abs(a-b)for a,b in zip(expected,saved['snapshot']['placement'][key]))<1e-8
 row.update(saved_version=24,state='canonical_native',saved_native_fingerprint=s,export_checkpoint_version=23)
raw=gzip.decompress((ROOT/m['review_model']).read_bytes());assert hashlib.sha256(raw).hexdigest()==m['review_model_sha256'];model=json.loads(raw)
def geometry_hash(model):return hashlib.sha256(json.dumps({'parts':model['parts'],'meshes':model['meshes']},sort_keys=True,separators=(',',':')).encode()).hexdigest()
gh=geometry_hash(model);model['native_migration'].update(authority='Canonical native Fusion geometry for corrected detached13-part motor complex',native_source_of_truth=True,saved_version=24,working_modified=False,export_checkpoint_version=23,assembly_release_ready=True,saved_reopen_evidence='audits/corrected-bench-saved-reopen.json',full_robot_authority='Generated integration reference; full robot not promoted')
newraw=json.dumps(model,separators=(',',':')).encode();out=ROOT/'exports/motor-complex-leg23-native/native-bench-review-canonical-leg24.json.gz';assert not out.exists();out.write_bytes(gzip.compress(newraw,mtime=0));assert geometry_hash(model)==gh
old=ROOT/'manifests/motor-complex-native-exports.json';previous=read(old);oldhash=sha(old);
shape_reports={'hip_hub':'native-hub-relief-validation.json','motor_mount_ring':'native-seat-validation.json','motor_carrier_1':'native-closure-validation.json','hip_stator_closure_1':'native-closure-validation.json'}
for key,row in m['parts'].items():
 if key in shape_reports:
  path=ROOT.parents[3]/'analysis/dfma/knee-stator-seats'/shape_reports[key];assert read(path)['passed'];row['geometry_comparison_evidence']=[evidence(path)]
 else:
  assert previous['parts'][key]['native_step_sha256']==row['native_step_sha256'];row['geometry_comparison_evidence']=previous['parts'][key]['geometry_comparison_evidence'];row['unchanged_qualified_geometry_from_manifest_sha256']=oldhash
archive=ROOT/'snapshots/authority-history'/('motor-complex-'+oldhash+'.json');archive.parent.mkdir(parents=True,exist_ok=True)
if archive.exists():assert sha(archive)==oldhash
else:archive.write_bytes(old.read_bytes())
reports=['corrected-bench-saved-reopen.json','corrected-bench-final-checkpoint.json','motor-complex-leg23-native-direct-exports.json','native-bench-all-pairs.json','native-bench-thread-envelope-classification.json','standard-countersunk-reference-seating.json','recessed-bench-reference-placements.json','knee-seat-family-edit-restore.json','recessed-closure-family-edit-restore.json','recessed-closure-family-export-restore.json','hub-case-family-edit-restore.json','corrected-thigh-split-native.json']
now=datetime.datetime.now(datetime.UTC).isoformat();m.update(native_source_of_truth=True,assembly_release_ready=True,authority='Native Fusion is canonical for these13 custom parts and the corrected static detached motor-complex assembly.',latest_leg_checkpoint=24,candidate_exports_are_not_manufacturing_release=False,manufacturing_scope='Unpowered fit and staged assembly prototype. Physical manufacturing fits, preload, printed operating strength and powered operation remain unqualified.',review_model=str(out.relative_to(ROOT)),review_model_sha256=hashlib.sha256(newraw).hexdigest(),review_model_gzip_sha256=sha(out),review_geometry_sha256=gh,private_candidate_manifest_sha256=sha(candidate),private_candidate_model_sha256=hashlib.sha256(raw).hexdigest(),promotion_evidence=external+[evidence(ROOT/'audits'/f)for f in reports],previous_authority_manifest_sha256=oldhash,updated_utc=now,limitations=['Static detached assembly; no automatic hardware repositioning after parameter edits or native joint preview is claimed.','Follow the staged assembly order; postclosure internal fasteners are not all directly accessible.','Reference motors/connectors are independently hideable vendor envelopes. Verify actual purchased dimensions.','Material assignments and robot mass are not qualified. No loaded, powered or whole-robot performance release.'],known_design_limitations=[])
for row in m['stock_references']:row.update(saved_version=24,export_checkpoint_version=23)
m['reference_seating_overrides']=[x for x in m['hardware_overrides']if x['item']=='Hip and roll countersunk reference seating']
m['hardware_overrides']=[x for x in m['hardware_overrides']if x['item']!='Hip and roll countersunk reference seating']
for x in m['hardware_overrides']:
 if x['item']=='Hip stator closure to cup':x.update(item='Cup closure',washer_quantity=0,nut_quantity=3)
old.write_text(json.dumps(m,indent=2)+'\n')
status=read(ROOT/'manifests/source-authority.json');status['canonical_scopes']['motor_complex'].update(manifest_sha256=sha(old),saved_leg_version=24);status['updated_utc']=now;(ROOT/'manifests/source-authority.json').write_text(json.dumps(status,indent=2)+'\n')
subs=read(ROOT/'manifests/subsystems.json');subs['subsystems']['leg'].update(version=24,save_verified=True,verification_report='audits/corrected-bench-saved-reopen.json',canonical_scope='Corrected13-part static motor complex only');(ROOT/'manifests/subsystems.json').write_text(json.dumps(subs,indent=2)+'\n')
print(json.dumps({'manifest_sha256':sha(old),'saved_version':24,'export_version':23,'review_model':m['review_model'],'assembly_release_ready':True,'full_robot_native':False},indent=2))
