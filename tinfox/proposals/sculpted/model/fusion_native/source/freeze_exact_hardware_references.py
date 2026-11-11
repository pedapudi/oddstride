"""Recover BRep hardware references without importing any custom design part."""
import gzip,hashlib,json,sys
from pathlib import Path
import numpy as np
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1];MODEL=ROOT.parent
manifest=json.loads((ROOT/'manifests/current-hardware-references.json').read_text());variant=manifest['variants']['low'];frozen=json.loads(gzip.decompress((ROOT/variant['frozen_geometry']).read_bytes()));custom={p['key'] for p in json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low']['custom_parts']};assert not custom.intersection(frozen['meshes'])
assembly_path=MODEL/'output/service-design/updated-robot.step';assembly=cq.Assembly.importStep(str(assembly_path));objects=assembly.objects;folder=ROOT/'snapshots/current-hardware'/variant['source_model_sha256']/'exact-reference-step';folder.mkdir(exist_ok=True);rows=[];groups={};references={}
search=[MODEL/'output/limb-refinement/step',MODEL/'output/low-lidar-reference/step',MODEL/'output/integrated-candidate/step',MODEL/'output/service-design/step',MODEL/'output/step-parts']
for entry in variant['reference_meshes']:
 key=entry['key'];assert key not in custom;part=next(p for p in frozen['parts'] if p['mesh']==key);mesh=frozen['meshes'][key];points=np.asarray(mesh['vertices']);wanted_volume=part.get('volume_mm3');candidates=[]
 for base in search:
  path=base/(key+'.step')
  if path.exists():candidates.append((cq.importers.importStep(str(path)).val(),str(path.relative_to(MODEL))))
 for instance in entry['instances']:
  obj=objects.get(instance['name'])
  if obj and obj.obj is not None:candidates.append((obj.obj.val() if isinstance(obj.obj,cq.Workplane) else obj.obj,str(assembly_path.relative_to(MODEL))+'#'+instance['name']));break
 attempts=[];chosen=None
 for shape,source in candidates:
  volume=shape.Volume();difference=abs(volume-wanted_volume) if wanted_volume is not None else float('inf')
  motor_reference=key.startswith(('hip_motor','knee_motor','roll_motor_'))
  if difference>max(.002,abs(wanted_volume)*1e-7) and not motor_reference:attempts.append({'source':source,'volume_error_mm3':difference});continue
  offset=np.zeros(3) if motor_reference else np.asarray(part['com_mm'])-np.asarray(shape.Center().toTuple());adjusted=shape.translate(tuple(offset));boundary=cq.Compound.makeCompound(adjusted.Faces());indices=np.linspace(0,len(points)-1,(len(points) if motor_reference else min(80,len(points))),dtype=int);error=max(boundary.distance(cq.Vertex.makeVertex(*p)) for p in points[indices]);attempts.append({'source':source,'volume_error_mm3':difference,'translation_mm':offset.tolist(),'maximum_frozen_vertex_boundary_distance_mm':error})
  if error<.001:chosen=(adjusted,source,offset,error,difference);break
 if chosen is None:rows.append({'key':key,'state':'exact_reference_unavailable','attempts':attempts});continue
 shape,source,offset,error,difference=chosen;path=folder/(key+'.step');cq.exporters.export(shape,str(path));sha=hashlib.sha256(path.read_bytes()).hexdigest();references[key]=shape;rows.append({'key':key,'state':'source_matched_reference','path':str(path.relative_to(ROOT)),'sha256':sha,'source':source,'translation_mm':offset.tolist(),'frozen_mesh_sha256':entry['mesh_sha256'],'volume_error_mm3':difference,'sampled_frozen_vertex_boundary_error_mm':error,'samples':(len(points) if motor_reference else min(80,len(points))),'custom_native_authoring':False,'source_metadata_consistent':difference<=max(.002,abs(wanted_volume)*1e-7),'metadata_note':'Service motor meshes and exact assembly include socket recesses, but service_design.register did not refresh the old volume/COM fields. Motor reference is matched at its original datum, without COM translation.' if motor_reference else None})
for part in frozen['parts']:
 if part['mesh'] not in references:continue
 group=(part.get('leg') or 'Body')+'_'+part['group'];groups.setdefault(group,cq.Assembly(name=group+' purchased references'));groups[group].add(references[part['mesh']],name=part['name'])
group_records=[]
for key,group in groups.items():
 path=folder/(key+'-reference-assembly.step');group.save(str(path));group_records.append({'group':key,'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'instances':len(group.children)})
record={'source_model_sha256':variant['source_model_sha256'],'parts':rows,'groups':group_records,'exact_reference_count':len(references),'missing_count':len(rows)-len(references),'scope':'Reference hardware only. No custom part is included. Source BReps matched to frozen volume, center and sampled mesh vertices; supplied stock dimensions and material properties remain unqualified.'};(ROOT/'manifests/current-exact-hardware-references.json').write_text(json.dumps(record,indent=2));print({'exact':record['exact_reference_count'],'missing':record['missing_count'],'groups':len(groups)});print('missing',[r['key'] for r in rows if r['state']=='exact_reference_unavailable'])
