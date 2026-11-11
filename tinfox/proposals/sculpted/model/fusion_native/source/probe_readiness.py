"""Bounded, read-only Fusion probes while a prior mutation has unknown status."""
import json,time,urllib.request,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for attempt in range(10):
 connection=json.load(open('/tmp/fusion-mcp-connection.json'))
 script='import adsk.core,json\ndef run(_context: str):\n app=adsk.core.Application.get()\n print(json.dumps({"active_document":app.activeDocument.name,"active_command":app.userInterface.activeCommand,"documents":[d.name for d in app.documents]}))\n'
 body={'jsonrpc':'2.0','id':1100+attempt,'method':'tools/call','params':{'name':'fusion_mcp_execute','arguments':{'featureType':'script','object':{'script':script}}}}
 row={'attempt':attempt,'utc':datetime.datetime.now(datetime.UTC).isoformat(),'read_only':True}
 try:
  with urllib.request.urlopen(urllib.request.Request(connection['url'],data=json.dumps(body).encode(),headers=connection['headers']),timeout=8) as response:row.update(responsive=True,response=response.read().decode())
 except Exception as error:row.update(responsive=False,error=str(error))
 with (ROOT/'audits/readiness-probes.jsonl').open('a') as handle:handle.write(json.dumps(row)+'\n')
 print(json.dumps(row),flush=True)
 if row['responsive']:break
 if attempt<9:time.sleep(60)
