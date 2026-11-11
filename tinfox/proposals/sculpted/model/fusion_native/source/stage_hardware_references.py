"""Transfer hash-verified vendor/reference STEP files; never custom geometry."""
import base64,json,zlib
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'manifests/current-exact-hardware-references.json').read_text());assert r['missing_count']==0
payload=[{'name':Path(g['path']).name,'sha256':g['sha256'],'data':base64.b64encode(zlib.compress((ROOT/g['path']).read_bytes(),9)).decode()} for g in r['groups']]
s='''import os,tempfile,zlib,base64,hashlib,json

def run(_context: str):
 folder=os.path.join(tempfile.gettempdir(),'tinfox-native','reference-hardware');os.makedirs(folder,exist_ok=True);rows=[]
 for item in PAYLOAD:
  data=zlib.decompress(base64.b64decode(item['data']));assert hashlib.sha256(data).hexdigest()==item['sha256'];path=os.path.join(folder,item['name'])
  with open(path,'wb') as file:file.write(data)
  assert hashlib.sha256(open(path,'rb').read()).hexdigest()==item['sha256'];rows.append({'name':item['name'],'path':path,'sha256':item['sha256'],'bytes':len(data)})
 print(json.dumps({'files':rows,'role':'Standard hardware and vendor envelope references only; custom parts excluded.'}))
'''.replace('PAYLOAD',repr(payload))
a=rpc(s,'stage-reference-hardware',timeout=60);assert a[0]['success'],a;record=json.loads(a[0]['message']);(ROOT/'audits/staged-reference-hardware.json').write_text(json.dumps(record,indent=2));print({'files':len(record['files'])})
