"""Separate authoring tabs from loaded reference contexts before any cleanup."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''\nimport adsk.core as core,adsk.fusion as fusion,json

def run(_context:str):
 app=core.Application.get();rows=[]
 for doc in app.documents:
  if not doc.dataFile:continue
  row={'name':doc.name,'file_id':doc.dataFile.id,'version':doc.dataFile.versionNumber,'modified':doc.isModified,'read_only':doc.dataFile.isReadOnly,'protected_subsystem':doc.dataFile.id in FILE_IDS.values()}
  try:refs=doc.allDocumentReferences
  except RuntimeError as error:
   if 'non-top-level document'not in str(error):raise
   row.update(context='loaded_reference',eligible_to_close=False)
  else:
   row.update(context='authoring_document',references=[{'name':x.dataFile.name,'version':x.version,'file_id':x.dataFile.id}for x in refs],eligible_to_close=not row['protected_subsystem']and not doc.isModified and doc.name.startswith('V0 - ')and doc.dataFile.isComplete)
  rows.append(row)
 print(json.dumps({'documents':rows,'editable_files':len(app.data.personalUseLimits.editableFiles),'scope':'Read-only classification. Loaded reference contexts must not be mistaken for disposable unsaved authoring tabs.'}))
'''
r=rpc(s,'loaded-document-contexts',timeout=60,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/loaded-document-contexts.json').write_text(json.dumps(record,indent=2));print(record)
