"""Save the current native Head and remove the retired bridge from active work."""
import json,hashlib
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
for label in ['current-sensor-hood-native','current-sensor-cradle-native']:
 sha=hashlib.sha256((ROOT/'exports'/f'{label}.step').read_bytes()).hexdigest()
 for suffix,gate in [('geometry','geometric_gate_passed'),('sections','section_gate_passed')]:
  data=json.loads((ROOT/'audits'/f'{label}-{suffix}.json').read_text());assert data[gate] and data['native_step_sha256']==sha,(label,suffix)
assert json.loads((ROOT/'audits/current-sensor-hood-silhouettes.json').read_text())['passed']
assert json.loads((ROOT/'audits/current-head-family-qualification.json').read_text())['passed']
assert (ROOT/'exports/Tinfox-Head-native-checkpoint.f3d').exists()
s=script_header()+'''
import adsk.core as core,adsk.fusion as fusion

def run(_context: str):
 import json,time,os,tempfile
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);before=[{'name':c.name,'part':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count} for c in d.allComponents];candidates={c.partNumber:c for c in d.allComponents if c.partNumber.startswith('CANDIDATE_current_')};assert len(candidates)==3
 # The saved V0 cloud version and local F3D preserve the old bridge. Neither the
 # native face nor the current cradle/hood depends on this retired component.
 retired=[o for o in list(root.occurrences) if o.component.partNumber=='body_nose_surround'];assert len(retired)==1;removed={'name':retired[0].component.name,'part':retired[0].component.partNumber,'features':retired[0].component.features.count};assert retired[0].deleteMe();assert d.computeAll()
 for c in candidates.values():assert c.bRepBodies.count==1 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),c.name
 for c in d.allComponents:
  if c.partNumber in ['front_fascia','sensor_bezel']:
   c.name=('Compound front face' if c.partNumber=='front_fascia' else 'Camera bezel')+' - native design master';c.partNumber='DESIGN_MASTER_'+c.partNumber;c.attributes.add('Tinfox','GeometryRole','Native construction dependency; not a separate physical part')
 master=candidates['CANDIDATE_current_front_face_master'];master.name='Integrated front face - native design master';master.partNumber='DESIGN_MASTER_integrated_front_face';master.attributes.add('Tinfox','GeometryRole','Native construction dependency; not a separate physical part')
 # Preserve each design master's sketch/feature history, but consume its final
 # construction solid after the dependent copies so it cannot add robot mass.
 for c in list(d.allComponents):
  if c.partNumber.startswith('DESIGN_MASTER_'):
   for b in list(c.bRepBodies):c.features.removeFeatures.add(b).name='Consume construction stock after dependent native copies'
 library=app.materialLibraries.itemById('C1EEA57C-3F56-45FC-B8CB-A9EC46A9994C');mname='PETG mass estimate (1270 kg/m3)';material=d.materials.itemByName(mname) or d.materials.addByCopy(library.materials.itemByName('PET Plastic'),mname)
 for key in ['structural_Density','thermal_Density']:
  prop=core.FloatProperty.cast(material.materialProperties.itemById(key))
  if prop:prop.value=1270
 appearance=d.appearances.itemByName('Tinfox ivory')
 if not appearance:
  template=app.materialLibraries.itemById('BA5EE55E-9982-449B-9D66-9F036540E140').appearances.itemByName('Plastic - Matte (White)');appearance=d.appearances.addByCopy(template,'Tinfox ivory')
  for key in ['opaque_albedo','surface_albedo']:
   prop=core.ColorProperty.cast(appearance.appearanceProperties.itemById(key))
   if prop:prop.value=core.Color.create(231,223,208,255)
 for key,name in [('front_fascia','Low sensor hood and compound front face'),('body_nose_surround','Rail-mounted sensor cradle')]:
  c=candidates['CANDIDATE_current_'+key];c.name=name;c.partNumber=key;c.bRepBodies.item(0).material=material;c.bRepBodies.item(0).appearance=appearance;c.attributes.add('Tinfox','SourceModelSHA256','929c06ab624ed80192157e99ce43165c1416db414902cb0a36c19d6d2ad50da6');c.attributes.add('Tinfox','GeometryStatus','Restored surfaces, nine sections and actual family edits checked. Hood silhouettes checked. Complete assembly/service gate pending.');c.attributes.add('Tinfox','ManufacturingRelease','False')
 for c in d.allComponents:
  for sk in c.sketches:sk.isLightBulbOn=False
  for pl in c.constructionPlanes:pl.isLightBulbOn=False
  for ax in c.constructionAxes:ax.isLightBulbOn=False
 for occ in root.occurrences:occ.isLightBulbOn=occ.component.partNumber in ['front_fascia','body_nose_surround']
 assert d.computeAll();issues=[(c.name,f.name,f.errorOrWarningMessage) for c in d.allComponents for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues
 physical=[c for c in d.allComponents if c.partNumber in ['front_fascia','body_nose_surround']]
 def bounds(c):return [min(getattr(v.geometry,a) for v in c.bRepBodies.item(0).vertices)*10 for a in ['x','y','z']]+[max(getattr(v.geometry,a) for v in c.bRepBodies.item(0).vertices)*10 for a in ['x','y','z']]
 original={c.partNumber:bounds(c) for c in physical};p=d.userParameters.itemByName('body_hip_x');old=p.expression;p.expression='190 mm';assert d.computeAll()
 for c in physical:assert max(abs((b-a)-(5 if i in [0,3] else 0)) for i,(a,b) in enumerate(zip(original[c.partNumber],bounds(c))))<.005,c.name
 p.expression=old;assert d.computeAll()
 for c in physical:assert max(abs(a-b) for a,b in zip(original[c.partNumber],bounds(c)))<.005,c.name
 assert sum(c.bRepBodies.count for c in d.allComponents)==2,'Only the two physical Head parts may retain final solids'
 after=[{'name':c.name,'part':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count} for c in d.allComponents];previous=doc.dataFile.versionNumber;assert doc.save('Current low sensor hood and two-foot cradle rebuilt as native parametric features. Shape, silhouette and family edit checks passed. Retired bridge removed; construction masters retained as dependencies. Whole robot qualification remains open.');path=os.path.join(tempfile.gettempdir(),'tinfox-native','Tinfox-Head-current-sensor-checkpoint.f3d');assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path));print(json.dumps({'save_requested':True,'previous_version':previous,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'path':path,'capacity':capacity,'before':before,'after':after,'retired_removed':removed,'source_of_truth_changed':False}))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'current-head-checkpoint',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-head-checkpoint.json').write_text(json.dumps(record,indent=2));print(record);fetch(record['path'],Path(record['path']).name)
