"""Reuse successful unchanged exact-geometry audits by source and export hashes."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def qualified_pair(label,reference):
 source=ROOT/reference['source_step'];native=ROOT/'exports'/f'{label}.step'
 if not source.exists() or not native.exists():return False
 expected={'source_step_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'native_step_sha256':hashlib.sha256(native.read_bytes()).hexdigest()}
 for suffix,gate in [('geometry','geometric_gate_passed'),('sections','section_gate_passed')]:
  path=ROOT/'audits'/f'{label}-{suffix}.json'
  if not path.exists():return False
  report=json.loads(path.read_text())
  if not report.get(gate) or any(report.get(key)!=value for key,value in expected.items()):return False
 return True
