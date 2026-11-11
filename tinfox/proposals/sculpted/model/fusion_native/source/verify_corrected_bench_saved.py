"""Reopen the corrected saved scope without replacing historical checkpoint evidence."""
import json
from pathlib import Path
from run_native import rpc
from motor_complex_corrected_exports import COMPONENTS
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'source/verify_motor_complex_saved.py').read_text();start=source.index("s=(ROOT/");end=source.index("\ntag=",start)
namespace={'ROOT':ROOT,'COMPONENTS':COMPONENTS,'reopen':True};exec(source[start:end],namespace)
s=namespace['s'];r=rpc(s,'corrected-bench-saved-reopen',timeout=900);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/corrected-bench-saved-reopen.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k!='snapshot'})
