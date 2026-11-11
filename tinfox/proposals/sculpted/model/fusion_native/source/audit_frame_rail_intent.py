"""Compare native motor rail boundaries and sections to the frozen frame."""
import json,sys
from pathlib import Path
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1];targets={p['key']:p for p in json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low']['custom_parts']};side=sys.argv[1] if len(sys.argv)>1 else 'right';label=sys.argv[2] if len(sys.argv)>2 else 'frame-intent-'+side+'-rail';key='chassis_beam_'+('102' if side=='right' else '-102');reference={'id':key,'source_step':targets[key]['files']['step']['path'],'source_reference_note':'Frozen low robot motor rail. Compact native history and shared frame/deck datums; independent hardware fits.'};audit(key,label,reference);sections(key,label,reference)
