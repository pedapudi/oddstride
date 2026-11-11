"""Combine canonical native motor interfaces with unchanged auxiliary fit gauges."""
import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import cadquery as cq
import trimesh
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cone
from prepare_mac_print_package import arrange,write_3mf

ROOT=Path(__file__).resolve().parent
NATIVE=ROOT/'fusion_native'
GAUGES=ROOT/'output/print-handoff/Tinfox-Motor-Fit-20261029T044755Z'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--complex-package',type=Path,required=True)
    parser.add_argument('--safe-only',action='store_true',help='Prepare only the two case gauges and unchanged native output hub.')
    parser.add_argument('--gauges-only',action='store_true',help='Omit every robot component; prepare only the two auxiliary case gauges.')
    args=parser.parse_args();source=args.complex_package.resolve()
    if args.gauges_only:args.safe_only=True
    source_manifest=json.loads((source/'manifest.json').read_text())
    authority_path=(NATIVE/source_manifest.get('source_manifest_relative','manifests/motor-complex-native-exports.json')).resolve()
    assert authority_path.is_relative_to((NATIVE/'manifests').resolve())
    authority=json.loads(authority_path.read_text());assert authority['native_source_of_truth'] is True
    integrated=authority.get('assembly_architecture')=='integrated-dfma'
    assert not (integrated and args.safe_only and not args.gauges_only), 'The integrated assembly has no separate output hub.'
    assert source_manifest['source_kind']=='fusion-native'
    if args.safe_only and not args.gauges_only:
        hub=next(p for p in source_manifest['parts'] if p['part']=='hip_hub')['source']
        for key in ['native_step_sha256','native_3mf_sha256']:assert hub[key]==authority['parts']['hip_hub'][key]
    elif not args.gauges_only:
        assert source_manifest['source_manifest_sha256']==sha(authority_path)
        assert authority.get('assembly_release_ready') is True
    source_hashes=dict(line.split('  ',1)[::-1] for line in (source/'SHA256SUMS').read_text().splitlines())
    gauge_hashes=dict(line.split('  ',1)[::-1] for line in (GAUGES/'SHA256SUMS').read_text().splitlines())
    cones=[]
    if not integrated and not args.safe_only:
        # The legacy package needs its motion-corrected countersunk stator plate.
        plate=cq.importers.importStep(str(source/'reference-step/motor_mount_ring.step')).val()
        for face in plate.Faces():
            surface=BRepAdaptor_Surface(face.wrapped)
            if surface.GetType()!=GeomAbs_Cone:continue
            cone=surface.Cone();point=cone.Location();direction=cone.Axis().Direction()
            if abs(abs(direction.Y())-1)<1e-6 and abs((point.X()**2+point.Z()**2)**.5-36.5)<1e-5:cones.append(cone)
        assert len(cones)==9,'Knee stator plate needs its nine motion-clearance countersinks.'
    items=[];records=[];files=[]
    for key in ['01-thigh-case-gauge-80p50','02-hip-case-gauge-81p50']:
        rel=f'individual-stl/{key}.stl';assert sha(GAUGES/rel)==gauge_hashes[rel]
        mesh=trimesh.load_mesh(GAUGES/rel,process=True)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0
        items.append((key,mesh));files.append((GAUGES/rel,rel))
        step=f'reference-step/{key}.step';assert sha(GAUGES/step)==gauge_hashes[step];files.append((GAUGES/step,step))
        records.append({'part':key,'source_kind':'generated-auxiliary-gauge','source_package':GAUGES.name,'source_stl_sha256':gauge_hashes[rel],'robot_component':False})
    interfaces=([('thigh_inner','03-integrated-primary-motor-cradle')] if integrated else
                [('motor_mount_ring','03-knee-stator-plate'),('hip_stator_closure_1','04-hip-stator-flange'),('hip_hub','05-hip-output-hub')])
    for key,label in interfaces:
        if args.gauges_only:continue
        if args.safe_only and key!='hip_hub':continue
        rel=f'individual-stl/{key}.stl';assert sha(source/rel)==source_hashes[rel]
        mesh=trimesh.load_mesh(source/rel,process=True)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0
        items.append((label,mesh));files.append((source/rel,f'individual-stl/{label}.stl'))
        for directory,suffix in [('reference-step','step'),('native-3mf','3mf')]:
            relative=f'{directory}/{key}.{suffix}';assert sha(source/relative)==source_hashes[relative]
            files.append((source/relative,f'{directory}/{label}.{suffix}'))
        records.append({'part':label,'source_kind':'fusion-native','native_part':key,'native_source':authority['parts'][key]})
    label=f'Tinfox-Motor-Interface-Fit-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}'
    target=ROOT/'output/print-handoff'/label;target.mkdir(parents=True,exist_ok=False)
    for path,relative in files:
        destination=target/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,destination)
    placed=arrange(items);write_3mf(target/'00-RS02-motor-fit.3mf',placed)
    shutil.copy2(authority_path,target/'native-source-manifest.json')
    (target/'manifest.json').write_text(json.dumps({'source_kind':'generated-auxiliary-gauges' if args.gauges_only else 'native-interfaces-with-generated-gauges','source_manifest_sha256':sha(authority_path),
        'parts':records,'units':'mm','sliced':False,'objects':len(items),'layout_bed_mm':[325,320,325],
        'plate_bounds_mm':{key:mesh.bounds.tolist() for key,mesh in placed},'knee_stator_countersinks':0 if integrated else len(cones)},indent=2))
    readme='''# RS02 motor fit plate

Open `00-RS02-motor-fit.3mf` in Bambu Studio using the actual H2D single-nozzle,
filament and nozzle profile. This file is unsliced; review orientation, supports
and layers before printing.

The two short case-clearance gauges retain their recorded generated source.
The three reusable motor interfaces derive from the current canonical native
Fusion parts. Their source versions, export hashes and print provenance are
recorded in the manifests. These gauges do not qualify loaded operation.

Use the revised countersunk knee-stator interface and the specified common
M3 flat-head screws. The earlier socket-head stator plate is a historical fit
reference and must not be reused for the actuated limb. The hip flange and hub
can be reused if their actual fit and source geometry match the current parts.

Let every print cool, then check motor seating and mounting-hole alignment.
Keep motors disconnected and supported; do not use screw tension to pull a
misaligned interface into place. The complete motor-complex package contains
the current hardware table and assembly instructions.
'''
    if integrated:
        readme='''# RS02 integrated motor fit plate

Open `00-RS02-motor-fit.3mf` in Bambu Studio using the actual H2D single-nozzle,
filament and nozzle profile. The plate contains the native primary structural
motor cradle and two unchanged generated case gauges. It is unsliced. Review
supports, especially beneath the cradle's offset motor face and knee region.

The primary cradle is a reusable part of the integrated thigh. It tests the hip
output flange, knee motor insertion and short socket-head stator seats. The
two rings test only nominal case clearance: 80.5 mm for the thigh and 81.5 mm
for the hip cup. They do not test connectors, bearings or complete assembly.
Separate hip hubs and stator plates belong to an earlier design.

Source versions and hashes are recorded in the manifests. Let prints cool
before checking fit. Keep motors disconnected and supported; do not pull a
misaligned interface together with screw tension. Use the full motor-complex
package's hardware list and assembly guide. These parts qualify only supported,
unpowered fit checks, not printed strength or loaded operation.
'''
    if args.safe_only:
        readme='''# RS02 case and output-hub fit plate

Print the two case-clearance gauges and the native hip output hub in
`00-RS02-motor-fit.3mf`. The gauges retain their recorded generated source;
the reusable hub derives from the canonical native Fusion part. The manifest
records exact source hashes. Motor stator plates and the motor cup are being
revised for confirmed fastener contacts and are deliberately omitted here.

Use the actual H2D single-nozzle, filament and nozzle profile in Bambu Studio.
This plate is unsliced. Inspect orientation, supports and layers, then let
prints cool before checking motor seating and output-hole alignment. Keep
the motor disconnected and supported. Do not pull a misaligned fit together
with screw tension. These checks do not qualify loaded or powered operation.
'''
    if args.gauges_only:
        readme='''# RS02 auxiliary case gauges

The plate contains only two generated diagnostic gauges: 80.5 mm for the thigh
case opening and 81.5 mm for the hip cup. Their immutable source hashes are
recorded in the manifest. Robot components are omitted while their native
fastener and case-clearance revisions complete independent assembly checks.

Open `00-RS02-motor-fit.3mf` in Bambu Studio using the actual H2D single-nozzle,
filament and nozzle profile. This file is unsliced; inspect the layers and let
prints cool before checking motor-case fit. These short rings do not test
mounting holes, connectors, bearings or the complete motor assembly.
'''
    (target/'README.md').write_text(readme)
    hashes={str(p.relative_to(target)):sha(p) for p in sorted(target.rglob('*')) if p.is_file()}
    (target/'SHA256SUMS').write_text(''.join(f'{value}  {name}\n' for name,value in hashes.items()))
    archive=target.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(target.rglob('*')):
            if path.is_file():z.write(path,path.relative_to(target.parent))
    print(json.dumps({'directory':str(target),'archive':str(archive),'archive_sha256':sha(archive)},indent=2))


if __name__=='__main__':main()
