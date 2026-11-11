"""Compare each native mount candidate to the frozen current motor interfaces."""
import json,sys
from pathlib import Path
from audit_part import audit
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1];target=json.loads((ROOT/'manifests/latest-mount-target.json').read_text())
for key,row in target['parts'].items():
 label='slim-native-'+key
 if not (ROOT/'exports'/f'{label}.step').exists():continue
 if len(sys.argv)>1 and sys.argv[1] not in key:continue
 ref={'id':key,'source_step':str(ROOT/row['path']),'source_reference_note':'Current slimmer mount target '+target['source_model_sha256']+'; no bearing-family substitution.'};audit(key,label,ref);sections(key,label,ref)
