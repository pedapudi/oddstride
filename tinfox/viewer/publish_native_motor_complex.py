"""Publish the approved native motor-complex export without rebuilding its geometry."""
import argparse
import gzip
import hashlib
import json
import os
from urllib.parse import urljoin
from collections import Counter
from pathlib import Path

from catalog_io import read_catalog, write_catalog

ROOT = Path(__file__).resolve().parent
TINFOX = ROOT.parent
NATIVE = TINFOX/'proposals/sculpted/model/fusion_native'
KEYS = {'hip_hub','motor_mount_ring','thigh_inner','thigh_outer','input_crank',
        'roll_cartridge_1','roll_stator_backplate_1','roll_inner_spacer_1','roll_outer_spacer_1',
        'roll_inner_backplate_1','roll_outer_retainer_1','motor_carrier_1','hip_stator_closure_1'}
LABELS = {'hip_hub':'Hip output hub','motor_mount_ring':'Knee stator plate',
          'thigh_inner':'Inner structural thigh','thigh_outer':'Outer structural thigh',
          'input_crank':'Knee input crank','roll_cartridge_1':'Paired-bearing housing',
          'roll_stator_backplate_1':'Roll stator backplate','roll_inner_spacer_1':'Inner race spacer',
          'roll_outer_spacer_1':'Outer race spacer','roll_inner_backplate_1':'Inner bearing backplate',
          'roll_outer_retainer_1':'Outer bearing retainer','motor_carrier_1':'Roll output motor carrier',
          'hip_stator_closure_1':'Removable hip stator flange'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def local(path):
    path = path.resolve()
    assert path.is_relative_to(TINFOX.resolve()) and path.is_file(), path
    return Path(os.path.relpath(path,ROOT)).as_posix()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,default=NATIVE/'manifests/motor-complex-native-exports.json')
    parser.add_argument('--candidate',action='store_true',help='Stage a private unapproved preview without changing the current catalog.')
    parser.add_argument('--print-package',type=Path,help='Add prepared part downloads from a matching native print package.')
    args = parser.parse_args()
    authority = json.loads(args.manifest.read_text())
    integrated = authority.get('assembly_architecture') == 'integrated-dfma'
    keys = KEYS - {'hip_hub', 'motor_mount_ring', 'hip_stator_closure_1'} if integrated else KEYS
    inventory = authority.get('assembly_inventory', {'custom_parts':13,'cut_stock_bodies':8,
        'purchased_references':103,'motors':3,'connector_bodies':24,'total_visible_bodies':124})
    assembly_ready = authority.get('assembly_release_ready') is True
    assert authority['native_source_of_truth'] is True or args.candidate, 'Native authority has not been approved.'
    assert set(authority['parts']) == keys
    if args.print_package:
        assert not args.candidate
        assert assembly_ready,'Complete assembly print release is withheld.'
        package = args.print_package.resolve()
        prepared = json.loads((package/'manifest.json').read_text())
        assert prepared['source_kind'] == 'fusion-native'
        assert prepared['source_manifest_sha256'] == sha(args.manifest.read_bytes())
        hashes = dict(line.split('  ',1)[::-1] for line in (package/'SHA256SUMS').read_text().splitlines())
        for key in keys:
            for relative in [f'individual-stl/{key}.stl',f'individual-3mf/{key}.3mf']:
                assert sha((package/relative).read_bytes()) == hashes[relative],relative
    model_bytes = args.model.read_bytes()
    raw = gzip.decompress(model_bytes) if args.model.suffix == '.gz' else model_bytes
    data = json.loads(raw)
    expected = authority.get('review_model_sha256')
    assert expected and sha(raw) == expected, 'Review model needs its native provenance hash.'
    assert all(part.get('leg') is None for part in data['parts']), 'Static review cannot use generated leg transforms.'
    roles = Counter(part.get('reference_role') for part in data['parts'])
    assert inventory['custom_parts']==len(keys) and inventory['cut_stock_bodies']==(6 if integrated else 8)
    assert inventory['motors']==3 and inventory['connector_bodies']==24
    assert roles['custom_structure'] == len(keys) and roles['cut_stock'] == inventory['cut_stock_bodies'], roles
    assert roles['vendor_motor'] == 3 and roles['standard_hardware'] == inventory['purchased_references']-27, roles
    assert all(roles[role] == 6 for role in ['connector_socket','connector_plug','connector_boot','connector_cable']), roles
    assert len(data['parts']) == inventory['total_visible_bodies'], 'Unexpected or stale geometry in the native bench export.'
    meshes = data['meshes']
    assert all(part['mesh'] in meshes for part in data['parts'])
    counts = Counter(part['mesh'] for part in data['parts'])
    assert all(counts[key] == 1 for key in keys), 'Each native custom definition needs one visible occurrence.'
    motors = [part for part in data['parts'] if part['name'].endswith(('_roll_motor','_hip_motor','_knee_motor'))]
    assert len(motors) == 3
    rows = []
    for key,count in counts.items():
        instances = [part for part in data['parts'] if part['mesh']==key]
        part = instances[0]
        bounds = part['bounds_mm']
        dimensions = [bounds[i+3]-bounds[i] for i in range(3)] if len(bounds)==6 else [bounds[1][i]-bounds[0][i] for i in range(3)]
        row = {'id':key,'label':LABELS.get(key,part['name'].replace('_',' ')),
               'instances':[part['name'] for part in instances],'quantity':count,
               'category':'Legs' if key in keys else 'Sensors and wiring' if part.get('reference_role','').startswith('connector_') else 'Hardware',
               'custom':key in keys,'material':part.get('material','envelope'),
               'mass_kg':0,'dimensions_mm':dimensions,
               'note':'Native editable Fusion custom part. Supported, unpowered fit prototype.' if key in keys
                      else 'Purchased hardware reference; verify actual part dimensions before assembly.'}
        if key in keys:
            native = authority['parts'][key]
            assert native.get('saved_version'), key
            step = NATIVE/native['native_step']
            assert sha(step.read_bytes()) == native['native_step_sha256'], key
            row['step'] = local(step)
            if args.print_package:
                row['print_stl'] = local(package/'individual-stl'/f'{key}.stl')
                row['print_3mf'] = local(package/'individual-3mf'/f'{key}.3mf')
        rows.append(row)
    model_hash = sha(raw)
    destination = ROOT/'.native-candidate' if args.candidate else ROOT
    destination.mkdir(exist_ok=True)
    report = destination/'audit.json' if args.candidate else ROOT/'checks/native-motor-complex-review.json'
    report.write_text(json.dumps({'model_sha256':model_hash,'motion_samples':[],
        'native_source_manifest':local(args.manifest),'scope':'Static native motor-complex review. See the saved native migration audits for assembly-access evidence. No live pose check or strength qualification is implied.'},indent=2))
    design = {'id':'native-motor-complex','title':'Native Fusion · three-motor assembly',
        'description':f'Saved native hip/thigh motor complex with {len(keys)} editable custom parts and three RS02 motors. Inspect assembly sections, separate motors and connectors, and individual structural parts.',
        'model':local(args.model),'model_sha256':model_hash,'audit':local(report),'assembly':None,
        'estimated_mass_kg':None,'physical_components':len(data['parts']),
        'scope':f'Detached, supported, unpowered fit assembly. Saved native geometry is canonical for these {len(keys)} custom parts. Whole-robot motion, printed strength and loaded operation remain separate checks.',
        'scope_label':'Motor complex','presentation':'motor-complex','motion_available':False,
        'live_check_available':False,'default_focus':'all','archived':False,'lifecycle':'current-review',
        'source':{'kind':'fusion-native','label':'Native Fusion · canonical motor complex',
                  'manifest':local(args.manifest),'manifest_sha256':sha(args.manifest.read_bytes())},
        'reports':[{'title':'Native source and export provenance','url':local(args.manifest)}],
        'parts':sorted(rows,key=lambda row:(not row['custom'],row['label']))}
    if integrated:
        labels = {'motor_carrier_1':'Integral rear-loaded hip cup',
                  'roll_outer_retainer_1':'Shared bearing cap and stator clamp',
                  'thigh_inner':'Primary structural motor cradle and thigh',
                  'thigh_outer':'Secondary structural motor cover and thigh'}
        for row in rows:
            row['label'] = labels.get(row['id'], row['label'])
    if not assembly_ready:
        design['source']['label']='Native Fusion geometry · assembly release withheld'
        design['scope']=authority.get('manufacturing_scope','Complete assembly release is withheld.')
    if args.candidate:
        design['source'].update(kind='fusion-native-candidate',label='Native Fusion candidate · promotion pending')
        design['scope'] = 'Unapproved native revision. The last published geometry retains authority until this candidate passes its remaining checks.'
        for key in ['model','audit']:
            design[key] = urljoin('/viewer/',design[key])
        for row in design['parts']:
            if row.get('step'):row['step'] = urljoin('/viewer/',row['step'])
        for row in design['reports']:row['url'] = urljoin('/viewer/',row['url'])
        (destination/'catalog.json').write_text(json.dumps({'current_design':design['id'],'designs':[design]}))
        for name in ['index.html','viewer.css','cad-shading.js','vendor','README.md','archive']:
            path=destination/name
            if not path.exists():path.symlink_to(ROOT/name,target_is_directory=(ROOT/name).is_dir())
        (destination/'viewer.js').write_text((ROOT/'viewer.js').read_text().replace("fetch('../design/appearance.json')","fetch('/design/appearance.json')"))
        releases=json.loads((ROOT/'releases.json').read_text())
        for release in releases['releases']:
            for key in ['archive','guide','first_plate']:
                if release.get(key):release[key]=urljoin('/viewer/',release[key])
        (destination/'releases.json').write_text(json.dumps(releases))
        print(json.dumps({'candidate_url':'http://127.0.0.1:8770/viewer/.native-candidate/','current_catalog_unchanged':True}))
        return
    catalog = read_catalog(ROOT)
    catalog['designs'] = [d for d in catalog['designs'] if d['id'] != design['id']]
    whole = next((d for d in catalog['designs'] if d.get('source',{}).get('kind') == 'fusion-native'
                  and d.get('presentation') == 'whole-robot' and not d.get('archived')),None)
    for previous in catalog['designs']:
        if not previous.get('archived') and previous.get('source',{}).get('kind') == 'generated-reference':
            previous['source']['label'] = 'Generated whole-robot reference · predates native motor-complex release'
            previous['lifecycle'] = 'reference-only'
            previous['defer_details'] = True
    catalog['designs'].insert(1 if whole else 0,design)
    catalog['current_design'] = whole['id'] if whole else design['id']
    write_catalog(ROOT,catalog)
    print(json.dumps({'current_design':catalog['current_design'],'custom_parts':len(keys),'components':len(data['parts']),'model_sha256':model_hash},indent=2))


if __name__ == '__main__':
    main()
