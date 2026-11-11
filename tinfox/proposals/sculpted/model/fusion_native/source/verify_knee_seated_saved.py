"""Verify the same saved document with the revised plate; retain Leg20 evidence."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'source/verify_motor_complex_saved.py').read_text()
source=source.replace('from motor_complex_exports import COMPONENTS','from motor_complex_exports import COMPONENTS as BASE_COMPONENTS\nCOMPONENTS=dict(BASE_COMPONENTS); COMPONENTS["motor_mount_ring"]=("CANDIDATE_ks_motor_mount_ring","knee-seated-native-motor_mount_ring")')
source=source.replace('motor-complex-saved-','motor-complex-seated-saved-')
exec(compile(source,str(ROOT/'source/verify_motor_complex_saved.py'),'exec'),{'__file__':str(ROOT/'source/verify_motor_complex_saved.py'),'__name__':'__main__'})
