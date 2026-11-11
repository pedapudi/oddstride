"""Export the saved native low-profile robot directly from its placed Fusion bodies."""
import gzip
import hashlib
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch

ROOT = Path(__file__).resolve().parents[1]
target = json.loads((ROOT / 'manifests/whole-robot-integration-target.json').read_text())
source = json.loads(gzip.decompress((ROOT / target['reference_model']).read_bytes()))
inventory = json.loads((ROOT / 'audits/current-master-assembly-refresh.json').read_text())
assert inventory['passed'] and inventory['model_items'] == 684
metadata = {p['name']: p for p in source['parts'] if p['name'] in inventory['instances']}
assert len(metadata) == 684
contact_path=ROOT/'audits'/('whole-reference-motion-classification-'+target['model_sha256']+'.json')
contact_audit=json.loads(contact_path.read_text());assert contact_audit['source_model_sha256']==target['model_sha256']
contact_rules=[]
for rule in contact_audit['thread_reference_pairs']:
    assert all(name in inventory['instances'] for name in rule['pair'])
    contact_rules.append({**rule,'evidence':{'classification_audit':str(contact_path.relative_to(ROOT)),'classification_audit_sha256':hashlib.sha256(contact_path.read_bytes()).hexdigest(),'native_placement_audit':'audits/current-master-assembly-refresh.json','native_placement_audit_sha256':hashlib.sha256((ROOT/'audits/current-master-assembly-refresh.json').read_bytes()).hexdigest()}})
assert len(contact_rules)==48
script = (ROOT / 'source/native_documents.py').read_text() + '''
import adsk.core as core,adsk.fusion as fusion,json,gzip,hashlib,os,time,math

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'master');doc.activate();d=fusion.Design.cast(app.activeProduct);assert not doc.isModified and doc.dataFile.isComplete
 root=d.rootComponent;tick=time.monotonic();parts=[];meshes={};live={};frames={};versions={};mesh_cache={};reuse_checks=[];identity=list(core.Matrix3D.create().asArray())
 auxiliary_paths={r['native_path']for r in INVENTORY.values()if r.get('auxiliary')}
 def walk(occ,ancestor_visible=True):
  visible=ancestor_visible and occ.isLightBulbOn
  if not visible and not any(occ.fullPathName==p or p.startswith(occ.fullPathName+'+')for p in auxiliary_paths):return
  if occ.component.partNumber.startswith('CURRENT_FRAME_'):frames[occ.component.partNumber]=occ
  if occ.component.bRepBodies.count:live[occ.fullPathName]=occ
  for child in occ.component.occurrences:walk(child.createForAssemblyContext(occ),visible)
 for o in root.occurrences:
  role=o.attributes.itemByName('Tinfox','Subsystem').value;versions[role]=o.documentReference.version;walk(o)
 assert len(live)==684 and len(frames)==24
 leg_doc=authoring_document(app,'leg');assert leg_doc.dataFile.versionNumber==versions['leg'] and not leg_doc.isModified;leg_design=fusion.Design.cast(leg_doc.products.itemByProductType('DesignProductType'));parameters={'units':'mm','joint_limits_deg':PARAMETERS['joint_limits_deg'],'nominal_pose_deg':PARAMETERS['nominal_pose_deg']};parameter_bindings={}
 for key,name in {'hip_x':'lc_hip_x','roll_y':'lc_roll_y','pitch_x_offset':'pr_pitch_x_offset','pitch_offset':'lc_pitch_offset','thigh':'lc_thigh_length','rod_length':'lc_thigh_length','crank_radius':'lc_crank_radius','crank_phase_deg':'lc_crank_phase','shank_to_foot_center':'lc_shank_foot_center','shin_y':'lc_foot_center_y','foot_radius':'lc_foot_radius','bearing_od':'lc_bearing_od','bearing_id':'lc_bearing_id','bearing_width':'lc_bearing_width'}.items():
  p=leg_design.userParameters.itemByName(name);assert p,name;value=p.value*(180/math.pi if key=='crank_phase_deg'else 10);assert abs(value-PARAMETERS[key])<1e-7,(key,value,PARAMETERS[key]);parameters[key]=value;parameter_bindings[key]={'native_parameter':name,'expression':p.expression,'value':value,'document_version':versions['leg']}
 def point_mm(p,m):return [sum(m[i*4+j]*p[j]for j in range(3))*10+m[i*4+3]*10 for i in range(3)]
 for name,record in INVENTORY.items():
  occ=live[record['native_path']];matrix=list(occ.transform2.asArray());assert max(abs(a-b)for a,b in zip(matrix,record['world_matrix_cm']))<1e-7,name
  meta=META[name];local=core.Matrix3D.create()
  if meta.get('leg'):
   local=frames['CURRENT_FRAME_'+meta['leg']+'_'+meta['group']].transform2.copy();assert local.invert()
  left=list(local.asArray());right=list(occ.transform2.asArray());world=core.Matrix3D.create();assert world.setWithArray([sum(left[i*4+k]*right[k*4+j]for k in range(4))for i in range(4)for j in range(4)])
  cache_key=(record['subsystem'],occ.component.id,tuple(body.entityToken for body in occ.component.bRepBodies))
  if cache_key not in mesh_cache:
   raw_vertices=[];faces=[];body_rows=[]
   for body in occ.component.bRepBodies:
    assert (body.isLightBulbOn or record.get('auxiliary'))and body.isSolid;calculator=body.meshManager.createMeshCalculator();calculator.surfaceTolerance=.001;calculator.maxNormalDeviation=.03;mesh=calculator.calculate();offset=len(raw_vertices);raw_vertices.extend([p.x,p.y,p.z]for p in mesh.nodeCoordinates);indices=list(mesh.nodeIndices);assert indices and len(indices)%3==0;faces.extend([[offset+indices[i],offset+indices[i+1],offset+indices[i+2]]for i in range(0,len(indices),3)]);body_rows.append({'name':body.name,'faces':body.faces.count,'edges':body.edges.count,'solid':body.isSolid})
   mesh_cache[cache_key]=(raw_vertices,faces,body_rows)
  raw_vertices,faces,body_rows=mesh_cache[cache_key];transform=list(world.asArray());vertices=[point_mm(p,transform)for p in raw_vertices]
  key=meta['mesh'];geometry={'vertices':vertices,'faces':faces};bounds=[min(p[i]for p in vertices)for i in range(3)]+[max(p[i]for p in vertices)for i in range(3)]
  if key in meshes:
   prior=meshes[key];error=None
   if prior['faces']==faces and len(prior['vertices'])==len(vertices):error=max((max(abs(a-b)for a,b in zip(p,q))for p,q in zip(prior['vertices'],vertices)),default=0)
   if error is not None and error<1e-7:reuse_checks.append({'name':name,'mesh':key,'maximum_corresponding_coordinate_error_mm':error});geometry=prior
   else:key=key+'__'+name
  meshes[key]=geometry;role=meta.get('reference_role')or('custom_structure'if record['kind']=='native_custom'else'vendor_or_standard_reference')
  if name in ['body_wordmark','body_serial']:role='nonmanufacturing_display_reference'
  if name=='sensor_window':role='provisional_optical_backing_envelope'
  if name=='electronics_clearance':role='auxiliary_clearance_envelope'
  parts.append({'name':name,'mesh':key,'source_mesh_key':meta['mesh'],'leg':meta.get('leg'),'group':meta.get('group','body'),'material':meta.get('material'),'color':meta.get('color'),'com_mm':[(bounds[i]+bounds[i+3])/2 for i in range(3)],'com_basis':'Display label anchor at mesh bounds center; not a measured center of mass.','bounds_mm':bounds,'mass_kg':None,'mass_status':'Unqualified material assignments; no robot mass estimate.','reference_role':role,'native_path':occ.fullPathName,'native_definition_id':occ.component.partNumber,'native_world_matrix_cm':matrix,'native_group_local_matrix_cm':list(world.asArray()),'native_bodies':body_rows})
  parts[-1]['native_visible']=record['native_visible']
  if record.get('auxiliary'):parts[-1].update(service_role='keepout',physical_component=False,note='Hidden electronics packaging clearance; not a manufactured or purchased component.')
 assert len(parts)==684 and sum(len(p['native_bodies'])for p in parts)==703
 result={'parameters':parameters,'native_parameter_bindings':parameter_bindings,'frozen_context_parameters':PARAMETERS,'poses':POSES,'parts':parts,'meshes':meshes,'estimated_mass_kg':None,'native_migration':{'scope':'Current low-profile robot; optional raised-head variant excluded.','native_source_of_truth':False,'authority':'Candidate saved native export; final comparison and publication approval pending.','document_file_id':doc.dataFile.id,'saved_master_version':doc.dataFile.versionNumber,'subsystem_versions':versions,'working_modified':doc.isModified,'target_model_sha256':TARGET,'geometry':'Direct Fusion meshManager surfaces in actual native kinematic-group frames; no generated custom geometry.','surface_tolerance_mm':.01,'max_normal_deviation_radians':.03,'parameter_scope':'Kinematics read from saved native parameters. Joint-limit and named-pose presets are retained review conditions, not collision-free certification. Frozen context is historical design metadata, not live native dimensions.'},'scope':'Geometry and assembly authority candidate. Existing body/contact, manufacturing and physical load limitations remain separate.'}
 result['inventory']={'review_records':684,'review_solids':703,'visible_model_items':683,'visible_model_solids':702,'hidden_auxiliary_envelopes':1};result['native_mesh_reuse_checks']=reuse_checks;result['validated_reference_contacts']=CONTACT_RULES;raw=json.dumps(result,separators=(',',':')).encode();folder=os.path.join(os.path.expanduser('~'),'Library','Caches','Tinfox','native-whole-master-'+str(doc.dataFile.versionNumber));os.makedirs(folder,exist_ok=True);path=os.path.join(folder,'native-whole-review-candidate.json.gz');open(path,'wb').write(gzip.compress(raw,mtime=0));assert not doc.isModified
 print(json.dumps({'passed':True,'path':path,'sha256':hashlib.sha256(open(path,'rb').read()).hexdigest(),'model_sha256':hashlib.sha256(raw).hexdigest(),'saved_master_version':doc.dataFile.versionNumber,'subsystem_versions':versions,'model_items':684,'solid_bodies':703,'meshed_native_definitions':len(mesh_cache),'verified_reused_meshes':len(reuse_checks),'source_target_sha256':TARGET,'elapsed_seconds':time.monotonic()-tick,'native_source_of_truth':False}))
'''
for token, value in [('INVENTORY', inventory['instances']), ('META', metadata), ('PARAMETERS', source['parameters']), ('POSES', source['poses']), ('TARGET', target['model_sha256']), ('CONTACT_RULES',contact_rules)]:
    script = script.replace(token, repr(value))
compile(script, 'export_current_native_robot.py', 'exec')
reply = rpc(script, 'current-native-whole-review-export', timeout=900, read_only=True)
assert reply[0]['success'], reply
record = json.loads(reply[0]['message'])
(ROOT / 'audits/current-native-whole-review-export.json').write_text(json.dumps(record, indent=2))
folder = 'whole-native-master-' + str(record['saved_master_version'])
fetch(record['path'], folder + '/native-whole-review-candidate.json.gz')
print(record)
