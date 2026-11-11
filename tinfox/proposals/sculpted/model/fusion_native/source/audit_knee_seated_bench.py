"""Reuse the static native interface checker with the explicit knee-seat revision."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'source/audit_motor_complex_native_interfaces.py').read_text()
source=source.replace('from motor_complex_exports import COMPONENTS','from motor_complex_exports import COMPONENTS as BASE_COMPONENTS\nCOMPONENTS=dict(BASE_COMPONENTS); COMPONENTS["motor_mount_ring"]=("CANDIDATE_ks_motor_mount_ring","knee-seated-native-motor_mount_ring")')
needle="hardware=json.loads((ROOT/'manifests/motor-complex-hardware.json').read_text())"
source=source.replace(needle,needle+"\nupdated={r['name']:r for r in json.loads((ROOT/'audits/knee-stator-seated-references.json').read_text())['references']}\nfor row in hardware['parts']:\n if row['name']in updated:row['bounds_mm']=updated[row['name']]['bounds_mm']")
source=source.replace("for angle in [90,210,330]:", "for angle in range(20,380,40):pairs.append(['motor_mount_ring','Knee stator M3x8 '+str(angle)])\nfor angle in [90,210,330]:")
source=source.replace('motor-complex-native-critical-interfaces','motor-complex-seated-native-critical-interfaces')
exec(compile(source,str(ROOT/'source/audit_motor_complex_native_interfaces.py'),'exec'),{'__file__':str(ROOT/'source/audit_motor_complex_native_interfaces.py'),'__name__':'__main__'})
