"""Freeze the source geometry identity and track the native migration gate."""
import json,hashlib,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];NATIVE=ROOT/'fusion_native'
source=ROOT/'output/service-design/model.json';raw=source.read_bytes();data=json.loads(raw)
parts={}
for p in data['parts']:
 k=p['mesh']
 if p.get('service_role') or p['material']=='envelope':continue
 if p['material']=='steel' and not any(q in k for q in ['pushrod','knee_axle','knee_inner_spacer']):continue
 if k not in parts:
  group=('Body and chassis' if not p.get('leg') else 'Shared leg designs')
  if k.startswith(('electronics','lidar','power_button','sensor_')):group='Electronics and sensors'
  parts[k]={'id':k,'label':k.replace('_',' ').capitalize(),'group':group,'material':p['material'],'instances':[],
    'source_mesh_sha256':hashlib.sha256(json.dumps(data['meshes'][k],sort_keys=True,separators=(',',':')).encode()).hexdigest(),
    'source_volume_mm3':p['volume_mm3'],'source_bounds_mm':p['bounds_mm'],
    'state':'pending_source_freeze' if k in ['body_nose_surround','body_aft_0'] else 'planned',
    'native_document':None,'native_component':None,'native_feature_count':0,'audits':{},'manufacturing_release':False}
 parts[k]['instances'].append({'name':p['name'],'leg':p.get('leg'),'kinematic_group':p['group']})
manifest={'schema':1,'updated_utc':datetime.datetime.now(datetime.UTC).isoformat(),'authoritative_source':'CadQuery service-design model until migration gate passes',
 'source_model_sha256':hashlib.sha256(raw).hexdigest(),'source_file':str(source.relative_to(ROOT)),
 'fusion_project':{'planned_name':'Tinfox','created':False,'id':None},
 'fusion_document':{'planned_name':'Tinfox - Native Master Assembly','created':False,'id':None},
 'migration_gate':{'passed':False,'requirements':['Every custom part constructed with native named timeline features and editable sketches.','No imported mesh, STEP, or replacement BRep authoring.','Volume, area, bounds, symmetric sampled surface deviation and critical sections match frozen source within explicitly reported tolerances.','Hole and bearing datums, connector volumes, link dimensions and instance transforms verified.','Visual comparison of front, side and isometric silhouettes.','Sampled collision and service path checks preserve or improve source results.','Parameter edit, recompute and restore test on scratch copy passes.','Native archive reopens with the expected timeline, parameters, components and instances.']},
 'parts':list(parts.values())}
(NATIVE/'manifests/parts.json').write_text(json.dumps(manifest,indent=2))
(NATIVE/'snapshots/source-model-identity.json').write_text(json.dumps({'model_sha256':manifest['source_model_sha256'],'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'build.py',ROOT/'service_design.py',ROOT/'parameters.json',ROOT/'kinematics.py']}},indent=2))
print('Inventory:',len(parts),'unique custom geometries;',sum(len(x['instances']) for x in parts.values()),'instances. Native parts completed: 0.')
