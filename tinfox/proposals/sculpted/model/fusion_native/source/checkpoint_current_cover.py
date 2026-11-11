"""Checkpoint the audited cover candidate without promoting robot authority."""
import json,hashlib
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
for filename,gate in [('current-body-cover-native-geometry.json','geometric_gate_passed'),('current-body-cover-native-sections.json','section_gate_passed'),('current-body-cover-silhouettes.json','passed'),('current-cover-family-qualification.json','passed')]:assert json.loads((ROOT/'audits'/filename).read_text())[gate],filename
s=script_header()+'''
import adsk.core as core,adsk.fusion as fusion

def run(_context: str):
 import json,time,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:R7U8KNNBSA6o3YwVNF2ZQQ';d=fusion.Design.cast(app.activeProduct);capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_current_body_center_0');assert c.bRepBodies.count==1 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features)
 library=app.materialLibraries.itemById('C1EEA57C-3F56-45FC-B8CB-A9EC46A9994C');name='PETG mass estimate (1270 kg/m3)';material=d.materials.itemByName(name) or d.materials.addByCopy(library.materials.itemByName('PET Plastic'),name)
 for key in ['structural_Density','thermal_Density']:
  p=core.FloatProperty.cast(material.materialProperties.itemById(key))
  if p:p.value=1270
 appearance=d.appearances.itemByName('Tinfox ivory')
 if not appearance:
  template=app.materialLibraries.itemById('BA5EE55E-9982-449B-9D66-9F036540E140').appearances.itemByName('Plastic - Matte (White)');appearance=d.appearances.addByCopy(template,'Tinfox ivory')
  for key in ['opaque_albedo','surface_albedo']:
   p=core.ColorProperty.cast(appearance.appearanceProperties.itemById(key))
   if p:p.value=core.Color.create(231,223,208,255)
 body=c.bRepBodies.item(0);body.material=material;body.appearance=appearance
 for sk in c.sketches:sk.isLightBulbOn=False
 for pl in c.constructionPlanes:pl.isLightBulbOn=False
 for axis in c.constructionAxes:axis.isLightBulbOn=False
 for occ in d.rootComponent.occurrences:
  if occ.component.partNumber=='body_center_0':occ.isLightBulbOn=False
  elif occ.component==c:occ.isLightBulbOn=True
 c.attributes.add('Tinfox','SourceModelSHA256','929c06ab624ed80192157e99ce43165c1416db414902cb0a36c19d6d2ad50da6');c.attributes.add('Tinfox','GeometryStatus','Full surfaces, nine sections, four silhouettes and three family edit/restores checked. Whole assembly/service gate pending.');c.attributes.add('Tinfox','MassMetrology','Use converged exported BRep integration: native physical-property quadrature is inaccurate for this roof.');c.attributes.add('Tinfox','ManufacturingRelease','False');previous=doc.dataFile.versionNumber;assert doc.save('Compact native rounded cover candidate with four-section guided roof. Shape, silhouette and family edits checked; complete assembly and fabrication gate remain open. Prior cover retained hidden for reversible comparison.');path=os.path.join(tempfile.gettempdir(),'tinfox-native','Tinfox-Chassis-current-cover-checkpoint.f3d');assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path));print(json.dumps({'save_requested':True,'previous_version':previous,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'path':path,'features':c.features.count,'sketches':c.sketches.count,'capacity':capacity,'source_of_truth_changed':False}))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'current-cover-checkpoint',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-cover-checkpoint.json').write_text(json.dumps(record,indent=2));print(record);fetch(record['path'],Path(record['path']).name)
