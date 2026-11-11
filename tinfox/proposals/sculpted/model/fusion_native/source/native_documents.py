"""Select authoring documents without confusing linked reference contexts."""
FILE_IDS={'master':'urn:adsk.wipprod:dm.lineage:7_ejr6qRQtezEex5HEj7xw','chassis':'urn:adsk.wipprod:dm.lineage:R7U8KNNBSA6o3YwVNF2ZQQ','leg':'urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ','head':'urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA'}
def authoring_document(app,role):
 candidates=[]
 for document in app.documents:
  if not document.dataFile or document.dataFile.id!=FILE_IDS[role]:continue
  # A derive link can reference the top-level authoring document itself.
  # Excluding every referenced document would incorrectly exclude that file.
  try:document.allDocumentReferences
  except RuntimeError as error:
   if 'non-top-level document' not in str(error):raise
   continue
  candidates.append(document)
 assert len(candidates)==1,(role,[(d.name,d.isModified) for d in candidates])
 return candidates[0]
