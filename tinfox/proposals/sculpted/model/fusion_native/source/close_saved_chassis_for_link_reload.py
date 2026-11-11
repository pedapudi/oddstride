"""Close only the verified saved source tab outside an MCP command transaction."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,sys,types,threading,json,time,traceback

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');assert doc.dataFile.versionNumber==11 and doc.dataFile.isComplete and not doc.isModified;assert doc!=app.activeDocument;key='tinfox_chassis_reload_event';assert key not in sys.modules;state=types.ModuleType(key);state.document=doc;state.result={'state':'scheduled','file_id':doc.dataFile.id,'version':doc.dataFile.versionNumber};state.attempts=0;state.event_id='tinfox.close.saved.chassis.source';state.event=app.registerCustomEvent(state.event_id);sys.modules[key]=state
 class Handler(core.CustomEventHandler):
  def __init__(self):super().__init__()
  def notify(self,args):
   try:
    command=app.userInterface.activeCommand;state.attempts+=1
    if command not in ['SelectCommand','FusionSelectCommand','']:
     if state.attempts<4:state.timer=threading.Timer(1,lambda:app.fireCustomEvent(state.event_id));state.timer.start();return
     state.result={'state':'not_closed','reason':'Active command still running','command':command};return
    target=state.document;assert target.isValid and target.dataFile.versionNumber==11 and target.dataFile.isComplete and not target.isModified;accepted=target.close(False);state.result={'state':'close_returned','accepted':accepted,'command':command,'file_id':'urn:adsk.wipprod:dm.lineage:R7U8KNNBSA6o3YwVNF2ZQQ','version':11,'verification_required':True}
   except Exception:state.result={'state':'error','traceback':traceback.format_exc()}
 state.handler=Handler();state.event.add(state.handler);state.timer=threading.Timer(1,lambda:app.fireCustomEvent(state.event_id));state.timer.start();print(json.dumps(state.result))
'''
r=rpc(s,'schedule-saved-chassis-close',timeout=30);assert r[0]['success'],r;print(r)
