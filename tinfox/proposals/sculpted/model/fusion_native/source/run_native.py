"""Send a native-feature script to Fusion and persist the complete response."""
import json,sys,urllib.request,datetime,zlib,base64,time,os,hashlib,gzip
from pathlib import Path
NATIVE=Path(__file__).resolve().parents[1]
def rpc(script,tag,timeout=900,*,read_only=False):
 publication_state=NATIVE/'manifests/publication-state.json'
 if not read_only and publication_state.exists():
  unresolved=json.loads(publication_state.read_text())
  if unresolved.get('state')=='execution_state_unknown':
   raise RuntimeError('A prior Fusion mutation has unknown status. Inspect and reconcile its actual document/file state before any further writes. See manifests/publication-state.json.')
 original_script_sha=hashlib.sha256(script.encode()).hexdigest()
 source_archive=None
 if not read_only:
  archive_dir=NATIVE/'snapshots/executed-scripts';archive_dir.mkdir(exist_ok=True);source_archive=archive_dir/(original_script_sha+'.py.gz')
  if not source_archive.exists():source_archive.write_bytes(gzip.compress(script.encode(),mtime=0))
 compressed=zlib.compress(script.encode(),9)
 if len(compressed)>180000:
  # Large native sketch recipes exceed the MCP HTTP request limit. Stage only
  # our generated Python source in bounded, verified chunks; authoring still
  # executes native Fusion operations and never imports a neutral solid.
  assert not read_only,'Read-only scripts must not stage files'
  archive_sha=hashlib.sha256(compressed).hexdigest()
  for index,offset in enumerate(range(0,len(compressed),100000)):
   chunk=base64.b64encode(compressed[offset:offset+100000]).decode()
   stage='import os,tempfile,base64,json\ndef run(_context: str):\n path=os.path.join(tempfile.gettempdir(),"tinfox-native","script-'+archive_sha+'.zlib")\n os.makedirs(os.path.dirname(path),exist_ok=True)\n assert '+str(offset)+'==0 or os.path.getsize(path)=='+str(offset)+'\n with open(path,"'+('wb' if offset==0 else 'ab')+'") as file:file.write(base64.b64decode('+repr(chunk)+'))\n print(json.dumps({"offset":'+str(offset)+',"size":os.path.getsize(path)}))\n'
   response=rpc(stage,tag+'-source-chunk-'+str(index),timeout=30)
   assert response and response[0].get('success'),response
  script='import os,tempfile,zlib,hashlib\ndef run(_context: str):\n path=os.path.join(tempfile.gettempdir(),"tinfox-native","script-'+archive_sha+'.zlib")\n data=open(path,"rb").read();assert hashlib.sha256(data).hexdigest()=='+repr(archive_sha)+'\n source=zlib.decompress(data);assert hashlib.sha256(source).hexdigest()=='+repr(original_script_sha)+'\n ns={};exec(compile(source,"tinfox_native.py","exec"),ns);ns["run"](_context)\n'
 started=time.monotonic();state={'tag':tag,'pid':os.getpid(),'started_utc':datetime.datetime.now(datetime.UTC).isoformat(),'state':'executing','read_only':read_only,'script_sha256':original_script_sha,'script_archive':str(source_archive.relative_to(NATIVE)) if source_archive else None}
 state_path=NATIVE/'manifests/current-rpc.json';state_path.write_text(json.dumps(state,indent=2))
 connection=json.load(open('/tmp/fusion-mcp-connection.json'))
 # Keep transport lines short and preserve exact source bytes.
 # Retain the current output guard while unwrapping stale guards from prior calls.
 encoded=base64.b64encode(zlib.compress(script.encode(),9)).decode()
 chunks='\n'.join('        '+repr(encoded[i:i+500]) for i in range(0,len(encoded),500))
 script='import base64,zlib,sys\ndef run(_context: str):\n    writer=sys.stdout\n    if type(writer).__name__=="_NsSanitizedWriter":\n        original=writer._original\n        while type(original).__name__=="_NsSanitizedWriter":original=original._original\n        writer._original=original\n    encoded=(\n'+chunks+'\n    )\n    ns={}\n    exec(compile(zlib.decompress(base64.b64decode(encoded)),"tinfox_native.py","exec"),ns)\n    ns["run"](_context)\n'
 body={'jsonrpc':'2.0','id':100,'method':'tools/call','params':{'name':'fusion_mcp_execute','arguments':{'featureType':'script','object':{'script':script}}}}
 try:
  with urllib.request.urlopen(urllib.request.Request(connection['url'],data=json.dumps(body).encode(),headers=connection['headers']),timeout=timeout) as response:
   if 'event-stream' in response.headers.get('Content-Type',''):
    result=None
    for line in response:
     s=line.decode().strip()
     if s.startswith('data:'):result=json.loads(s[5:]);break
   else:result=json.loads(response.read())
 except Exception as error:
  state.update(state='execution_state_unknown',elapsed_seconds=time.monotonic()-started,error=str(error));state_path.write_text(json.dumps(state,indent=2))
  if not read_only:publication_state.write_text(json.dumps(state,indent=2))
  raise
 (NATIVE/'audits'/f'{tag}-rpc.json').write_text(json.dumps(result,indent=2))
 messages=[]
 for c in result.get('result',{}).get('content',[]):
  if c.get('type')=='text':
   try:messages.append(json.loads(c['text']))
   except json.JSONDecodeError:messages.append(c['text'])
 state.update(state='complete',elapsed_seconds=time.monotonic()-started,success=all(not isinstance(m,dict) or m.get('success',True) for m in messages));state_path.write_text(json.dumps(state,indent=2))
 (NATIVE/'audits'/f'{tag}-timing.json').write_text(json.dumps(state,indent=2))
 print(json.dumps({'tag':tag,'success':state['success'],'elapsed_seconds':round(state['elapsed_seconds'],2),'response_file':'audits/'+tag+'-rpc.json'}),flush=True)
 return messages
if __name__=='__main__':rpc(Path(sys.argv[1]).read_text(),sys.argv[2] if len(sys.argv)>2 else 'last')
