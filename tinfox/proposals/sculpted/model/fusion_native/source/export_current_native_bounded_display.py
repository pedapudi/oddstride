"""Export the saved native viewport meshes directly from the placed Fusion bodies."""
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
 root=d.rootComponent;tick=time.monotonic();parts=[];meshes={};live={};frames={};versions={};mesh_cache={};reuse_checks=[];authoring_components={};identity=list(core.Matrix3D.create().asArray())
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
 for role in ['leg','chassis','head']:
  source_doc=authoring_document(app,role);assert source_doc.dataFile.versionNumber==versions[role]and not source_doc.isModified;source_design=fusion.Design.cast(source_doc.products.itemByProductType('DesignProductType'));authoring_components[role]={}
  for c in source_design.allComponents:authoring_components[role].setdefault(c.partNumber,[]).append(c)
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
   for body_index,body in enumerate(occ.component.bRepBodies):
    assert (body.isLightBulbOn or record.get('auxiliary'))and body.isSolid;display=body.meshManager.displayMeshes;candidates=[(display.item(i).surfaceTolerance*10,i,display.item(i),'linked_native_cache')for i in range(display.count)];source_binding=None
    if record['kind']=='native_custom':
     matches=authoring_components[record['subsystem']].get(occ.component.partNumber,[]);assert len(matches)==1,(name,'Authoring definition is not unique');source_component=matches[0];assert source_component.bRepBodies.count==occ.component.bRepBodies.count;source_body=source_component.bRepBodies.item(body_index);assert (source_body.faces.count,source_body.edges.count)==(body.faces.count,body.edges.count);bounds=lambda b:[*b.boundingBox.minPoint.asArray(),*b.boundingBox.maxPoint.asArray()];bound_error=max(abs(a-b)for a,b in zip(bounds(body),bounds(source_body)))*10;assert bound_error<.000001,(name,bound_error);vertices=lambda b:sorted(tuple(round(x,9)for x in v.geometry.asArray())for v in b.vertices);assert vertices(body)==vertices(source_body),(name,'Linked and authoring definition vertices differ');source_display=source_body.meshManager.displayMeshes;candidates.extend((source_display.item(i).surfaceTolerance*10,i,source_display.item(i),'saved_authoring_native_cache')for i in range(source_display.count));source_binding={'document':record['subsystem'],'saved_version':versions[record['subsystem']],'part_number':source_component.partNumber,'body_index':body_index,'linked_local_bounds_error_mm':bound_error,'linked_local_vertex_fingerprint_equal':True}
    eligible=[r for r in candidates if r[0]<=.05]
    if eligible:tolerance,index,mesh,mesh_source=max(eligible,key=lambda r:r[0])
    else:
     calculator=body.meshManager.createMeshCalculator();calculator.surfaceTolerance=.005;calculator.maxNormalDeviation=.12;mesh=calculator.calculate();tolerance=.05;index=None;mesh_source='native_calculator_bounded_fallback'
    assert mesh and mesh.isValid and tolerance>0,(name,tolerance);offset=len(raw_vertices);raw_vertices.extend([p.x,p.y,p.z]for p in mesh.nodeCoordinates);indices=list(mesh.nodeIndices);assert indices and len(indices)%3==0;faces.extend([[offset+indices[i],offset+indices[i+1],offset+indices[i+2]]for i in range(0,len(indices),3)]);body_rows.append({'name':body.name,'faces':body.faces.count,'edges':body.edges.count,'solid':body.isSolid,'native_display_surface_tolerance_mm':tolerance,'native_display_mesh_count':display.count,'display_triangles':len(indices)//3,'native_display_mesh_index':index,'mesh_source':mesh_source,'authoring_cache_binding':source_binding,'display_tolerance_outlier':tolerance>.05})
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
 result={'parameters':parameters,'native_parameter_bindings':parameter_bindings,'frozen_context_parameters':PARAMETERS,'poses':POSES,'parts':parts,'meshes':meshes,'estimated_mass_kg':None,'native_migration':{'scope':'Current low-profile robot; optional raised-head variant excluded.','native_source_of_truth':False,'authority':'Candidate saved native export; final comparison and publication approval pending.','document_file_id':doc.dataFile.id,'saved_master_version':doc.dataFile.versionNumber,'subsystem_versions':versions,'working_modified':doc.isModified,'target_model_sha256':TARGET,'geometry':'Native linked or equivalent saved-authoring viewport caches at0.05mm or finer; native calculator fallback for remaining bodies. Actual native group frames; no generated or externally simplified custom geometry.','display_surface_tolerance_mm_max':max(b['native_display_surface_tolerance_mm']for p in parts for b in p['native_bodies']),'tessellation_scope':'Native viewport display meshes; per-body reported tolerances are recorded. Exact native STEP and high-detail audit exports remain separate.','parameter_scope':'Kinematics read from saved native parameters. Joint-limit and named-pose presets are retained review conditions, not collision-free certification. Frozen context is historical design metadata, not live native dimensions.'},'scope':'Geometry and assembly authority candidate. Existing body/contact, manufacturing and physical load limitations remain separate.'}
 result['inventory']={'review_records':684,'review_solids':703,'visible_model_items':683,'visible_model_solids':702,'hidden_auxiliary_envelopes':1};result['native_mesh_reuse_checks']=reuse_checks;result['validated_reference_contacts']=CONTACT_RULES;raw=json.dumps(result,separators=(',',':')).encode();folder=os.path.join(os.path.expanduser('~'),'Library','Caches','Tinfox','native-whole-master-'+str(doc.dataFile.versionNumber));os.makedirs(folder,exist_ok=True);path=os.path.join(folder,'native-whole-bounded-display-candidate.json.gz');open(path,'wb').write(gzip.compress(raw,compresslevel=1,mtime=0));assert not doc.isModified
 print(json.dumps({'passed':True,'path':path,'sha256':hashlib.sha256(open(path,'rb').read()).hexdigest(),'model_sha256':hashlib.sha256(raw).hexdigest(),'saved_master_version':doc.dataFile.versionNumber,'subsystem_versions':versions,'model_items':684,'solid_bodies':703,'native_display_definitions':len(mesh_cache),'display_triangles':sum(len(m['faces'])for m in meshes.values()),'display_surface_tolerance_mm_max':result['native_migration']['display_surface_tolerance_mm_max'],'verified_reused_meshes':len(reuse_checks),'source_target_sha256':TARGET,'elapsed_seconds':time.monotonic()-tick,'native_source_of_truth':False}))
'''
for token, value in [('INVENTORY', inventory['instances']), ('META', metadata), ('PARAMETERS', source['parameters']), ('POSES', source['poses']), ('TARGET', target['model_sha256']), ('CONTACT_RULES',contact_rules)]:
    script = script.replace(token, repr(value))
compile(script, 'export_current_native_robot.py', 'exec')
reply = rpc(script, 'current-native-whole-bounded-display-export', timeout=900, read_only=True)
assert reply[0]['success'], reply
record = json.loads(reply[0]['message'])
(ROOT / 'audits/current-native-whole-bounded-display-export.json').write_text(json.dumps(record, indent=2))
folder = 'whole-native-master-' + str(record['saved_master_version'])
fetch(record['path'], folder + '/native-whole-bounded-display-candidate.json.gz')
print(record)
