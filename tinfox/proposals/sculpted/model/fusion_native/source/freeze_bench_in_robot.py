"""Freeze a whole-robot migration reference using the audited native bench exports.

This combines references for conversion audits. It does not publish a browser
candidate, prepare manufacturing files or change native source authority.
"""
import copy
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import trimesh

NATIVE = Path(__file__).resolve().parents[1]
MODEL = NATIVE.parent
sys.path.insert(0,str(MODEL))
from prepare_native_motor_complex import read_3mf

BASE_HASH = 'b968fea927022ba467e05eb52ab602a680e14fd7295c263eefcb95a58a90cdc6'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def mapping(part, original):
    name = part['name']
    aliases = {'mc_roll_motor':'FL_roll_motor','mc_hip_motor':'FL_hip_motor','mc_knee_motor':'FL_knee_motor'}
    name = aliases.get(name,name)
    if name in original:return name,original[name]['group']
    patterns=[(r'Pod M3x60 screw (\d+)','FL_pod_tie_{}','thigh'),
              (r'Pod M3 nut (\d+)','FL_pod_tie_nut_{}','thigh'),
              (r'Hip output M4x8 (\d+)','FL_hip_output_bolt_{}','thigh'),
              (r'Knee output M4x12 (\d+)','FL_input_bolt_{}','crank'),
              (r'Knee stator M3x8 (\d+)','FL_knee_stator_bolt_{}','thigh')]
    for pattern,template,group in patterns:
        match = re.fullmatch(pattern,name)
        if match:return template.format(match[1]),group
    raise ValueError(('Unmapped purchased reference',name))


def reflect(mesh, front, side, roll_axis=False):
    result=mesh.copy()
    matrix=np.eye(4)
    if roll_axis:matrix[0,0]=front
    matrix[1,1]=side
    result.apply_transform(matrix)
    return result


def properties(mesh):
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0
    return dict(volume_mm3=float(mesh.volume),com_mm=mesh.center_mass.tolist(),bounds_mm=mesh.extents.tolist())


def freeze():
    authority_file=NATIVE/'manifests/motor-complex-native-exports.json'
    authority=json.loads(authority_file.read_text())
    assert authority['native_source_of_truth'] is True, 'Freeze from the promoted native bench.'
    model_path=MODEL/'output/paired-roll-work/model.json'
    raw=model_path.read_bytes();assert sha(raw)==BASE_HASH
    data=json.loads(raw);original={p['name']:copy.deepcopy(p) for p in data['parts']}
    body_meshes={p['mesh']:sha(json.dumps(data['meshes'][p['mesh']],sort_keys=True).encode())
                 for p in data['parts'] if not p.get('leg')}
    review_path=NATIVE/authority['review_model']
    bench_raw=gzip.decompress(review_path.read_bytes())
    assert sha(bench_raw)==authority['review_model_sha256']
    bench=json.loads(bench_raw)
    changes=[];new_steps={};native_rows={p['mesh']:p for p in bench['parts'] if p['reference_role']=='custom_structure'}
    # Refresh all canonical proximal definitions, including later native edits.
    # Rear carriers keep the source's separately constructed journal/web reversal.
    common={'hip_hub','motor_mount_ring','thigh_inner','thigh_outer','input_crank'}
    definitions={**authority['parts'],**authority.get('related_native_parts',{})}
    for key,row in definitions.items():
        source=NATIVE/row['native_3mf'];assert sha(source.read_bytes())==row['native_3mf_sha256']
        left=read_3mf(source)
        explicit_right=key.endswith('_right')
        base_key=key.removesuffix('_right')
        explicit_rear=base_key.endswith('_-1')
        fronts=[-1] if explicit_rear else [1] if base_key in common or base_key=='motor_carrier_1' or base_key[:-1]+'-1' in definitions else [1,-1]
        sides=[-1] if explicit_right else [1] if key+'_right' in definitions else [1,-1]
        for front in fronts:
            x_reflection=front<0 and base_key.startswith('roll_') and not explicit_rear
            translation=-2*data['parameters']['pitch_x_offset'] if front<0 and base_key=='hip_stator_closure_1' else 0
            for side in sides:
                mesh=reflect(left,front,1 if explicit_right else side,x_reflection);mesh.apply_translation([translation,0,0])
                stem=base_key if front>0 or explicit_rear else base_key[:-1]+'-1'
                mesh_key=stem+('_right' if side<0 else '')
                assert mesh_key in data['meshes'],mesh_key
                data['meshes'][mesh_key]={'vertices':mesh.vertices.tolist(),'faces':mesh.faces.tolist()}
                props=properties(mesh)
                for part in data['parts']:
                    if part['mesh']!=mesh_key:continue
                    density=part['mass_kg']/part['volume_mm3']
                    part.update(props,mass_kg=props['volume_mm3']*density)
                    part['note']='Audited native motor-complex geometry, propagated by explicit reflections/translations for whole-robot migration comparison. Physical bearing fit and loaded operation remain unqualified.'
                    changes.append({'instance':part['name'],'native_part':key,'handed_y_reflection':side<0,
                        'rear_x_reflection':x_reflection,'translation_x_mm':translation,'group':part['group']})
                new_steps[mesh_key]={'native_step':row['native_step'],'native_step_sha256':row['native_step_sha256'],
                    'reflect_y':side<0,'reflect_x':x_reflection,'translation_x_mm':translation}
    reference_rows=[];stock_rows=[]
    for part in bench['parts']:
        if part['reference_role']=='custom_structure':continue
        source_mesh=bench['meshes'][part['mesh']]
        mesh=trimesh.Trimesh(vertices=source_mesh['vertices'],faces=source_mesh['faces'],process=False)
        mesh.merge_vertices(digits_vertex=7)
        if part['reference_role']=='cut_stock':stock_rows.append((part,mesh));continue
        name,group=mapping(part,original)
        reference_rows.append((part,mesh,name,group))
    purchased_count=authority.get('assembly_inventory',{}).get('purchased_references',103)
    assert len(reference_rows)==purchased_count and len(stock_rows)==8
    mapped_left={name for _,_,name,_ in reference_rows}
    removed=[p['name'] for p in data['parts'] if p.get('leg') and
             p['name'].startswith(p['leg']+'_carrier_closure_washer_') and
             'FL'+p['name'][2:] not in mapped_left]
    data['parts']=[p for p in data['parts'] if p['name'] not in removed]
    # Compound two pod sleeve bodies under each existing cut-stock component ID.
    stocks={}
    for part,mesh in stock_rows:
        name=part['name'].rsplit(' ',1)[0] if part['name'].startswith('pod_sleeve_') else part['name']
        stocks.setdefault(name,[]).append(mesh)
    assert len(stocks)==5
    replaced=[];added=[]
    for leg,front,side in [('FL',1,1),('FR',1,-1),('RL',-1,1),('RR',-1,-1)]:
        for source,mesh,left_name,group in reference_rows:
            name=leg+left_name[2:]
            roll_axis=left_name=='FL_roll_motor' or left_name.startswith(('FL_roll_port_','FL_roll_bearing_','FL_roll_stator_','FL_roll_retainer_','FL_roll_output_'))
            placed=reflect(mesh,front,side,roll_axis)
            if group in ['mount','roll']:placed.apply_translation([front*data['parameters']['pitch_x_offset'],0,0])
            key='bench_reference_'+name
            data['meshes'][key]={'vertices':placed.vertices.tolist(),'faces':placed.faces.tolist()}
            old=original.get(name)
            props=properties(placed)
            record=copy.deepcopy(old) if old else {'name':name,'leg':leg,'group':group,'check':False,'color':'#A1AAA4'}
            material=old['material'] if old else 'steel'
            mass=old['mass_kg'] if old else props['volume_mm3']*7.85e-6
            if source['reference_role']=='vendor_motor':mass=.405
            elif material=='steel':mass=props['volume_mm3']*7.85e-6
            record.update(props,mesh=key,material=material,mass_kg=mass,
                note='Purchased reference from the audited native bench inventory. Actual supplier geometry, stock and physical fits require confirmation.')
            if old:data['parts'][next(i for i,p in enumerate(data['parts']) if p['name']==name)]=record;replaced.append(name)
            else:data['parts'].append(record);added.append(name)
            changes.append({'instance':name,'bench_instance':source['name'],'group':group,
                'roll_axis_x_reflection':front<0 and roll_axis,'handed_y_reflection':side<0,
                'neutral_to_group_translation_mm':[front*data['parameters']['pitch_x_offset'] if group in ['mount','roll'] else 0,0,0]})
        for suffix,meshes in stocks.items():
            name=leg+'_'+suffix;old=original[name];placed=reflect(trimesh.util.concatenate(meshes),front,side)
            key='bench_stock_'+name;props=properties(placed)
            data['meshes'][key]={'vertices':placed.vertices.tolist(),'faces':placed.faces.tolist()}
            record=copy.deepcopy(old);density=old['mass_kg']/old['volume_mm3'] if old['volume_mm3'] else 0
            record.update(props,mesh=key,mass_kg=props['volume_mm3']*density,
                note='Native cut-stock reference: pod tubes OD5/ID3.4 at41mm and6mm; thigh tubes OD8/ID4.3 at18mm. Printed surrogates are fit-only.')
            data['parts'][next(i for i,p in enumerate(data['parts']) if p['name']==name)]=record;replaced.append(name)
    assert len(added)==48 and len(data['parts'])==len(original)+48-len(removed)
    assert len({p['name'] for p in data['parts']})==len(data['parts'])
    # Body, head, shin and linkage geometry are frozen source references.
    for part in data['parts']:
        if not part.get('leg'):
            assert part==original[part['name']]
            assert sha(json.dumps(data['meshes'][part['mesh']],sort_keys=True).encode())==body_meshes[part['mesh']]
    used={p['mesh'] for p in data['parts']};data['meshes']={k:v for k,v in data['meshes'].items() if k in used}
    scope={'purpose':'Whole-robot native migration target; not an authoritative CAD or manufacturing release.',
        'generated_whole_reference_sha256':BASE_HASH,'native_bench_manifest_sha256':sha(authority_file.read_bytes()),
        'native_bench_review_sha256':sha(bench_raw),'source_of_truth':False,
        'body_head_unchanged':True,'new_purchased_instances':48,
        'removed_purchased_instances':len(removed),
        'existing_limitations':'Retain known generated-source body contacts. Updated whole-robot motion/interference and linkage closure require audit; prior reports do not validate this composite.'}
    data['integration_reference']=scope
    data['status']=scope['purpose']
    encoded=json.dumps(data,separators=(',',':')).encode();identity=sha(encoded)
    folder=NATIVE/'snapshots/whole-robot-integration'/identity;folder.mkdir(parents=True,exist_ok=False)
    (folder/'model.json.gz').write_bytes(gzip.compress(encoded,mtime=0))
    manifest={**scope,'model_sha256':identity,'reference_model':str((folder/'model.json.gz').relative_to(NATIVE)),
        'parts':len(data['parts']),'native_custom_deltas':new_steps,'instance_mappings':changes,
        'physical_components':sum(p.get('service_role') not in ['keepout','withdrawal'] for p in data['parts']),
        'nonphysical_reservations':sum(p.get('service_role') in ['keepout','withdrawal'] for p in data['parts']),
        'whole_robot_canonical':False,
        'replaced_purchased_and_stock_instances':replaced,'added_purchased_instances':added,
        'removed_reference_instances':removed,
        'benchmark_source_units':'mm','estimated_base_mass_kg':sum(p['mass_kg'] for p in data['parts'])}
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2))
    (NATIVE/'manifests/whole-robot-integration-target.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({'snapshot':str(folder),'model_sha256':identity,'parts':len(data['parts']),'added_purchased_instances':len(added)},indent=2))


if __name__=='__main__':freeze()
