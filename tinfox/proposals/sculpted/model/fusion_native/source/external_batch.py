"""Build a bounded list of native part documents; audit each exported shape once."""
import sys,subprocess,json
from pathlib import Path
from external_build import build
ROOT=Path(__file__).resolve().parents[1];PYTHON=ROOT.parents[3]/'.venv/bin/python'
for key in sys.argv[1:]:
 print('Native part',key,flush=True)
 if build(key):
  for script in ['audit_part.py','audit_sections.py']:
   result=subprocess.run([str(PYTHON),str(ROOT/'source'/script),key],text=True,capture_output=True)
   print(result.stdout or result.stderr,flush=True)
 else:print('Native feature failure; inspect saved RPC evidence:',key,flush=True)
