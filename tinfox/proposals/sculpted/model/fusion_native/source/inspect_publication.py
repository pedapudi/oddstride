"""Read the master after a publication timeout without changing any document."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
script='''import adsk.core as core,adsk.fusion as fusion,json

def run(_context: str):
 app=core.Application.get();master=next(d for d in app.documents if d.name.startswith('Tinfox - Native Master Assembly'))
 # Inspect its design through products; preserve the active document.
 design=next(fusion.Design.cast(p) for p in master.products if fusion.Design.cast(p))
 parts=[]
 for group in design.rootComponent.occurrences:
  for occurrence in group.component.occurrences:
   c=occurrence.component
   if c.partNumber not in ['thigh_outer','thigh_outer_right','shin_outer','body_center_0']:continue
   file=occurrence.documentReference.dataFile if occurrence.isReferencedComponent else None
   parts.append({'part':c.partNumber,'component':c.name,'path':occurrence.fullPathName,'features':c.features.count,'sketches':c.sketches.count,'volume_mm3':sum(b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume for b in c.bRepBodies)*1000,'file_id':file.id if file else None,'file_name':file.name if file else None,'version':file.versionNumber if file else None})
 print(json.dumps({'active_document':app.activeDocument.name,'documents':[d.name for d in app.documents],'parts':parts,'read_only':True}))
'''
response=rpc(script,'inspect-publication',timeout=60,read_only=True);assert response[0].get('success'),response
result=json.loads(response[0]['message']);(ROOT/'audits/publication-reconciliation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
