"""Reuse matching distal audits; check only changed paired-bearing target solids."""
import gzip,json,hashlib
from pathlib import Path
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1];mapping=json.loads((ROOT/'manifests/whole-native-component-map-candidate.json').read_text())['parts'];base=ROOT/'snapshots/paired-bearing-target/b968fea927022ba467e05eb52ab602a680e14fd7295c263eefcb95a58a90cdc6';paired=json.loads(gzip.decompress((base/'model.json.gz').read_bytes()));lowref=json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low'];low=json.loads(gzip.decompress((ROOT/lowref['reference_model']).read_bytes()));lowparts={x['key']:x for x in lowref['custom_parts']};rows=[]
cache=[]
for file in (ROOT/'audits').glob('*.json'):
 try:d=json.loads(file.read_text())
 except (ValueError,UnicodeError):continue
 if isinstance(d,dict)and 'source_step_sha256'in d and 'native_step_sha256'in d:cache.append((file,d))
for key in ['foot','foot_right','pushrod','pushrod_right','knee_inner_spacer','knee_inner_spacer_right','knee_axle','knee_axle_right','shin_clamp_sleeve_37','shin_clamp_sleeve_37_right','shin_clamp_sleeve_105','shin_clamp_sleeve_105_right']:
 path=base/'step'/(key+'.step');mesh_identity=False
 if not path.exists():
  assert paired['meshes'][key]==low['meshes'][key],key;path=ROOT/lowparts[key]['files']['step']['path'];mesh_identity=True
 native=ROOT/mapping[key]['native_step'];sh=hashlib.sha256(path.read_bytes()).hexdigest();nh=hashlib.sha256(native.read_bytes()).hexdigest();matched=[(f,d)for f,d in cache if d['source_step_sha256']==sh and d['native_step_sha256']==nh];ga=next(((f,d)for f,d in matched if d.get('geometric_gate_passed')),None);sa=next(((f,d)for f,d in matched if d.get('section_gate_passed')),None)
 ref={'id':key,'source_step':str(path),'volume_method':'gauss_kronrod_spans','volume_method_reason':'Consistent current-target native reconciliation','skip_legacy_probes':True,'exact_face_sampling':True}
 a=ga[1]if ga else audit(key,native.stem,ref);b=sa[1]if sa else sections(key,native.stem,ref)
 row={'part':key,'target_step':str(path),'target_sha256':sh,'native_sha256':nh,'geometry_passed':a['geometric_gate_passed'],'sections_passed':b['section_gate_passed'],'reused_geometry_evidence':str(ga[0])if ga else None,'reused_section_evidence':str(sa[0])if sa else None,'fallback_source_mesh_byte_equal':mesh_identity};rows.append(row);print(row,flush=True)
d={'passed':all(x['geometry_passed']and x['sections_passed']for x in rows),'parts':rows,'scope':'Current distal geometry and cylindrical/section comparisons; placement and moving assembly remain pending.'};(ROOT/'audits/whole-distal-current-target.json').write_text(json.dumps(d,indent=2));assert d['passed']
