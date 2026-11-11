"""Audit each native linkage and sleeve against its frozen assembly geometry."""
import shutil
from audit_cache import qualified_pair
from pathlib import Path
import cadquery as cq
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1];frozen=ROOT/'snapshots/cohesive-limb/step'
for key in ['pushrod','sleeve_0','sleeve_1','knee_axle']:
 dest=frozen/f'{key}.step'
 if not dest.exists():
  src=ROOT/'snapshots/cohesive-limb/hardware'/f'{key}.step'
  if not src.exists():src=ROOT/'snapshots/step'/f'{key}.step'
  shutil.copyfile(src,dest)
 right=frozen/f'{key}_right.step'
 if not right.exists():cq.exporters.export(cq.importers.importStep(str(dest)).val().mirror('XZ'),str(right))
 for suffix in ['', '_right']:
  k=key+suffix;label='cohesive-'+k.replace('_','-');ref={'id':k,'source_step':f'snapshots/cohesive-limb/step/{k}.step'}
  if qualified_pair(label,ref):print(label,'unchanged audit reused');continue
  audit(k,label,ref);sections(k,label,ref)
