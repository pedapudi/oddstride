"""Reopen the saved whole-leg checkpoint and verify histories, geometry and placements."""
import json
from pathlib import Path
from run_native import rpc

ROOT=Path(__file__).resolve().parents[1]
pose=json.loads((ROOT/'audits/current-native-pose-edit-restore.json').read_text());assert pose['passed']
installed=json.loads((ROOT/'audits/current-native-installed-all.json').read_text());assert installed['passed']
script=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();assert doc.dataFile.isComplete and not doc.isModified;file=doc.dataFile;version=file.versionNumber;tick=time.monotonic()
 def capture(document):
  d=fusion.Design.cast(document.products.itemByProductType('DesignProductType'));root=d.rootComponent;placements={};definitions={};visible=[o.component.partNumber for o in root.occurrences if o.isLightBulbOn];assert all(o.component.joints.count==0 for o in root.occurrences if o.component.partNumber in ['ASSEMBLY_FL','ASSEMBLY_FR','ASSEMBLY_RL','ASSEMBLY_RR'])
  def walk(occ):
   if not occ.isLightBulbOn:return
   c=occ.component
   if c.bRepBodies.count:
    placements[occ.fullPathName]=list(occ.transform2.asArray())
    if c.partNumber not in definitions:
     definitions[c.partNumber]={'features':c.features.count,'sketches':c.sketches.count,'bodies':[]}
     assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),c.partNumber
     for b in c.bRepBodies:
      bb=b.boundingBox;definitions[c.partNumber]['bodies'].append({'faces':b.faces.count,'edges':b.edges.count,'vertices':[list(v.geometry.asArray())for v in b.vertices],'bounds_cm':[*bb.minPoint.asArray(),*bb.maxPoint.asArray()]})
   for child in c.occurrences:walk(child.createForAssemblyContext(occ))
  for o in root.occurrences:walk(o)
  assert len(placements)==592 and len(visible)==4;assert all(p.startswith('CURRENT_ASSEMBLY_')for p in visible)
  return {'placements':placements,'definitions':definitions,'parameters':{p.name:p.expression for p in d.userParameters},'visible':visible,'timeline_count':d.timeline.count}
 before=capture(doc);d=fusion.Design.cast(doc.products.itemByProductType('DesignProductType'));p=d.userParameters.itemByName('pose_FL_hip');original=p.expression
 try:
  p.expression='35 deg';assert d.computeAll();moving=capture(doc);assert moving['visible']==before['visible']and set(moving['placements'])==set(before['placements'])
 finally:p.expression=original;assert d.computeAll()
 restored=capture(doc);assert restored['parameters']==before['parameters'];assert restored['visible']==before['visible'];assert set(restored['placements'])==set(before['placements']);assert max(abs(a-b)for key,row in before['placements'].items()for a,b in zip(row,restored['placements'][key]))<1e-8
 # Only this controlled, restored pose experiment has modified the previously
 # verified saved document. Reopening discards its redundant dirty flag.
 assert doc.close(False);doc=app.documents.open(file,True);assert doc and doc.dataFile.versionNumber==version and doc.dataFile.isComplete and not doc.isModified;after=capture(doc);assert before['parameters']==after['parameters'] and before['visible']==after['visible'] and before['timeline_count']==after['timeline_count'];assert set(before['placements'])==set(after['placements']);matrix_error=max(abs(a-b)for key,row in before['placements'].items()for a,b in zip(row,after['placements'][key]));assert matrix_error<1e-8;checks=[]
 for key,first in before['definitions'].items():
  last=after['definitions'][key];assert first['features']==last['features'] and first['sketches']==last['sketches'] and len(first['bodies'])==len(last['bodies']);errors=[]
  for a,b in zip(first['bodies'],last['bodies']):
   assert a['faces']==b['faces'] and a['edges']==b['edges'] and len(a['vertices'])==len(b['vertices']);assert max(abs(x-y)for x,y in zip(a['bounds_cm'],b['bounds_cm']))<1e-6;error=max((min(sum((x-y)**2 for x,y in zip(v,w))for w in b['vertices'])for v in a['vertices']),default=0)**.5*10;assert error<.00001,(key,error);errors.append(error)
  checks.append({'part_number':key,'features':last['features'],'sketches':last['sketches'],'bodies':len(last['bodies']),'maximum_vertex_error_mm':max(errors,default=0)})
 print(json.dumps({'passed':True,'saved_version':version,'reopened':True,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'visible':after['visible'],'placed_items':len(after['placements']),'visibility_survives_pose_edit_and_restore':True,'controlled_test_edits_discarded_after_verified_restore':True,'maximum_matrix_error_cm':matrix_error,'definition_checks':checks,'parameters':after['parameters'],'timeline_count':after['timeline_count'],'editable_files':len(app.data.personalUseLimits.editableFiles),'elapsed_seconds':time.monotonic()-tick,'scope':'Saved/reopened current four-leg assembly; history, parameters, actual placements and boundary fingerprints preserved. Physical strength and collision-free use remain separate.'}))
'''
reply=rpc(script,'current-native-leg-saved-reopen',timeout=1200)
assert reply[0]['success'],reply
record=json.loads(reply[0]['message']);(ROOT/'audits/current-native-leg-saved-reopen.json').write_text(json.dumps(record,indent=2))
print({k:v for k,v in record.items()if k not in ['definition_checks','parameters']})
