"""Compare current native carrier solids against the frozen machined interfaces."""
from pathlib import Path
from audit_cache import qualified_pair
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1]
for front in [1,-1]:
 for suffix in ['', '_right']:
  key='motor_carrier_'+str(front)+suffix;label='cohesive-motor-carrier-'+str(front)+suffix.replace('_','-')
  if not (ROOT/'exports'/f'{label}.step').exists():continue
  ref={'id':key,'source_step':f'snapshots/cohesive-limb/step/{key}.step'}
  if qualified_pair(label,ref):print(label,'unchanged audit reused');continue
  audit(key,label,ref);sections(key,label,ref)
