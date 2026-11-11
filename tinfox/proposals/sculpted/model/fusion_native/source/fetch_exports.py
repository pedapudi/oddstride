"""Retrieve generated native archives and audit exports in bounded MCP chunks."""
import json,base64,zlib,hashlib,urllib.request,sys,subprocess,shlex,tempfile,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(script,parsed=True):
 connection=json.load(open('/tmp/fusion-mcp-connection.json'))
 script=script.replace('def run(_context: str):', 'def run(_context: str):\n    import sys\n    writer=sys.stdout\n    if type(writer).__name__=="_NsSanitizedWriter":\n        original=writer._original\n        while type(original).__name__=="_NsSanitizedWriter":original=original._original\n        writer._original=original')
 body={'jsonrpc':'2.0','id':101,'method':'tools/call','params':{'name':'fusion_mcp_execute','arguments':{'featureType':'script','object':{'script':script}}}}
 with urllib.request.urlopen(urllib.request.Request(connection['url'],data=json.dumps(body).encode(),headers=connection['headers']),timeout=60) as r:
  raw=r.read().decode()
  if raw.startswith('event:') or raw.startswith('data:'):raw=next(x[5:].strip() for x in raw.splitlines() if x.startswith('data:'))
  outer=json.loads(raw);inner=json.loads(outer['result']['content'][0]['text'])
  if not inner.get('success'):raise RuntimeError(inner)
  return json.loads(inner['message']) if parsed else inner['message']
def fetch_ssh(remote,name):
 """Read the completed export without using Fusion's UI thread for chunks."""
 destination=(ROOT/'exports'/name).resolve();assert destination.is_relative_to((ROOT/'exports').resolve()) and not Path(name).is_absolute();destination.parent.mkdir(parents=True,exist_ok=True)
 command=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','sunil@sunils-mac-mini.lan']
 meta=subprocess.run(command+['/usr/bin/shasum -a 256 '+shlex.quote(remote)],capture_output=True,timeout=30)
 if meta.returncode:return False
 digest=meta.stdout.decode().split()[0];assert len(digest)==64
 result=subprocess.run(command+['/bin/cat '+shlex.quote(remote)],capture_output=True,timeout=90)
 if result.returncode:return False
 data=result.stdout;assert hashlib.sha256(data).hexdigest()==digest,'Export transfer hash mismatch'
 destination=ROOT/'exports'/name
 with tempfile.NamedTemporaryFile(dir=destination.parent,delete=False)as f:f.write(data);temporary=f.name
 os.replace(temporary,destination);print(name,len(data),'bytes, SSH SHA verified');return True

def fetch(remote,name):
 if fetch_ssh(remote,name):return
 prep='import json,zlib,hashlib\ndef run(_context: str):\n    data=open('+repr(remote)+',"rb").read()\n    packed=zlib.compress(data,6)\n    open('+repr(remote+'.zlib')+',"wb").write(packed)\n    print(json.dumps({"size":len(data),"packed":len(packed),"sha256":hashlib.sha256(data).hexdigest()}))\n'
 meta=read(prep);chunks=[]
 for offset in range(0,meta['packed'],196608):
  script='import base64\ndef run(_context: str):\n    f=open('+repr(remote+'.zlib')+',"rb");f.seek('+str(offset)+')\n    data=f.read(196608)\n    for i in range(0,len(data),512):print(base64.b64encode(data[i:i+512]).decode())\n'
  chunks.append(b''.join(base64.b64decode(line) for line in read(script,False).splitlines() if line))
 data=zlib.decompress(b''.join(chunks));assert len(data)==meta['size'] and hashlib.sha256(data).hexdigest()==meta['sha256']
 (ROOT/'exports'/name).write_bytes(data);print(name,len(data),'bytes, SHA verified')
if __name__=='__main__':
 r=json.load(open(ROOT/'audits/motor-mount-ring-export-rpc.json'));m=json.loads(json.loads(r['result']['content'][0]['text'])['message'])
 for p in m['paths']:fetch(p,Path(p).name)
