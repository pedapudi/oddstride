"""Read actual Fusion state, export built parts and checkpoint the native master."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
SCRIPT='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
    app=core.Application.get();doc=next((d for d in app.documents if d.name.startswith('Tinfox - Native Master Assembly')),None)
    assert doc is not None,'Native V0 document is not open'
    doc.activate();d=fusion.Design.cast(app.activeProduct);d.attributes.add('Tinfox','Revision','V0')
    path=os.path.join(tempfile.gettempdir(),'tinfox-native');os.makedirs(path,exist_ok=True)
    parts=[];ex=d.exportManager
    for group in d.rootComponent.occurrences:
        for occurrence in group.component.occurrences:
            c=occurrence.component
            if not c.partNumber or c.bRepBodies.count<1:continue
            key=c.partNumber;step=os.path.join(path,key+'.step');stl=os.path.join(path,key+'.stl')
            if not os.path.exists(step):assert ex.execute(ex.createSTEPExportOptions(step,c))
            if not os.path.exists(stl):
                options=ex.createSTLExportOptions(c,stl);options.unitType=fusion.DistanceUnits.MillimeterDistanceUnits;options.meshRefinement=fusion.MeshRefinementSettings.MeshRefinementHigh;assert ex.execute(options)
            parts.append({'id':key,'name':c.name,'group':group.component.name,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'volume_mm3':sum(b.physicalProperties.volume for b in c.bRepBodies)*1000,'paths':[step,stl]})
    archive=os.path.join(path,'Tinfox-Native-Master.f3d');assert ex.execute(ex.createFusionArchiveExportOptions(archive))
    if doc.isModified:doc.save('V0 native feature conversion checkpoint; migration gates remain open.')
    print(json.dumps({'document':doc.name,'file_id':doc.dataFile.id,'parts':parts,'native_archive':archive,'timeline_items':d.timeline.count,'parameters':d.userParameters.count}))
'''
def reconcile():
 result=rpc(SCRIPT,'native-state',timeout=120)
 if not result[0].get('success',True):raise RuntimeError(result)
 state=json.loads(result[0]['message']);(ROOT/'manifests/native-state.json').write_text(json.dumps(state,indent=2))
 for p in state['parts']:
  for path in p['paths']:
   if not (ROOT/'exports'/Path(path).name).exists():fetch(path,Path(path).name)
 fetch(state['native_archive'],'Tinfox-Native-Master.f3d')
 import hashlib
 (ROOT/'manifests/archive.json').write_text(json.dumps({'kind':'native feature checkpoint','parts':[p['id'] for p in state['parts']],'timeline_items':state['timeline_items'],'archive_sha256':hashlib.sha256((ROOT/'exports/Tinfox-Native-Master.f3d').read_bytes()).hexdigest(),'migration_gate_passed':False},indent=2))
 manifest=json.loads((ROOT/'manifests/parts.json').read_text());lookup={p['id']:p for p in state['parts']}
 for p in manifest['parts']:
  if p['id'] in lookup:
   item=lookup[p['id']];p.update(native_feature_count=item['features'],native_sketch_count=item['sketches'],native_component=item['name'],state='native_built_pending_audit')
   audit=ROOT/'audits'/f'{p["id"]}-geometry.json'
   if audit.exists():
    evidence=json.loads(audit.read_text());p['audits']['geometry']='audits/'+audit.name
    p['state']='geometry_audited_editability_pending' if evidence['geometric_gate_passed'] else 'geometry_audit_failed'
   sections=ROOT/'audits'/f'{p["id"]}-sections.json'
   if sections.exists():
    evidence=json.loads(sections.read_text());p['audits']['sections']='audits/'+sections.name
    if not evidence['section_gate_passed']:p['state']='section_audit_failed'
 manifest['design_revision']='V0';manifest['fusion_document']['id']=state['file_id'];(ROOT/'manifests/parts.json').write_text(json.dumps(manifest,indent=2))
 return state
if __name__=='__main__':reconcile()
