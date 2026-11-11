"""Prepare purchased hardware and envelope references for the native assembly.

Only parts excluded from the custom-part native manifest are eligible. Their
meshes remain explicitly marked references; they do not satisfy or enter the
native custom-part authoring gate. No custom structural geometry is imported.
API: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_MeshBodies_addByTriangleMeshData.htm
"""
import json,gzip,hashlib,sys
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]

def prepare():
 manifest=json.loads((ROOT/'manifests/parts.json').read_text());path=ROOT/manifest.get('reference_model','snapshots/reference-model.json.gz');model=json.loads(gzip.decompress(path.read_bytes()));custom={p['id'] for p in manifest['parts']}
 rows=[];meshes={}
 for part in model['parts']:
  if part['mesh'] in custom or part.get('service_role'):continue
  assert part['material'] in ['steel','envelope'],('Review nonstandard part before reference import',part['name'],part['material'])
  mesh=model['meshes'][part['mesh']];identity=hashlib.sha256(json.dumps(mesh,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  rows.append({'key':part['mesh'],'name':part['name'],'leg':part.get('leg'),'kinematic_group':part['group'],'color':part['color'],'material':part['material'],'mass_kg':part.get('mass_kg'),'mesh_sha256':identity,'authoring_role':'purchased hardware or placement envelope reference'})
  meshes[part['mesh']]=mesh
 result={'custom_part_ids_excluded':sorted(custom),'reference_model_archive_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'parts':rows,'meshes':meshes,'scope':'Reference geometry only. These bodies are excluded from native custom-part completeness and shape gates.'}
 (ROOT/'snapshots/reference-hardware.json.gz').write_bytes(gzip.compress(json.dumps(result,separators=(',',':')).encode(),mtime=0));print('Prepared',len(rows),'hardware/envelope reference instances. No Fusion changes.')
 return result

def install(data):
 script='''import adsk.core as core,adsk.fusion as fusion,json

def run(_context: str):
 app=core.Application.get();master=next(doc for doc in app.documents if doc.name.startswith('Tinfox - Native Master Assembly'));master.activate();design=fusion.Design.cast(app.activeProduct)
 group=next(o.component for o in design.rootComponent.occurrences if o.component.name=='Purchased references')
 assert group.occurrences.count==0,'References already exist; reconcile before repeating'
 custom=set(DATA['custom_part_ids_excluded']);records=[]
 for key,mesh in DATA['meshes'].items():
  assert key not in custom
  occurrence=group.occurrences.addNewComponent(core.Matrix3D.create());component=occurrence.component
  component.name='Reference - '+key;component.partNumber='REF_'+key
  component.attributes.add('Tinfox','AuthoringRole','Purchased hardware or placement envelope. Not a native custom part.')
  coordinates=[v*.1 for point in mesh['vertices'] for v in point];indices=[index for triangle in mesh['faces'] for index in triangle]
  body=component.meshBodies.addByTriangleMeshData(coordinates,indices,[],[]);assert body is not None
  body.name='Reference geometry - '+key
  records.append({'source_mesh':key,'native_reference_part_number':component.partNumber,'mesh_body_count':component.meshBodies.count,'custom_part':False})
 master.save('Add explicitly marked purchased hardware references; custom parts retain native features.')
 print(json.dumps({'references':records,'source_instances':DATA['parts'],'custom_part_import_count':0}))
'''.replace('DATA',repr(data))
 response=rpc(script,'hardware-references',timeout=900);assert response[0].get('success'),response
 (ROOT/'manifests/hardware-references.json').write_text(json.dumps(json.loads(response[0]['message']),indent=2))
if __name__=='__main__':
 data=prepare()
 if '--install' in sys.argv:install(data)
