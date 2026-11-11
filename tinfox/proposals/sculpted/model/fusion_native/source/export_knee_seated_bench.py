"""Run the shared direct exporter with revision paths, preserving Leg20 artifacts."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'source/export_motor_complex_native.py').read_text()
source=source.replace('from motor_complex_exports import COMPONENTS','from motor_complex_exports import COMPONENTS as BASE_COMPONENTS\nCOMPONENTS=dict(BASE_COMPONENTS); COMPONENTS["motor_mount_ring"]=("CANDIDATE_ks_motor_mount_ring","knee-seated-native-motor_mount_ring")')
source=source.replace('motor-complex-native','motor-complex-seated-native')
exec(compile(source,str(ROOT/'source/export_motor_complex_native.py'),'exec'),{'__file__':str(ROOT/'source/export_motor_complex_native.py'),'__name__':'__main__'})
